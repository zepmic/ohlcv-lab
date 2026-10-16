# ohlcv-lab

A small Python toolkit for crypto OHLCV data. The plan is to pull candles from public exchange APIs, store them locally, compute indicators on them, and browse the result in a dashboard.

It only deals with analysis and backtesting data. There is no trading code, and it never needs an API key with trading rights.

The project is at an early stage. So far there is the package skeleton and a config module.

## Setup

```bash
pip install -e ".[dev]"
```

## Tests

```bash
python -m pytest -q
```

## Layout

- `src/ohlcv_lab/` holds the package code (src layout)
- `tests/` holds the pytest tests
