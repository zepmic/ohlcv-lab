"""Konfiguration für Symbole, Intervall und Datenpfad."""

from dataclasses import dataclass

DEFAULT_SYMBOLS: tuple[str, ...] = ("BTC/USDT", "ETH/USDT")
DEFAULT_INTERVAL = "1h"
DEFAULT_DATA_PATH = "data"


@dataclass
class Config:
    """Laufzeiteinstellungen für das Abrufen und Speichern von OHLCV-Daten."""

    symbols: tuple[str, ...] = DEFAULT_SYMBOLS
    interval: str = DEFAULT_INTERVAL
    data_path: str = DEFAULT_DATA_PATH
