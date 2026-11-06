"""Custom exception types raised across the package.

Each type also subclasses the built-in exception that call sites would
otherwise expect (e.g. ValueError), so existing `except ValueError` handlers
keep working while callers can catch a more specific type if they want to.
"""


class OhlcvLabError(Exception):
    """Base class for all errors raised by this package."""


class InvalidCandleError(OhlcvLabError, ValueError):
    """Raised when a Candle is constructed with invalid or inconsistent values."""


class UnsupportedSymbolError(OhlcvLabError, ValueError):
    """Raised when a provider does not recognize a requested symbol."""


class UnsupportedIntervalError(OhlcvLabError, ValueError):
    """Raised when an interval is not supported for the requested operation."""


class NoPriceDataError(OhlcvLabError, ValueError):
    """Raised when a provider's response does not contain price data for a symbol."""
