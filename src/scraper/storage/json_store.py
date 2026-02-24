"""Save scraped data to JSON files."""

import json
from pathlib import Path

from scraper.config import OUTPUT_DIR
from scraper.utils import get_logger

log = get_logger(__name__)


def save(data: dict, filepath: str | Path | None = None) -> Path:
    """Save data dict to a JSON file. Returns the path written to."""
    if filepath is None:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        filepath = OUTPUT_DIR / "results.json"
    else:
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    log.info("Saved to %s", filepath)
    return filepath
