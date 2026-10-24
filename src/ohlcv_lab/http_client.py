"""HTTP client wrapper with a default timeout, retries and backoff."""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

DEFAULT_TIMEOUT = 10
DEFAULT_RETRIES = 3
DEFAULT_BACKOFF_FACTOR = 0.5
RETRY_STATUS_CODES = (429, 500, 502, 503, 504)


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
    )
    adapter = HTTPAdapter(max_retries=retry)
    session = requests.Session()
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def get(
    url: str,
    session: requests.Session | None = None,
    timeout: float = DEFAULT_TIMEOUT,
    **kwargs,
) -> requests.Response:
    """Send a GET request with a default timeout and raise for HTTP error status.

    Uses a one-off retrying session if none is given.
    """
    session = session or build_session()
    response = session.get(url, timeout=timeout, **kwargs)
    response.raise_for_status()
    return response
