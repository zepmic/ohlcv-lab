# ohlcv-lab

A small Python toolkit for crypto OHLCV data. The plan is to pull candles from public exchange APIs, store them locally, compute indicators on them, and browse the result in a dashboard.

It only deals with analysis and backtesting data. There is no trading code, and it never needs an API key with trading rights.

The project is at an early stage. So far there is the package skeleton, a config module, a logging setup, the `Candle` data model, an HTTP client wrapper, and SQLite storage for candles.

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

`Candle` in `ohlcv_lab.models` represents a single OHLCV candle (timestamp, open, high, low, close, volume). It validates its values on creation and raises `InvalidCandleError` for negative or inconsistent data, for example when `high` is below `low` or a price is not positive.

## HTTP client

`ohlcv_lab.http_client` wraps `requests` for GET requests. `build_session()` returns a `requests.Session` that retries failed requests with exponential backoff on connection errors and on `418`/`429`/`5xx` responses, and honors a `Retry-After` header when the server sends one. `get(url)` uses such a session with a default timeout of 10 seconds and raises for HTTP error status codes.

## Binance klines

`ohlcv_lab.binance` fetches candles from the public Binance klines endpoint. `fetch_klines(symbol, interval, limit=500)` returns up to `limit` candles and accepts optional `start_time`/`end_time` bounds in milliseconds since the epoch.

Binance caps a single response at 1000 candles, so a longer time range needs more than one request. `fetch_klines_range(symbol, interval, start_time, end_time)` covers this by paginating automatically, starting each new request right after the last candle of the previous one until `end_time` is reached.

`fetch_price(symbol)` fetches the current price for a symbol from the Binance ticker endpoint.

## Price providers

`ohlcv_lab.providers.PriceProvider` describes the shared interface for fetching the current price of a symbol. `ohlcv_lab.binance.fetch_price` and `ohlcv_lab.coingecko.fetch_price` both implement it, so either can be used as the price source for a given symbol.

`ohlcv_lab.coingecko` fetches prices from the public CoinGecko simple price endpoint. `fetch_price(symbol)` accepts a "BASE/QUOTE" symbol such as `"BTC/USD"`, defaults the quote currency to USD when omitted, and translates the base currency to the CoinGecko coin id it expects.

## Storage

`ohlcv_lab.storage` stores candles in a SQLite database. `connect(path)` opens a connection to the database file and brings its schema up to date. `upsert_candles(connection, symbol, interval, candles)` inserts a list of candles, identifying each row by `(symbol, interval, timestamp)`. Fetching the same candle again updates the existing row in place instead of creating a duplicate. `fetch_candles(connection, symbol, interval, start_time=0, end_time=...)` returns the stored candles for a symbol and interval, ordered by timestamp, optionally narrowed to a timestamp range in milliseconds since the epoch.

`find_gaps(connection, symbol, interval, interval_ms, start_time=0, end_time=...)` compares consecutive stored candles against the expected spacing `interval_ms` and returns a list of `(gap_start, gap_end)` timestamp pairs, each marking a run of one or more missing candles between two stored ones.

Schema changes are tracked as a list of migrations in `MIGRATIONS`, each one the SQL for a single schema version. `connect(path)` applies any migrations after the version recorded in a `schema_version` table, so an existing database is brought up to date instead of rebuilt. `migrate(connection)` does this directly on an open connection and is a no-op if the schema is already current.

## Incremental sync

`ohlcv_lab.sync.sync_missing_candles(connection, symbol, interval, interval_ms, start_time, end_time, fetch_range)` reloads only the candles missing from storage for a time range, instead of re-fetching everything. It works out what's missing, a leading range before the first stored candle, the gaps `find_gaps` reports, and a trailing range after the last stored candle, then calls `fetch_range` once per missing range, for example `ohlcv_lab.binance.fetch_klines_range`. The fetched candles are stored and also returned; candles already in storage are left untouched.

## Export

`ohlcv_lab.export` writes a list of candles to a file. `export_candles_to_csv(candles, path)` writes them to a CSV file with a header row (`timestamp, open, high, low, close, volume`). `export_candles_to_parquet(candles, path)` writes them to a Parquet file with the same columns.

## Indicators

`ohlcv_lab.indicators` computes indicators from a list of candles. `sma(candles, period)` and `ema(candles, period)` each return a list of the same length as `candles`, one value per candle in the same order. The first `period - 1` entries are `None` because there are not yet enough candles to average. `ema` seeds its first value with the simple moving average of the first `period` closes and then smooths each later close with the standard factor `2 / (period + 1)`.

`rsi(candles, period)` computes the relative strength index of closing prices using Wilder's smoothing method. It returns a list of the same length as `candles`; the first `period` entries are `None` because at least `period` price changes are needed to seed the average gain and loss, after which each value is smoothed with the next price change.

## Exceptions

`ohlcv_lab.exceptions` defines the custom exception types raised across the package. `OhlcvLabError` is the common base class. `InvalidCandleError` is raised by `Candle` for invalid data, `UnsupportedSymbolError` and `UnsupportedIntervalError` are raised by the Binance and CoinGecko clients for symbols or intervals they do not recognize, and `NoPriceDataError` is raised when a provider's response does not contain the requested price. Each of these also subclasses `ValueError`, so existing code that catches `ValueError` keeps working.
