from unittest.mock import MagicMock

import pytest
import requests

from ohlcv_lab.binance import KLINES_URL, fetch_klines
from ohlcv_lab.models import Candle

SAMPLE_KLINE = [
    1699000000000,
    "100.00000000",
    "110.00000000",
    "95.00000000",
    "105.00000000",
    "12.50000000",
    1699003599999,
    "1312.50000000",
    10,
    "6.00000000",
    "630.00000000",
    "0",
]


def _session_returning(klines):
    session = MagicMock()
    response = MagicMock()
    response.json.return_value = klines
    session.get.return_value = response
    return session


def test_fetch_klines_parses_candles():
    session = _session_returning([SAMPLE_KLINE])

    candles = fetch_klines("BTC/USDT", "1h", session=session)

    assert candles == [
        Candle(timestamp=1699000000000, open=100.0, high=110.0, low=95.0, close=105.0, volume=12.5)
    ]


def test_fetch_klines_requests_expected_params():
    session = _session_returning([])

    fetch_klines("BTC/USDT", "1h", limit=10, session=session)

    session.get.assert_called_once()
    args, kwargs = session.get.call_args
    assert args[0] == KLINES_URL
    assert kwargs["params"] == {"symbol": "BTCUSDT", "interval": "1h", "limit": 10}


def test_fetch_klines_returns_empty_list_for_no_data():
    session = _session_returning([])

    assert fetch_klines("ETH/USDT", "1h", session=session) == []


def test_fetch_klines_raises_on_http_error():
    session = MagicMock()
    response = MagicMock()
    response.raise_for_status.side_effect = requests.HTTPError("boom")
    session.get.return_value = response

    with pytest.raises(requests.HTTPError):
        fetch_klines("BTC/USDT", "1h", session=session)
