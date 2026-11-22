"""Moving average indicators computed on candle closing prices."""

from ohlcv_lab.models import Candle


def sma(candles: list[Candle], period: int) -> list[float | None]:
    """Compute the simple moving average of closing prices over `period` candles.

    Returns one value per candle, in the same order as `candles`. The first
    `period - 1` entries are None because there are not yet enough candles
    to average.
    """
    if period < 1:
        raise ValueError(f"period must be >= 1, got {period}")
    closes = [candle.close for candle in candles]
    result: list[float | None] = [None] * len(closes)
    window_sum = 0.0
    for i, close in enumerate(closes):
        window_sum += close
        if i >= period:
            window_sum -= closes[i - period]
        if i >= period - 1:
            result[i] = window_sum / period
    return result


def ema(candles: list[Candle], period: int) -> list[float | None]:
    """Compute the exponential moving average of closing prices over `period` candles.

    Uses the standard smoothing factor `2 / (period + 1)`. The first
    `period - 1` entries are None, like `sma`; the entry at index `period - 1`
    seeds the average with the simple moving average of the first `period`
    closes, and every later entry builds on the previous EMA value.
    """
    if period < 1:
        raise ValueError(f"period must be >= 1, got {period}")
    closes = [candle.close for candle in candles]
    result: list[float | None] = [None] * len(closes)
    if len(closes) < period:
        return result
    multiplier = 2 / (period + 1)
    previous = sum(closes[:period]) / period
    result[period - 1] = previous
    for i in range(period, len(closes)):
        previous = (closes[i] - previous) * multiplier + previous
        result[i] = previous
    return result
