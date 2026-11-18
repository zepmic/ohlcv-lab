import csv

import pyarrow.parquet as pq

from ohlcv_lab.export import export_candles_to_csv, export_candles_to_parquet
from ohlcv_lab.models import Candle

CANDLES = [
    Candle(timestamp=1_700_000_000_000, open=100.0, high=110.0, low=95.0, close=105.0, volume=12.5),
    Candle(timestamp=1_700_000_003_600, open=105.0, high=108.0, low=102.0, close=106.0, volume=8.0),
]


def test_export_candles_to_csv_writes_header_and_rows(tmp_path):
    path = tmp_path / "candles.csv"

    export_candles_to_csv(CANDLES, str(path))

    with open(path, newline="") as file:
        rows = list(csv.reader(file))
    assert rows[0] == ["timestamp", "open", "high", "low", "close", "volume"]
    assert rows[1:] == [
        ["1700000000000", "100.0", "110.0", "95.0", "105.0", "12.5"],
        ["1700000003600", "105.0", "108.0", "102.0", "106.0", "8.0"],
    ]


def test_export_candles_to_csv_writes_only_header_when_empty(tmp_path):
    path = tmp_path / "candles.csv"

    export_candles_to_csv([], str(path))

    with open(path, newline="") as file:
        rows = list(csv.reader(file))
    assert rows == [["timestamp", "open", "high", "low", "close", "volume"]]


def test_export_candles_to_parquet_writes_rows(tmp_path):
    path = tmp_path / "candles.parquet"

    export_candles_to_parquet(CANDLES, str(path))

    table = pq.read_table(path)
    assert table.to_pylist() == [
        {
            "timestamp": 1_700_000_000_000,
            "open": 100.0,
            "high": 110.0,
            "low": 95.0,
            "close": 105.0,
            "volume": 12.5,
        },
        {
            "timestamp": 1_700_000_003_600,
            "open": 105.0,
            "high": 108.0,
            "low": 102.0,
            "close": 106.0,
            "volume": 8.0,
        },
    ]


def test_export_candles_to_parquet_writes_empty_table_when_no_candles(tmp_path):
    path = tmp_path / "candles.parquet"

    export_candles_to_parquet([], str(path))

    table = pq.read_table(path)
    assert table.num_rows == 0
    assert table.column_names == ["timestamp", "open", "high", "low", "close", "volume"]
