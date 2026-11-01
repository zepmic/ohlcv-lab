from unittest.mock import MagicMock

import pytest
import requests

from ohlcv_lab.coingecko import PRICE_URL, fetch_price


def _session_returning(data):
    session = MagicMock()
    response = MagicMock()
    response.json.return_value = data
    session.get.return_value = response
    return session


def test_fetch_price_returns_parsed_price():
    session = _session_returning({"bitcoin": {"usd": 42000.5}})

    assert fetch_price("BTC/USD", session=session) == 42000.5


def test_fetch_price_defaults_to_usd_when_quote_is_missing():
    session = _session_returning({"ethereum": {"usd": 2500.0}})

    assert fetch_price("ETH", session=session) == 2500.0


def test_fetch_price_requests_expected_params():
    session = _session_returning({"bitcoin": {"eur": 1}})

    fetch_price("BTC/EUR", session=session)

    args, kwargs = session.get.call_args
    assert args[0] == PRICE_URL
    assert kwargs["params"] == {"ids": "bitcoin", "vs_currencies": "eur"}


def test_fetch_price_rejects_unsupported_symbol():
    session = _session_returning({})

    with pytest.raises(ValueError):
        fetch_price("DOGE/USD", session=session)


def test_fetch_price_raises_when_response_has_no_price_data():
    session = _session_returning({})

    with pytest.raises(ValueError):
        fetch_price("BTC/USD", session=session)


def test_fetch_price_raises_on_http_error():
    session = MagicMock()
    response = MagicMock()
    response.raise_for_status.side_effect = requests.HTTPError("boom")
    session.get.return_value = response

    with pytest.raises(requests.HTTPError):
        fetch_price("BTC/USD", session=session)
