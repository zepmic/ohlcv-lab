from unittest.mock import MagicMock

import pytest
import requests

from ohlcv_lab.binance import KLINES_URL, MAX_LIMIT, fetch_klines, fetch_klines_range
from ohlcv_lab.models import Candle

ONE_HOUR_MS = 60 * 60 * 1000

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


def _kline_at(timestamp):
    return [timestamp, "100", "110", "95", "105", "12.5"] + SAMPLE_KLINE[6:]


def _session_returning(klines):
    session = MagicMock()
    response = MagicMock()
    response.json.return_value = klines
    session.get.return_value = response
    return session


def _session_returning_pages(pages):
    session = MagicMock()
    responses = []
    for page in pages:
        response = MagicMock()
        response.json.return_value = page
        responses.append(response)
    session.get.side_effect = responses
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


def test_fetch_klines_includes_start_and_end_time_when_given():
    session = _session_returning([])

    fetch_klines("BTC/USDT", "1h", session=session, start_time=1, end_time=2)

    args, kwargs = session.get.call_args
    assert kwargs["params"]["startTime"] == 1
    assert kwargs["params"]["endTime"] == 2


def test_fetch_klines_range_paginates_across_full_pages():
    start = 1699000000000
    page1 = [_kline_at(start + i * ONE_HOUR_MS) for i in range(MAX_LIMIT)]
    last_of_page1 = page1[-1][0]
    page2 = [_kline_at(last_of_page1 + ONE_HOUR_MS)]
    session = _session_returning_pages([page1, page2])

    candles = fetch_klines_range(
        "BTC/USDT", "1h", start, last_of_page1 + ONE_HOUR_MS, session=session
    )

    assert len(candles) == MAX_LIMIT + 1
    assert session.get.call_count == 2
    first_params = session.get.call_args_list[0].kwargs["params"]
    second_params = session.get.call_args_list[1].kwargs["params"]
    assert first_params["startTime"] == start
    assert second_params["startTime"] == last_of_page1 + ONE_HOUR_MS


def test_fetch_klines_range_stops_on_short_page():
    start = 1699000000000
    end = start + 100 * ONE_HOUR_MS
    page = [_kline_at(start + i * ONE_HOUR_MS) for i in range(3)]
    session = _session_returning_pages([page])

    candles = fetch_klines_range("BTC/USDT", "1h", start, end, session=session)

    assert len(candles) == 3
    session.get.assert_called_once()


def test_fetch_klines_range_returns_empty_list_for_no_data():
    session = _session_returning_pages([[]])

    candles = fetch_klines_range(
        "BTC/USDT", "1h", 1699000000000, 1699000000000 + ONE_HOUR_MS, session=session
    )

    assert candles == []


def test_fetch_klines_range_rejects_unsupported_interval():
    with pytest.raises(ValueError):
        fetch_klines_range("BTC/USDT", "1M", 0, 1)
