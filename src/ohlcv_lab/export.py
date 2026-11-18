"""Export candles to CSV and Parquet files."""

import csv

import pyarrow as pa
import pyarrow.parquet as pq

from ohlcv_lab.models import Candle

FIELDNAMES = ["timestamp", "open", "high", "low", "close", "volume"]

PARQUET_SCHEMA = pa.schema(
    [
        ("timestamp", pa.int64()),
        ("open", pa.float64()),
        ("high", pa.float64()),
        ("low", pa.float64()),
        ("close", pa.float64()),
        ("volume", pa.float64()),
    ]
)


def export_candles_to_csv(candles: list[Candle], path: str) -> None:
    """Write candles to a CSV file with a header row, in the given order."""
    with open(path, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(FIELDNAMES)
        writer.writerows(
            (
                candle.timestamp,
                candle.open,
                candle.high,
                candle.low,
                candle.close,
                candle.volume,
            )
            for candle in candles
        )


def export_candles_to_parquet(candles: list[Candle], path: str) -> None:
    """Write candles to a Parquet file, in the given order."""
    table = pa.table(
        {name: [getattr(candle, name) for candle in candles] for name in FIELDNAMES},
        schema=PARQUET_SCHEMA,
    )
    pq.write_table(table, path)
