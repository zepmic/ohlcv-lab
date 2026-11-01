import inspect

from ohlcv_lab import binance, coingecko
from ohlcv_lab.providers import PriceProvider


def test_binance_and_coingecko_price_fetchers_share_the_same_signature():
    expected = inspect.signature(PriceProvider.__call__).parameters
    # Drop "self", it has no counterpart in the plain fetch_price functions.
    expected = list(expected.values())[1:]

    for fetch_price in (binance.fetch_price, coingecko.fetch_price):
        assert list(inspect.signature(fetch_price).parameters.values()) == expected
