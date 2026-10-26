"""Configuration for symbols, interval and data path."""

from dataclasses import dataclass

DEFAULT_SYMBOLS: tuple[str, ...] = ("BTC/USDT", "ETH/USDT")
DEFAULT_INTERVAL = "1h"
DEFAULT_DATA_PATH = "data"


@dataclass
class Config:
    """Runtime settings for fetching and storing OHLCV data."""

    symbols: tuple[str, ...] = DEFAULT_SYMBOLS
    interval: str = DEFAULT_INTERVAL
    data_path: str = DEFAULT_DATA_PATH
