"""SQLite storage for OHLCV candles."""

import sqlite3

from ohlcv_lab.models import Candle

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS candles (
    symbol TEXT NOT NULL,
    interval TEXT NOT NULL,
    timestamp INTEGER NOT NULL,
    open REAL NOT NULL,
    high REAL NOT NULL,
    low REAL NOT NULL,
    close REAL NOT NULL,
    volume REAL NOT NULL,
    PRIMARY KEY (symbol, interval, timestamp)
)
"""

UPSERT_SQL = """
INSERT INTO candles (symbol, interval, timestamp, open, high, low, close, volume)
VALUES (?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT (symbol, interval, timestamp) DO UPDATE SET
    open = excluded.open,
    high = excluded.high,
    low = excluded.low,
    close = excluded.close,
    volume = excluded.volume
"""


def connect(path: str) -> sqlite3.Connection:
    """Open a connection to the candle database, creating the schema if needed."""
    connection = sqlite3.connect(path)
    connection.execute(CREATE_TABLE_SQL)
    connection.commit()
    return connection


def upsert_candles(
    connection: sqlite3.Connection,
    symbol: str,
    interval: str,
    candles: list[Candle],
) -> None:
    """Insert candles for a symbol and interval, updating existing rows in place.

    A row is identified by (symbol, interval, timestamp), so fetching the same
    candle again just refreshes its values instead of creating a duplicate.
    """
    connection.executemany(
        UPSERT_SQL,
        [
            (
                symbol,
                interval,
                candle.timestamp,
                candle.open,
                candle.high,
                candle.low,
                candle.close,
                candle.volume,
            )
            for candle in candles
        ],
    )
    connection.commit()
