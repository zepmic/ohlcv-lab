import logging

from ohlcv_lab.logging_setup import DEFAULT_LOG_LEVEL, LOG_FORMAT, LOG_LEVEL_ENV_VAR, configure_logging


def test_configure_logging_uses_default_level(monkeypatch):
    monkeypatch.delenv(LOG_LEVEL_ENV_VAR, raising=False)

    configure_logging()

    root = logging.getLogger()
    assert root.level == logging.getLevelName(DEFAULT_LOG_LEVEL)
    assert root.handlers
    assert root.handlers[0].formatter._fmt == LOG_FORMAT


def test_configure_logging_reads_level_from_env(monkeypatch):
    monkeypatch.setenv(LOG_LEVEL_ENV_VAR, "DEBUG")

    configure_logging()

    assert logging.getLogger().level == logging.DEBUG


def test_configure_logging_falls_back_on_invalid_level(monkeypatch):
    monkeypatch.setenv(LOG_LEVEL_ENV_VAR, "NOT_A_LEVEL")

    configure_logging()

    assert logging.getLogger().level == logging.getLevelName(DEFAULT_LOG_LEVEL)
