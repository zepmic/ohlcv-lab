"""HTTP client wrapper with a default timeout, retries and backoff."""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

DEFAULT_TIMEOUT = 10
DEFAULT_RETRIES = 3
DEFAULT_BACKOFF_FACTOR = 0.5
# 418 is used by some exchanges (e.g. Binance) to signal a temporary IP ban
# after repeated rate limit violations, alongside a Retry-After header.
RETRY_STATUS_CODES = (418, 429, 500, 502, 503, 504)


def build_session(
    retries: int = DEFAULT_RETRIES,
    backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
) -> requests.Session:
    """Build a requests session that retries failed GET requests with backoff."""
    retry = Retry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=RETRY_STATUS_CODES,
        allowed_methods=("GET",),
        # Return the last response once retries run out, so get() raises HTTPError, not RetryError.
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session = requests.Session()
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


_session: requests.Session | None = None


def _default_session() -> requests.Session:
    """Create the shared session on first use so calls reuse connections."""
    global _session
    if _session is None:
        _session = build_session()
    return _session


def get(
    url: str,
    session: requests.Session | None = None,
    timeout: float = DEFAULT_TIMEOUT,
    **kwargs,
) -> requests.Response:
    """Send a GET request with a default timeout and raise for HTTP error status.

    Uses a shared retrying session if none is given.
    """
    session = session or _default_session()
    response = session.get(url, timeout=timeout, **kwargs)
    response.raise_for_status()
    return response
