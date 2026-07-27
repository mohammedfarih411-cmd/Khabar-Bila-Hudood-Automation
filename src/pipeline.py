from __future__ import annotations

from dataclasses import dataclass, field
import logging

from .ai.truthguard import ArticleVerifier, EditorialPackage
from .database.store import NewsStore
from .models import Article
from .news.collector import collect_rss
from .news.ranking import rank_articles


@dataclass(slots=True)
class PipelineResult:
    collected: int
    eligible: int
    selected: list[Article]
    editorial: dict[str, EditorialPackage] = field(default_factory=dict)


def run_pipeline(
    config: dict,
    logger: logging.Logger,
    verifier: ArticleVerifier | None = None,
) -> PipelineResult:
    news_config = config["news"]
    articles = collect_rss(
        config["sources"]["rss"],
        max_articles=int(news_config.get("max_articles", 30)),
    )
    store = NewsStore(config["database"]["path"])

    unique = [article for article in articles if not store.contains(article)]
    ranked = rank_articles(unique)
    publish_count = max(0, int(news_config.get("publish_per_run", 1)))
    selected: list[Article] = []
    editorial: dict[str, EditorialPackage] = {}

    for article in ranked:
        if len(selected) >= publish_count:
            break
        if verifier is None:
            selected.append(article)
            continue

        try:
            package = verifier.verify(article)
        except Exception:
            logger.exception("TruthGuard failed | source=%s | title=%s", article.source, article.title)
            store.save(article, status="verification_error")
            continue

        editorial[article.fingerprint] = package
        if not package.approved:
            store.save(article, status="rejected")
            logger.warning(
                "TruthGuard rejected article | confidence=%.2f | reason=%s | title=%s",
                package.confidence,
                package.reason,
                article.title,
            )
            continue
        selected.append(article)

    for article in selected:
        store.save(article, status="verified" if verifier else "selected")
        package = editorial.get(article.fingerprint)
        logger.info(
            "Selected article | category=%s | score=%.2f | confidence=%s | source=%s | title=%s",
            article.category,
            article.score,
            f"{package.confidence:.2f}" if package else "n/a",
            article.source,
            package.title_ar if package else article.title,
        )

    logger.info(
        "Pipeline complete | collected=%d | unique=%d | eligible=%d | selected=%d",
        len(articles),
        len(unique),
        len(ranked),
        len(selected),
    )
    return PipelineResult(len(articles), len(ranked), selected, editorial)
