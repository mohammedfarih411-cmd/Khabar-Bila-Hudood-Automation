from __future__ import annotations

from dataclasses import dataclass
import logging

from .database.store import NewsStore
from .models import Article
from .news.collector import collect_rss
from .news.ranking import rank_articles


@dataclass(slots=True)
class PipelineResult:
    collected: int
    eligible: int
    selected: list[Article]


def run_pipeline(config: dict, logger: logging.Logger) -> PipelineResult:
    news_config = config["news"]
    articles = collect_rss(
        config["sources"]["rss"],
        max_articles=int(news_config.get("max_articles", 30)),
    )
    store = NewsStore(config["database"]["path"])

    unique = [article for article in articles if not store.contains(article)]
    ranked = rank_articles(unique)
    publish_count = max(0, int(news_config.get("publish_per_run", 1)))
    selected = ranked[:publish_count]

    for article in selected:
        store.save(article, status="selected")
        logger.info(
            "Selected article | category=%s | score=%.2f | source=%s | title=%s",
            article.category,
            article.score,
            article.source,
            article.title,
        )

    logger.info(
        "Pipeline complete | collected=%d | unique=%d | selected=%d",
        len(articles),
        len(unique),
        len(selected),
    )
    return PipelineResult(len(articles), len(ranked), selected)
