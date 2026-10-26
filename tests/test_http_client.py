import http.server
import threading
from unittest.mock import MagicMock, patch

import pytest
import requests
from requests.adapters import HTTPAdapter

from ohlcv_lab.http_client import (
    DEFAULT_BACKOFF_FACTOR,
    DEFAULT_RETRIES,
    DEFAULT_TIMEOUT,
    RETRY_STATUS_CODES,
    build_session,
    get,
)


def test_build_session_configures_retry_and_backoff():
    session = build_session(retries=5, backoff_factor=1.5)

    adapter = session.get_adapter("https://example.com")
    assert isinstance(adapter, HTTPAdapter)
    retry = adapter.max_retries
    assert retry.total == 5
    assert retry.backoff_factor == 1.5
    assert set(retry.status_forcelist) == set(RETRY_STATUS_CODES)
    assert set(retry.allowed_methods) == {"GET"}
    assert retry.raise_on_status is False


def test_build_session_uses_defaults():
    session = build_session()

    retry = session.get_adapter("https://example.com").max_retries
    assert retry.total == DEFAULT_RETRIES
    assert retry.backoff_factor == DEFAULT_BACKOFF_FACTOR


def test_get_uses_default_timeout_and_returns_response():
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_session.get.return_value = mock_response

    result = get("https://example.com/data", session=mock_session)

    mock_session.get.assert_called_once_with("https://example.com/data", timeout=DEFAULT_TIMEOUT)
    mock_response.raise_for_status.assert_called_once()
    assert result is mock_response


def test_get_passes_custom_timeout_and_kwargs():
    mock_session = MagicMock()

    get("https://example.com", session=mock_session, timeout=2, params={"a": 1})

    mock_session.get.assert_called_once_with("https://example.com", timeout=2, params={"a": 1})


def test_get_raises_on_http_error():
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.HTTPError("boom")
    mock_session.get.return_value = mock_response

    with pytest.raises(requests.HTTPError):
        get("https://example.com", session=mock_session)


def test_get_builds_session_when_none_given():
    mock_response = MagicMock()
    mock_session = MagicMock()
    mock_session.get.return_value = mock_response

    with patch("ohlcv_lab.http_client.build_session", return_value=mock_session) as mock_build:
        result = get("https://example.com")

    mock_build.assert_called_once_with()
    mock_session.get.assert_called_once_with("https://example.com", timeout=DEFAULT_TIMEOUT)
    assert result is mock_response


def test_get_raises_http_error_after_retries_are_exhausted():
    class AlwaysUnavailable(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(503)
            self.end_headers()

        def log_message(self, *args):
            pass

    server = http.server.HTTPServer(("127.0.0.1", 0), AlwaysUnavailable)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        session = build_session(retries=1, backoff_factor=0)
        with pytest.raises(requests.HTTPError):
            get(f"http://127.0.0.1:{server.server_port}/", session=session)
    finally:
        server.shutdown()
        server.server_close()
