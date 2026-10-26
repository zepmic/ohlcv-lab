"""Client for the Binance public klines endpoint."""

import requests

from ohlcv_lab.http_client import get
from ohlcv_lab.models import Candle

KLINES_URL = "https://api.binance.com/api/v3/klines"
MAX_LIMIT = 1000

INTERVAL_MS = {
    "1m": 60_000,
    "3m": 3 * 60_000,
    "5m": 5 * 60_000,
    "15m": 15 * 60_000,
    "30m": 30 * 60_000,
    "1h": 60 * 60_000,
    "2h": 2 * 60 * 60_000,
    "4h": 4 * 60 * 60_000,
    "6h": 6 * 60 * 60_000,
    "8h": 8 * 60 * 60_000,
    "12h": 12 * 60 * 60_000,
    "1d": 24 * 60 * 60_000,
    "3d": 3 * 24 * 60 * 60_000,
    "1w": 7 * 24 * 60 * 60_000,
}


def fetch_klines(
    symbol: str,
    interval: str,
    limit: int = 500,
    session: requests.Session | None = None,
    start_time: int | None = None,
    end_time: int | None = None,
) -> list[Candle]:
    """Fetch klines for a symbol and interval and parse them into candles."""
    params = {
        "symbol": _to_binance_symbol(symbol),
        "interval": interval,
        "limit": limit,
    }
    if start_time is not None:
        params["startTime"] = start_time
    if end_time is not None:
        params["endTime"] = end_time
    response = get(KLINES_URL, session=session, params=params)
    return [_parse_kline(kline) for kline in response.json()]


def fetch_klines_range(
    symbol: str,
    interval: str,
    start_time: int,
    end_time: int,
    session: requests.Session | None = None,
) -> list[Candle]:
    """Fetch all klines between start_time and end_time, paginating as needed.

    Binance caps a single response at MAX_LIMIT candles, so a long time range
    is split into successive requests, each starting right after the last
    candle of the previous one.
    """
    step_ms = _interval_to_ms(interval)
    candles: list[Candle] = []
    current_start = start_time
    while current_start <= end_time:
        batch = fetch_klines(
            symbol,
            interval,
            limit=MAX_LIMIT,
            session=session,
            start_time=current_start,
            end_time=end_time,
        )
        if not batch:
            break
        candles.extend(batch)
        current_start = batch[-1].timestamp + step_ms
        if len(batch) < MAX_LIMIT:
            break
    return candles


def _interval_to_ms(interval: str) -> int:
    """Convert a Binance interval string to its duration in milliseconds."""
    try:
        return INTERVAL_MS[interval]
    except KeyError:
        raise ValueError(f"unsupported interval for pagination: {interval!r}") from None


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
