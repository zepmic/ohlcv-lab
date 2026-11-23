"""Indicators computed on candle closing prices."""

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


def rsi(candles: list[Candle], period: int) -> list[float | None]:
    """Compute the relative strength index of closing prices over `period` candles.

    Uses Wilder's smoothing method. Returns one value per candle, in the
    same order as `candles`. The first `period` entries are None because
    at least `period` price changes are needed to seed the average gain
    and loss; the entry at index `period` seeds the averages with the
    simple mean of the first `period` gains and losses, and every later
    entry smooths the previous averages with the next gain or loss.
    """
    if period < 1:
        raise ValueError(f"period must be >= 1, got {period}")
    closes = [candle.close for candle in candles]
    result: list[float | None] = [None] * len(closes)
    if len(closes) <= period:
        return result
    changes = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    gains = [max(change, 0.0) for change in changes]
    losses = [max(-change, 0.0) for change in changes]
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    result[period] = _rsi_from_averages(avg_gain, avg_loss)
    for i in range(period, len(changes)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        result[i + 1] = _rsi_from_averages(avg_gain, avg_loss)
    return result


def _rsi_from_averages(avg_gain: float, avg_loss: float) -> float:
    if avg_gain == 0 and avg_loss == 0:
        return 50.0
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - 100 / (1 + rs)
