"""CLI entry point for the web scraper."""

import argparse
import sys
from urllib.parse import urlparse

from scraper import dynamic_scraper
from scraper.config import EXTRACTOR_CONF
from scraper.storage import json_store, sqlite_store
from scraper.utils import get_logger

log = get_logger(__name__)

_ALLOWED_SCHEMES = {"http", "https"}


def _validate_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in _ALLOWED_SCHEMES:
        raise argparse.ArgumentTypeError(
            f"URL scheme {parsed.scheme!r} is not allowed. Use http or https."
        )
    return url


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="scraper",
        description="Scrape web pages and save results to JSON or SQLite.",
    )
    parser.add_argument("--url", required=True, type=_validate_url, help="URL to scrape (http/https only)")
    parser.add_argument("--category", required=True, choices=list(EXTRACTOR_CONF.keys()), help="The category of web site")
    parser.add_argument(
        "--output",
        choices=["json", "sqlite", "both"],
        default="json",
        help="Output format (default: json)",
    )
    parser.add_argument("--output-path", help="Custom output file/db path")
    return parser.parse_args(argv)

def _save(data: dict, output: str, output_path: str | None) -> None:
    if output in ("json", "both"):
        json_store.save(data, output_path)
    if output in ("sqlite", "both"):
        sqlite_store.save(data, output_path)

def run(args: argparse.Namespace) -> None:
    data = dynamic_scraper.scrape(args.url, args.category)
    log.info("Scraped: %s", data.get("title", "(no title)"))
    _save(data, args.output, args.output_path)


def main() -> None:
    args = parse_args()
    try:
        run(args)
    except Exception:
        log.exception("Scraping failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
