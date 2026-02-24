"""Unit tests for the web scraper project."""

import json
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

import pytest

from scraper.config import EXTRACTOR_CONF
from scraper.storage import json_store, sqlite_store
from scraper.main import parse_args
from scraper.utils import retry


SAMPLE_DATA = {
    "url": "https://example.com",
    "title": "Example Domain",
    "text": "This domain is for use in illustrative examples.",
}

BUS_MODEL = {
    "route": {"type": "text", "selector": ".route"},
    "mapstops": {"type": "extract_func", "selector": ".stop"},
}


# ---------------------------------------------------------------------------
# parse_args
# ---------------------------------------------------------------------------

def test_parse_args_defaults():
    args = parse_args(["--url", "https://example.com", "--category", "bus"])
    assert args.url == "https://example.com"
    assert args.category == "bus"
    assert args.output == "json"


def test_parse_args_all_options():
    args = parse_args([
        "--url", "https://example.com",
        "--category", "bus",
        "--output", "sqlite",
        "--output-path", "/tmp/test.db",
    ])
    assert args.category == "bus"
    assert args.output == "sqlite"
    assert args.output_path == "/tmp/test.db"


def test_parse_args_invalid_category_exits():
    with pytest.raises(SystemExit):
        parse_args(["--url", "https://example.com", "--category", "invalid"])


def test_parse_args_missing_url_exits():
    with pytest.raises(SystemExit):
        parse_args(["--category", "bus"])


def test_parse_args_missing_category_exits():
    with pytest.raises(SystemExit):
        parse_args(["--url", "https://example.com"])


def test_parse_args_category_choices_match_config():
    """--category choices must stay in sync with EXTRACTOR_CONF keys."""
    for key in EXTRACTOR_CONF:
        args = parse_args(["--url", "https://example.com", "--category", key])
        assert args.category == key


# ---------------------------------------------------------------------------
# json_store
# ---------------------------------------------------------------------------

def test_json_store_save_creates_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "test.json"
        result = json_store.save(SAMPLE_DATA, path)
        assert result == path
        assert path.exists()


def test_json_store_save_content():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "test.json"
        json_store.save(SAMPLE_DATA, path)
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["title"] == "Example Domain"


def test_json_store_overwrites_existing_file():
    new_data = {"url": "https://new.com", "title": "New"}
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "test.json"
        json_store.save(SAMPLE_DATA, path)
        json_store.save(new_data, path)
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["title"] == "New"


# ---------------------------------------------------------------------------
# sqlite_store
# ---------------------------------------------------------------------------

def test_sqlite_store_saves_row():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        sqlite_store.save(SAMPLE_DATA, db_path)
        conn = sqlite3.connect(db_path)
        rows = conn.execute("SELECT url FROM pages").fetchall()
        conn.close()
        assert len(rows) == 1
        assert rows[0] == ("https://example.com",)


def test_sqlite_store_raw_json_roundtrip():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        sqlite_store.save(SAMPLE_DATA, db_path)
        conn = sqlite3.connect(db_path)
        raw = conn.execute("SELECT raw_json FROM pages").fetchone()[0]
        conn.close()
        assert json.loads(raw)["title"] == SAMPLE_DATA["title"]


def test_sqlite_store_no_title_column():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        sqlite_store.save(SAMPLE_DATA, db_path)
        conn = sqlite3.connect(db_path)
        columns = [row[1] for row in conn.execute("PRAGMA table_info(pages)").fetchall()]
        conn.close()
        assert "title" not in columns
        assert "text" not in columns


def test_sqlite_store_appends():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        sqlite_store.save(SAMPLE_DATA, db_path)
        sqlite_store.save(SAMPLE_DATA, db_path)
        conn = sqlite3.connect(db_path)
        count = conn.execute("SELECT COUNT(*) FROM pages").fetchone()[0]
        conn.close()
        assert count == 2


# ---------------------------------------------------------------------------
# retry
# ---------------------------------------------------------------------------

def test_retry_succeeds_after_failure():
    call_count = 0

    @retry(max_attempts=3, delay=0)
    def flaky():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ConnectionError("fail")
        return "ok"

    assert flaky() == "ok"
    assert call_count == 3


def test_retry_raises_after_all_attempts():
    @retry(max_attempts=2, delay=0)
    def always_fails():
        raise ValueError("always")

    with pytest.raises(ValueError, match="always"):
        always_fails()


def test_retry_first_attempt_success():
    @retry(max_attempts=3, delay=0)
    def good():
        return "done"

    assert good() == "done"


# ---------------------------------------------------------------------------
# BusExtractor
# ---------------------------------------------------------------------------

def _make_mock_parser(route_text="Route 99", stop_nodes=None):
    mock_parser = MagicMock()
    mock_parser.css_first.return_value.text.return_value = route_text
    mock_parser.css.return_value = stop_nodes or []
    return mock_parser


def _make_stop_node(text):
    node = MagicMock()
    node.text.return_value = text
    return node


def test_bus_extractor_text_field():
    mock_parser = _make_mock_parser(route_text="Route 42")
    with patch("builtins.open", mock_open()), patch("yaml.load", return_value=BUS_MODEL):
        from scraper.extractors.bus_extractor import BusExtractor
        extractor = BusExtractor(mock_parser, "bus")
    assert extractor.data["route"] == "Route 42"


def test_bus_extractor_mapstops_parsed():
    nodes = [_make_stop_node("Stop A\nStop B\n"), _make_stop_node("Stop C\n")]
    mock_parser = _make_mock_parser(stop_nodes=nodes)
    with patch("builtins.open", mock_open()), patch("yaml.load", return_value=BUS_MODEL):
        from scraper.extractors.bus_extractor import BusExtractor
        extractor = BusExtractor(mock_parser, "bus")
    assert ("Stop A", "Stop B") in extractor.data["mapstops"]
    assert ("Stop C",) in extractor.data["mapstops"]


def test_bus_extractor_skips_empty_nodes():
    nodes = [_make_stop_node(""), _make_stop_node("Stop A\n")]
    mock_parser = _make_mock_parser(stop_nodes=nodes)
    with patch("builtins.open", mock_open()), patch("yaml.load", return_value=BUS_MODEL):
        from scraper.extractors.bus_extractor import BusExtractor
        extractor = BusExtractor(mock_parser, "bus")
    assert len(extractor.data["mapstops"]) == 1


# ---------------------------------------------------------------------------
# get_extractor
# ---------------------------------------------------------------------------

def test_get_extractor_returns_bus_extractor():
    mock_parser = _make_mock_parser()
    with patch("builtins.open", mock_open()), patch("yaml.load", return_value=BUS_MODEL):
        from scraper.dynamic_scraper import get_extractor
        from scraper.extractors import BusExtractor
        extractor = get_extractor(mock_parser, "bus")
    assert isinstance(extractor, BusExtractor)


# ---------------------------------------------------------------------------
# dynamic_scraper.scrape
# ---------------------------------------------------------------------------

def test_scrape_returns_extractor_data():
    mock_extractor = MagicMock()
    mock_extractor.data = {"route": "Route 1", "mapstops": [("Stop A",)]}

    mock_page = MagicMock()
    mock_page.title.return_value = "Bus Route 1"
    mock_page.evaluate.return_value = "<div class='route'>Route 1</div>"

    mock_browser = MagicMock()
    mock_browser.new_page.return_value = mock_page

    with patch("scraper.dynamic_scraper.sync_playwright") as mock_sp, \
         patch("scraper.dynamic_scraper.LexborHTMLParser"), \
         patch("scraper.dynamic_scraper.get_extractor", return_value=mock_extractor):
        mock_sp.return_value.__enter__.return_value.chromium.launch.return_value = mock_browser

        from scraper.dynamic_scraper import scrape
        result = scrape("https://example.com", "bus")

    assert result["url"] == "https://example.com"
    assert result["title"] == "Bus Route 1"
    assert result["route"] == "Route 1"


def test_scrape_calls_goto_with_url():
    mock_extractor = MagicMock()
    mock_extractor.data = {}

    mock_page = MagicMock()
    mock_page.title.return_value = ""
    mock_page.evaluate.return_value = ""

    mock_browser = MagicMock()
    mock_browser.new_page.return_value = mock_page

    with patch("scraper.dynamic_scraper.sync_playwright") as mock_sp, \
         patch("scraper.dynamic_scraper.LexborHTMLParser"), \
         patch("scraper.dynamic_scraper.get_extractor", return_value=mock_extractor):
        mock_sp.return_value.__enter__.return_value.chromium.launch.return_value = mock_browser

        from scraper.dynamic_scraper import scrape
        scrape("https://example.com/bus/42", "bus")

    mock_page.goto.assert_called_once()
    assert mock_page.goto.call_args[0][0] == "https://example.com/bus/42"
