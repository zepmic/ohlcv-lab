import pytest

from ohlcv_lab.exceptions import (
    InvalidCandleError,
    NoPriceDataError,
    OhlcvLabError,
    UnsupportedIntervalError,
    UnsupportedSymbolError,
)


@pytest.mark.parametrize(
    "exception_type",
    [InvalidCandleError, UnsupportedSymbolError, UnsupportedIntervalError, NoPriceDataError],
)
def test_custom_exceptions_are_ohlcv_lab_errors(exception_type):
    assert issubclass(exception_type, OhlcvLabError)


@pytest.mark.parametrize(
    "exception_type",
    [InvalidCandleError, UnsupportedSymbolError, UnsupportedIntervalError, NoPriceDataError],
)
def test_custom_exceptions_are_value_errors(exception_type):
    assert issubclass(exception_type, ValueError)


def test_ohlcv_lab_error_is_not_a_value_error():
    assert not issubclass(OhlcvLabError, ValueError)
