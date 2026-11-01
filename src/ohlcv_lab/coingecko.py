"""Client for the CoinGecko public simple price endpoint."""

import requests

from ohlcv_lab.http_client import get

PRICE_URL = "https://api.coingecko.com/api/v3/simple/price"

COIN_IDS = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "USDT": "tether",
    "USDC": "usd-coin",
    "BNB": "binancecoin",
    "SOL": "solana",
    "XRP": "ripple",
}


def fetch_price(symbol: str, session: requests.Session | None = None) -> float:
    """Fetch the current price for a "BASE/QUOTE" symbol."""
    base, _, quote = symbol.partition("/")
    coin_id = _to_coin_id(base)
    vs_currency = quote.lower() if quote else "usd"
    params = {"ids": coin_id, "vs_currencies": vs_currency}
    response = get(PRICE_URL, session=session, params=params)
    data = response.json()
    try:
        return float(data[coin_id][vs_currency])
    except KeyError:
        raise ValueError(f"no price data for {symbol!r}") from None


def _to_coin_id(base: str) -> str:
    """Translate a base currency like "BTC" to its CoinGecko coin id."""
    try:
        return COIN_IDS[base.upper()]
    except KeyError:
        raise ValueError(f"unsupported symbol for CoinGecko: {base!r}") from None
