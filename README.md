# ohlcv-lab

A small Python toolkit for crypto OHLCV data. The plan is to pull candles from public exchange APIs, store them locally, compute indicators on them, and browse the result in a dashboard.

It only deals with analysis and backtesting data. There is no trading code, and it never needs an API key with trading rights.

The project is at an early stage. So far there is the package skeleton, a config module, a logging setup, the `Candle` data model, and an HTTP client wrapper.

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

## Data model

`Candle` in `ohlcv_lab.models` represents a single OHLCV candle (timestamp, open, high, low, close, volume). It validates its values on creation and raises `ValueError` for negative or inconsistent data, for example when `high` is below `low` or a price is not positive.

## HTTP client

`ohlcv_lab.http_client` wraps `requests` for GET requests. `build_session()` returns a `requests.Session` that retries failed requests with exponential backoff on connection errors and on `429`/`5xx` responses. `get(url)` uses such a session with a default timeout of 10 seconds and raises for HTTP error status codes.

## Binance klines

`ohlcv_lab.binance` fetches candles from the public Binance klines endpoint. `fetch_klines(symbol, interval, limit=500)` returns up to `limit` candles and accepts optional `start_time`/`end_time` bounds in milliseconds since the epoch.

Binance caps a single response at 1000 candles, so a longer time range needs more than one request. `fetch_klines_range(symbol, interval, start_time, end_time)` covers this by paginating automatically, starting each new request right after the last candle of the previous one until `end_time` is reached.
