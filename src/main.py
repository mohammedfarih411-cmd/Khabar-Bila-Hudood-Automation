from __future__ import annotations

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

    result = run_pipeline(config, logger)
    if not result.selected:
        logger.warning("No eligible new article was selected in this run.")


if __name__ == "__main__":
    main()
