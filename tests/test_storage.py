from ohlcv_lab.models import Candle
from ohlcv_lab.storage import connect, fetch_candles, upsert_candles


def _select_all(connection):
    rows = connection.execute(
        "SELECT symbol, interval, timestamp, open, high, low, close, volume "
        "FROM candles ORDER BY symbol, interval, timestamp"
    ).fetchall()
    return rows


def test_connect_creates_schema(tmp_path):
    connection = connect(str(tmp_path / "ohlcv.sqlite"))
    tables = connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'candles'"
    ).fetchall()
    assert tables == [("candles",)]


def test_upsert_inserts_new_candles(tmp_path):
    connection = connect(str(tmp_path / "ohlcv.sqlite"))
    candle = Candle(timestamp=1_700_000_000_000, open=100.0, high=110.0, low=95.0, close=105.0, volume=12.5)

    upsert_candles(connection, "BTC/USDT", "1h", [candle])

    rows = _select_all(connection)
    assert rows == [("BTC/USDT", "1h", 1_700_000_000_000, 100.0, 110.0, 95.0, 105.0, 12.5)]


def test_upsert_updates_existing_candle_in_place(tmp_path):
    connection = connect(str(tmp_path / "ohlcv.sqlite"))
    original = Candle(timestamp=1_700_000_000_000, open=100.0, high=110.0, low=95.0, close=105.0, volume=12.5)
    updated = Candle(timestamp=1_700_000_000_000, open=100.0, high=120.0, low=90.0, close=115.0, volume=20.0)

    upsert_candles(connection, "BTC/USDT", "1h", [original])
    upsert_candles(connection, "BTC/USDT", "1h", [updated])

    rows = _select_all(connection)
    assert rows == [("BTC/USDT", "1h", 1_700_000_000_000, 100.0, 120.0, 90.0, 115.0, 20.0)]


def test_upsert_keeps_candles_for_different_symbols_and_intervals_separate(tmp_path):
    connection = connect(str(tmp_path / "ohlcv.sqlite"))
    candle = Candle(timestamp=1_700_000_000_000, open=1.0, high=1.0, low=1.0, close=1.0, volume=0.0)

    upsert_candles(connection, "BTC/USDT", "1h", [candle])
    upsert_candles(connection, "BTC/USDT", "4h", [candle])
    upsert_candles(connection, "ETH/USDT", "1h", [candle])

    rows = _select_all(connection)
    assert len(rows) == 3


def test_upsert_handles_multiple_candles_at_once(tmp_path):
    connection = connect(str(tmp_path / "ohlcv.sqlite"))
    candles = [
        Candle(timestamp=1_700_000_000_000, open=1.0, high=1.0, low=1.0, close=1.0, volume=0.0),
        Candle(timestamp=1_700_000_003_600, open=2.0, high=2.0, low=2.0, close=2.0, volume=0.0),
    ]

    upsert_candles(connection, "BTC/USDT", "1h", candles)

    rows = _select_all(connection)
    assert [row[2] for row in rows] == [1_700_000_000_000, 1_700_000_003_600]


def test_fetch_candles_returns_all_candles_for_symbol_and_interval(tmp_path):
    connection = connect(str(tmp_path / "ohlcv.sqlite"))
    candles = [
        Candle(timestamp=1_700_000_000_000, open=1.0, high=1.0, low=1.0, close=1.0, volume=0.0),
        Candle(timestamp=1_700_000_003_600, open=2.0, high=2.0, low=2.0, close=2.0, volume=0.0),
    ]
    upsert_candles(connection, "BTC/USDT", "1h", candles)

    result = fetch_candles(connection, "BTC/USDT", "1h")

    assert result == candles


def test_fetch_candles_filters_by_time_range(tmp_path):
    connection = connect(str(tmp_path / "ohlcv.sqlite"))
    candles = [
        Candle(timestamp=1_700_000_000_000, open=1.0, high=1.0, low=1.0, close=1.0, volume=0.0),
        Candle(timestamp=1_700_000_003_600, open=2.0, high=2.0, low=2.0, close=2.0, volume=0.0),
        Candle(timestamp=1_700_000_007_200, open=3.0, high=3.0, low=3.0, close=3.0, volume=0.0),
    ]
    upsert_candles(connection, "BTC/USDT", "1h", candles)

    result = fetch_candles(
        connection, "BTC/USDT", "1h", start_time=1_700_000_003_600, end_time=1_700_000_007_200
    )

    assert result == candles[1:]


def test_fetch_candles_ignores_other_symbols_and_intervals(tmp_path):
    connection = connect(str(tmp_path / "ohlcv.sqlite"))
    candle = Candle(timestamp=1_700_000_000_000, open=1.0, high=1.0, low=1.0, close=1.0, volume=0.0)
    upsert_candles(connection, "BTC/USDT", "1h", [candle])
    upsert_candles(connection, "BTC/USDT", "4h", [candle])
    upsert_candles(connection, "ETH/USDT", "1h", [candle])

    result = fetch_candles(connection, "BTC/USDT", "1h")

    assert result == [candle]


def test_fetch_candles_returns_empty_list_when_nothing_stored(tmp_path):
    connection = connect(str(tmp_path / "ohlcv.sqlite"))

    result = fetch_candles(connection, "BTC/USDT", "1h")

    assert result == []
