"""Shared interface for price providers."""

from typing import Protocol

import requests


class PriceProvider(Protocol):
    """A callable that fetches the current price for a symbol.

    `ohlcv_lab.binance.fetch_price` and `ohlcv_lab.coingecko.fetch_price`
    both match this signature, so they can be used interchangeably.
    """

    def __call__(self, symbol: str, session: requests.Session | None = None) -> float: ...
