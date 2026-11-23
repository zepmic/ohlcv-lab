import pytest

from ohlcv_lab.indicators import ema, rsi, sma
from ohlcv_lab.models import Candle


def _candles(closes: list[float]) -> list[Candle]:
    return [
        Candle(timestamp=i, open=close, high=close, low=close, close=close, volume=1.0)
        for i, close in enumerate(closes)
    ]


def test_sma_leaves_leading_entries_as_none():
    candles = _candles([1.0, 2.0, 3.0, 4.0, 5.0])

    result = sma(candles, period=3)

    assert result == [None, None, 2.0, 3.0, 4.0]


def test_sma_with_period_one_equals_close_prices():
    candles = _candles([1.0, 2.0, 3.0])

    result = sma(candles, period=1)

    assert result == [1.0, 2.0, 3.0]


def test_sma_with_period_larger_than_candles_is_all_none():
    candles = _candles([1.0, 2.0])

    result = sma(candles, period=3)

    assert result == [None, None]


def test_sma_with_empty_candles_returns_empty_list():
    assert sma([], period=3) == []


def test_sma_rejects_non_positive_period():
    with pytest.raises(ValueError):
        sma(_candles([1.0, 2.0]), period=0)


def test_ema_seeds_with_sma_and_then_smooths():
    candles = _candles([10.0, 20.0, 10.0, 20.0, 10.0, 20.0, 10.0])

    result = ema(candles, period=3)

    assert result[0] is None
    assert result[1] is None
    assert result[2] == pytest.approx(13.333333333333334)
    assert result[3] == pytest.approx(16.666666666666668)
    assert result[4] == pytest.approx(13.333333333333334)
    assert result[5] == pytest.approx(16.666666666666668)
    assert result[6] == pytest.approx(13.333333333333334)


def test_ema_with_period_larger_than_candles_is_all_none():
    candles = _candles([1.0, 2.0])

    result = ema(candles, period=3)

    assert result == [None, None]


def test_ema_with_empty_candles_returns_empty_list():
    assert ema([], period=3) == []


def test_ema_rejects_non_positive_period():
    with pytest.raises(ValueError):
        ema(_candles([1.0, 2.0]), period=0)


def test_rsi_seeds_with_average_gain_and_loss_and_then_smooths():
    candles = _candles([44.00, 44.25, 44.5, 43.75, 44.5, 44.0])

    result = rsi(candles, period=4)

    assert result[:4] == [None, None, None, None]
    assert result[4] == pytest.approx(62.5)
    assert result[5] == pytest.approx(46.875)


def test_rsi_is_100_when_there_are_only_gains():
    candles = _candles([1.0, 2.0, 3.0, 4.0, 5.0])

    result = rsi(candles, period=3)

    assert result[:3] == [None, None, None]
    assert result[3] == pytest.approx(100.0)
    assert result[4] == pytest.approx(100.0)


def test_rsi_with_minimal_number_of_candles_sets_single_value():
    candles = _candles([1.0, 2.0, 3.0])

    result = rsi(candles, period=2)

    assert result == [None, None, 100.0]


def test_rsi_with_period_larger_than_candles_is_all_none():
    candles = _candles([1.0, 2.0])

    result = rsi(candles, period=3)

    assert result == [None, None]


def test_rsi_with_empty_candles_returns_empty_list():
    assert rsi([], period=3) == []


def test_rsi_rejects_non_positive_period():
    with pytest.raises(ValueError):
        rsi(_candles([1.0, 2.0]), period=0)
