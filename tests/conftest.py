"""Shared test setup: import scrape.py from the project folder, and block the network."""
import socket
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    """Every test runs offline: any attempt to open a connection fails the test."""
    def blocked(*args, **kwargs):
        raise RuntimeError("network access in a test")
    monkeypatch.setattr(socket.socket, "connect", blocked)


@pytest.fixture
def page1_html():
    return (FIXTURES / "page-1.html").read_text(encoding="utf-8")


@pytest.fixture
def book_html():
    return (FIXTURES / "a-light-in-the-attic_1000.html").read_text(encoding="utf-8")


@pytest.fixture
def tmp_data(tmp_path, monkeypatch):
    """Point scrape.py's data/ and data/raw/ at an empty temp folder."""
    import scrape
    monkeypatch.setattr(scrape, "DATA", tmp_path)
    monkeypatch.setattr(scrape, "RAW", tmp_path / "raw")
    return tmp_path
