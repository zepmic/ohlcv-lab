import pytest

from ohlcv_lab.models import Candle


def test_valid_candle():
    candle = Candle(timestamp=1_700_000_000_000, open=100.0, high=110.0, low=95.0, close=105.0, volume=12.5)
    assert candle.open == 100.0
    assert candle.high == 110.0
    assert candle.low == 95.0
    assert candle.close == 105.0
    assert candle.volume == 12.5


def test_rejects_negative_timestamp():
    with pytest.raises(ValueError):
        Candle(timestamp=-1, open=1.0, high=1.0, low=1.0, close=1.0, volume=0.0)


@pytest.mark.parametrize("field", ["open", "high", "low", "close"])
def test_rejects_non_positive_price(field):
    values = {"open": 1.0, "high": 1.0, "low": 1.0, "close": 1.0}
    values[field] = 0.0
    with pytest.raises(ValueError):
        Candle(timestamp=0, volume=0.0, **values)


def test_rejects_negative_volume():
    with pytest.raises(ValueError):
        Candle(timestamp=0, open=1.0, high=1.0, low=1.0, close=1.0, volume=-1.0)


def test_rejects_high_below_low():
    with pytest.raises(ValueError):
        Candle(timestamp=0, open=5.0, high=4.0, low=6.0, close=5.0, volume=0.0)


def test_rejects_high_below_open_or_close():
    with pytest.raises(ValueError):
        Candle(timestamp=0, open=10.0, high=9.0, low=1.0, close=5.0, volume=0.0)


def test_rejects_low_above_open_or_close():
    with pytest.raises(ValueError):
        Candle(timestamp=0, open=1.0, high=10.0, low=2.0, close=5.0, volume=0.0)
