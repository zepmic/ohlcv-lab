# ohlcv-lab

Krypto-Marktdaten holen, speichern, Indikatoren berechnen, im Dashboard anzeigen.
Nur Analyse und Backtesting-Daten – kein Trading, keine Orders, keine API-Keys mit Handelsrechten.

## Setup

```bash
pip install -e ".[dev]"
```

## Tests

```bash
python -m pytest -q
```

## Struktur

- `src/ohlcv_lab/` – Paketcode (src-Layout)
- `tests/` – pytest-Tests
- `ROADMAP.md` – geplante Schritte
