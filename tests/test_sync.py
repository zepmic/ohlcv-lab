from unittest.mock import MagicMock

from ohlcv_lab.models import Candle
from ohlcv_lab.storage import connect, fetch_candles, upsert_candles
from ohlcv_lab.sync import sync_missing_candles

ONE_HOUR_MS = 3_600_000


def _candle_at(timestamp):
    return Candle(timestamp=timestamp, open=1.0, high=1.0, low=1.0, close=1.0, volume=0.0)


def _fetcher_returning(candles):
    return MagicMock(return_value=candles)


def test_sync_fetches_entire_range_when_nothing_stored(tmp_path):
    connection = connect(str(tmp_path / "ohlcv.sqlite"))
    base = 1_700_000_000_000
    candles = [_candle_at(base), _candle_at(base + ONE_HOUR_MS)]
    fetch_range = _fetcher_returning(candles)

    result = sync_missing_candles(
        connection, "BTC/USDT", "1h", ONE_HOUR_MS, base, base + ONE_HOUR_MS, fetch_range
    )

    fetch_range.assert_called_once_with(
        "BTC/USDT", "1h", start_time=base, end_time=base + ONE_HOUR_MS
    )
    assert result == candles
    assert fetch_candles(connection, "BTC/USDT", "1h") == candles


def test_sync_fetches_only_the_gap_when_partial_data_stored(tmp_path):
    connection = connect(str(tmp_path / "ohlcv.sqlite"))
    base = 1_700_000_000_000
    upsert_candles(
        connection, "BTC/USDT", "1h", [_candle_at(base), _candle_at(base + 3 * ONE_HOUR_MS)]
    )
    filler = [_candle_at(base + ONE_HOUR_MS), _candle_at(base + 2 * ONE_HOUR_MS)]
    fetch_range = _fetcher_returning(filler)

    result = sync_missing_candles(
        connection, "BTC/USDT", "1h", ONE_HOUR_MS, base, base + 3 * ONE_HOUR_MS, fetch_range
    )

    fetch_range.assert_called_once_with(
        "BTC/USDT",
        "1h",
        start_time=base + ONE_HOUR_MS,
        end_time=base + 2 * ONE_HOUR_MS,
    )
    assert result == filler
    stored = fetch_candles(connection, "BTC/USDT", "1h")
    assert [candle.timestamp for candle in stored] == [
        base,
        base + ONE_HOUR_MS,
        base + 2 * ONE_HOUR_MS,
        base + 3 * ONE_HOUR_MS,
    ]


def test_sync_fetches_leading_and_trailing_ranges(tmp_path):
    connection = connect(str(tmp_path / "ohlcv.sqlite"))
    base = 1_700_000_000_000
    upsert_candles(connection, "BTC/USDT", "1h", [_candle_at(base + 2 * ONE_HOUR_MS)])
    fetch_range = MagicMock(
        side_effect=[
            [_candle_at(base), _candle_at(base + ONE_HOUR_MS)],
            [_candle_at(base + 3 * ONE_HOUR_MS), _candle_at(base + 4 * ONE_HOUR_MS)],
        ]
    )

    result = sync_missing_candles(
        connection, "BTC/USDT", "1h", ONE_HOUR_MS, base, base + 4 * ONE_HOUR_MS, fetch_range
    )

    assert fetch_range.call_args_list[0].kwargs == {
        "start_time": base,
        "end_time": base + ONE_HOUR_MS,
    }
    assert fetch_range.call_args_list[1].kwargs == {
        "start_time": base + 3 * ONE_HOUR_MS,
        "end_time": base + 4 * ONE_HOUR_MS,
    }
    assert len(result) == 4
    stored = fetch_candles(connection, "BTC/USDT", "1h")
    assert [candle.timestamp for candle in stored] == [
        base,
        base + ONE_HOUR_MS,
        base + 2 * ONE_HOUR_MS,
        base + 3 * ONE_HOUR_MS,
        base + 4 * ONE_HOUR_MS,
    ]


def test_sync_does_not_fetch_when_range_is_fully_covered(tmp_path):
    connection = connect(str(tmp_path / "ohlcv.sqlite"))
    base = 1_700_000_000_000
    candles = [_candle_at(base), _candle_at(base + ONE_HOUR_MS)]
    upsert_candles(connection, "BTC/USDT", "1h", candles)
    fetch_range = _fetcher_returning([])

    result = sync_missing_candles(
        connection, "BTC/USDT", "1h", ONE_HOUR_MS, base, base + ONE_HOUR_MS, fetch_range
    )

    fetch_range.assert_not_called()
    assert result == []
    assert fetch_candles(connection, "BTC/USDT", "1h") == candles


def test_sync_leaves_other_symbols_and_intervals_untouched(tmp_path):
    connection = connect(str(tmp_path / "ohlcv.sqlite"))
    base = 1_700_000_000_000
    other = _candle_at(base)
    upsert_candles(connection, "ETH/USDT", "1h", [other])
    fetch_range = _fetcher_returning([_candle_at(base)])

    sync_missing_candles(
        connection, "BTC/USDT", "1h", ONE_HOUR_MS, base, base, fetch_range
    )

    assert fetch_candles(connection, "ETH/USDT", "1h") == [other]
