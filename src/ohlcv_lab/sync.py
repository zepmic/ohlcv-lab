"""Incremental reload of only the candles missing from local storage."""

import sqlite3
from typing import Callable

from ohlcv_lab.models import Candle
from ohlcv_lab.storage import fetch_candles, find_gaps, upsert_candles

RangeFetcher = Callable[..., list[Candle]]


def sync_missing_candles(
    connection: sqlite3.Connection,
    symbol: str,
    interval: str,
    interval_ms: int,
    start_time: int,
    end_time: int,
    fetch_range: RangeFetcher,
) -> list[Candle]:
    """Fetch and store only the candles missing from storage in a time range.

    Compares what's already stored for `symbol`/`interval` against
    `[start_time, end_time]` to find what's missing: a leading range before
    the first stored candle, the gaps `find_gaps` reports between stored
    candles, and a trailing range after the last stored candle. `fetch_range`
    is called once per missing range as
    `fetch_range(symbol, interval, start_time=gap_start, end_time=gap_end)`,
    e.g. `ohlcv_lab.binance.fetch_klines_range`. Candles already in storage
    are left untouched and not re-fetched. Returns the newly fetched candles.
    """
    missing_ranges = _missing_ranges(
        connection, symbol, interval, interval_ms, start_time, end_time
    )
    fetched: list[Candle] = []
    for gap_start, gap_end in missing_ranges:
        fetched.extend(
            fetch_range(symbol, interval, start_time=gap_start, end_time=gap_end)
        )
    if fetched:
        upsert_candles(connection, symbol, interval, fetched)
    return fetched


def _missing_ranges(
    connection: sqlite3.Connection,
    symbol: str,
    interval: str,
    interval_ms: int,
    start_time: int,
    end_time: int,
) -> list[tuple[int, int]]:
    """Return the (start, end) timestamp ranges not yet covered by storage."""
    candles = fetch_candles(connection, symbol, interval, start_time, end_time)
    if not candles:
        return [(start_time, end_time)]

    ranges = []
    if candles[0].timestamp > start_time:
        ranges.append((start_time, candles[0].timestamp - interval_ms))
    ranges.extend(
        find_gaps(connection, symbol, interval, interval_ms, start_time, end_time)
    )
    if candles[-1].timestamp < end_time:
        ranges.append((candles[-1].timestamp + interval_ms, end_time))
    return ranges
