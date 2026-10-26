"""Client for the Binance public klines endpoint."""

import requests

from ohlcv_lab.http_client import get
from ohlcv_lab.models import Candle

KLINES_URL = "https://api.binance.com/api/v3/klines"


def fetch_klines(
    symbol: str,
    interval: str,
    limit: int = 500,
    session: requests.Session | None = None,
) -> list[Candle]:
    """Fetch klines for a symbol and interval and parse them into candles."""
    params = {
        "symbol": _to_binance_symbol(symbol),
        "interval": interval,
        "limit": limit,
    }
    response = get(KLINES_URL, session=session, params=params)
    return [_parse_kline(kline) for kline in response.json()]


def _to_binance_symbol(symbol: str) -> str:
    """Convert a "BASE/QUOTE" symbol to the slash-free format Binance expects."""
    return symbol.replace("/", "").upper()


def _parse_kline(kline: list) -> Candle:
    """Parse a single Binance kline entry into a Candle."""
    return Candle(
        timestamp=int(kline[0]),
        open=float(kline[1]),
        high=float(kline[2]),
        low=float(kline[3]),
        close=float(kline[4]),
        volume=float(kline[5]),
    )
