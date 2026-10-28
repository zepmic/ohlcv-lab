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


def test_get_builds_session_when_none_given(monkeypatch):
    monkeypatch.setattr("ohlcv_lab.http_client._session", None)
    mock_response = MagicMock()
    mock_session = MagicMock()
    mock_session.get.return_value = mock_response

    with patch("ohlcv_lab.http_client.build_session", return_value=mock_session) as mock_build:
        result = get("https://example.com")

    mock_build.assert_called_once_with()
    mock_session.get.assert_called_once_with("https://example.com", timeout=DEFAULT_TIMEOUT)
    assert result is mock_response


def test_get_reuses_default_session(monkeypatch):
    monkeypatch.setattr("ohlcv_lab.http_client._session", None)
    mock_session = MagicMock()

    with patch("ohlcv_lab.http_client.build_session", return_value=mock_session) as mock_build:
        get("https://example.com/a")
        get("https://example.com/b")

    mock_build.assert_called_once_with()
    assert mock_session.get.call_count == 2


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


def test_get_retries_on_rate_limit_ban_and_respects_retry_after():
    request_count = 0

    class BannedThenOk(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            nonlocal request_count
            request_count += 1
            if request_count == 1:
                self.send_response(418)
                self.send_header("Retry-After", "0")
                self.end_headers()
            else:
                self.send_response(200)
                self.end_headers()

        def log_message(self, *args):
            pass

    server = http.server.HTTPServer(("127.0.0.1", 0), BannedThenOk)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        session = build_session(retries=1, backoff_factor=0)
        response = get(f"http://127.0.0.1:{server.server_port}/", session=session)
        assert response.status_code == 200
        assert request_count == 2
    finally:
        server.shutdown()
        server.server_close()
