from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_readme_exists():
    readme = ROOT / "README.md"
    assert readme.is_file()
    assert readme.read_text(encoding="utf-8").strip()


def test_package_importable():
    import ohlcv_lab

    assert ohlcv_lab.__version__
