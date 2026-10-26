"""Data model for a single OHLCV candle."""

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Candle:
    """A single OHLCV candle for one symbol and interval.

    The timestamp is the candle open time in milliseconds since the epoch.
    """

    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float

    def __post_init__(self) -> None:
        if self.timestamp < 0:
            raise ValueError(f"timestamp must be >= 0, got {self.timestamp}")
        for name in ("open", "high", "low", "close", "volume"):
            value = getattr(self, name)
            # NaN fails every comparison below, so it has to be rejected here.
            if not math.isfinite(value):
                raise ValueError(f"{name} must be finite, got {value}")
        for name in ("open", "high", "low", "close"):
            value = getattr(self, name)
            if value <= 0:
                raise ValueError(f"{name} must be > 0, got {value}")
        if self.volume < 0:
            raise ValueError(f"volume must be >= 0, got {self.volume}")
        if self.high < self.low:
            raise ValueError(f"high ({self.high}) must be >= low ({self.low})")
        if self.high < self.open or self.high < self.close:
            raise ValueError(f"high ({self.high}) must be >= open and close")
        if self.low > self.open or self.low > self.close:
            raise ValueError(f"low ({self.low}) must be <= open and close")
