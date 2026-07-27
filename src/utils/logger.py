from __future__ import annotations

import logging
from pathlib import Path


def setup_logger(config: dict | None = None) -> logging.Logger:
    settings = config or {}
    level_name = str(settings.get("level", "INFO")).upper()
    level = getattr(logging, level_name, logging.INFO)
    log_path = Path(settings.get("file", "logs/app.log"))
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("KhabarBilaHudood")
    logger.setLevel(level)
    if logger.handlers:
        return logger

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger
