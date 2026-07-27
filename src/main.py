from __future__ import annotations

from .ai.truthguard import build_truthguard
from .config import load_config
from .pipeline import run_pipeline
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

    for article in result.selected:
        package = result.editorial.get(article.fingerprint)
        if package:
            logger.info(
                "Editorial package ready | title=%s | tags=%d | hashtags=%d",
                package.title_ar,
                len(package.tags),
                len(package.hashtags),
            )


if __name__ == "__main__":
    main()
