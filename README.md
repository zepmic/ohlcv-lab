# ohlcv-lab

A small Python toolkit for crypto OHLCV data. The plan is to pull candles from public exchange APIs, store them locally, compute indicators on them, and browse the result in a dashboard.

It only deals with analysis and backtesting data. There is no trading code, and it never needs an API key with trading rights.

The project is at an early stage. So far there is the package skeleton, a config module, and a logging setup.

## Setup

```bash
pip install -e ".[dev]"
```

## Tests

```bash
python -m pytest -q
```

## Layout

- `src/ohlcv_lab/` holds the package code (src layout)
- `tests/` holds the pytest tests

## Logging

Call `configure_logging()` from `ohlcv_lab.logging_setup` to set up a unified log format on the root logger. The log level defaults to `INFO` and can be overridden with the `OHLCV_LAB_LOG_LEVEL` environment variable (e.g. `DEBUG`, `WARNING`).
