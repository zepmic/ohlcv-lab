"""Logging setup with a unified format and level from an environment variable."""

import logging
import os

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"
LOG_LEVEL_ENV_VAR = "OHLCV_LAB_LOG_LEVEL"
DEFAULT_LOG_LEVEL = "INFO"


def configure_logging() -> None:
    """Configure the root logger with a unified format and a level read from the environment."""
    level_name = os.environ.get(LOG_LEVEL_ENV_VAR, DEFAULT_LOG_LEVEL).upper()
    level = logging.getLevelName(level_name)
    if not isinstance(level, int):
        level = logging.getLevelName(DEFAULT_LOG_LEVEL)

    logging.basicConfig(format=LOG_FORMAT, level=level, force=True)
