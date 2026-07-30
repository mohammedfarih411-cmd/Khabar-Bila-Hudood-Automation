from __future__ import annotations

from .ai.truthguard import build_truthguard
from .config import load_config
from .pipeline import run_pipeline
from .production import produce_and_publish
from .utils.logger import setup_logger


def main() -> None:
    config = load_config()
    logger = setup_logger(config.get("logging", {}))

    logger.info("=" * 60)
    logger.info("Khabar Bila Hudood Automation Started")
    logger.info("=" * 60)
    logger.info("Language: %s", config["project"]["language"])
    logger.info("Model: %s", config["ai"]["model"])

    verifier = build_truthguard(config) if config.get("ai", {}).get("enabled", True) else None
    result = run_pipeline(config, logger, verifier=verifier)
    if not result.selected:
        logger.warning("No verified new article was selected in this run.")
        return

    ready_articles = []
    for article in result.selected:
        package = result.editorial.get(article.fingerprint)
        if not package:
            continue
        logger.info(
            "Editorial package ready | title=%s | tags=%d | hashtags=%d",
            package.title_ar,
            len(package.tags),
            len(package.hashtags),
        )
        ready_articles.append(article)

    if not ready_articles:
        logger.warning("No editorial package was ready for production.")
        return

    production_enabled = bool(config.get("production", {}).get("enabled", False))
    if not production_enabled:
        logger.info("Production is disabled; no media or upload was attempted.")
        return

    try:
        produce_and_publish(ready_articles, result.editorial, config, logger)
    except Exception:
        logger.exception(
            "Media production failed | article_count=%d", len(ready_articles)
        )
        raise


if __name__ == "__main__":
    main()
