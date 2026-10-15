from ohlcv_lab.config import Config, DEFAULT_DATA_PATH, DEFAULT_INTERVAL, DEFAULT_SYMBOLS


def test_defaults():
    config = Config()
    assert config.symbols == DEFAULT_SYMBOLS
    assert config.interval == DEFAULT_INTERVAL
    assert config.data_path == DEFAULT_DATA_PATH


def test_overrides():
    config = Config(symbols=("SOL/USDT",), interval="1d", data_path="/tmp/ohlcv")
    assert config.symbols == ("SOL/USDT",)
    assert config.interval == "1d"
    assert config.data_path == "/tmp/ohlcv"
