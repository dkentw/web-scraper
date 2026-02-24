# Web Scraper

A modular Python web scraper that uses Playwright to scrape dynamic, JavaScript-rendered pages. It extracts structured data using configurable YAML-based extractors and saves results to JSON or SQLite.

## Setup

Requires [uv](https://docs.astral.sh/uv/) for dependency management.

```bash
# Install dependencies
uv sync

# Install Playwright browser
uv run playwright install chromium
```

## Usage

```bash
uv run python -m scraper --url <URL> --category <CATEGORY> [--output <FORMAT>] [--output-path <PATH>]
```

### Options

| Option | Values | Default | Description |
|--------|--------|---------|-------------|
| `--url` | any URL | *(required)* | The URL to scrape |
| `--category` | `bus` | *(required)* | Category of site to scrape (determines which extractor to use) |
| `--output` | `json`, `sqlite`, `both` | `json` | Output storage format |
| `--output-path` | file path | `output/results.json` or `output/scraper.db` | Custom output location |

### Examples

```bash
# Scrape bus route info and save as JSON
uv run python -m scraper --url https://example.com/bus/route --category bus

# Save to SQLite
uv run python -m scraper --url https://example.com/bus/route --category bus --output sqlite

# Save to both JSON and SQLite
uv run python -m scraper --url https://example.com/bus/route --category bus --output both

# Custom output path
uv run python -m scraper --url https://example.com/bus/route --category bus --output-path results/data.json
```

## Extractors

Extractors define how to pull structured data from a page. Each category maps to an extractor class and a YAML config file.

### YAML config format

```yaml
field_name:
  selector: "css selector"
  type: text | extract_func
```

- **`text`** — Extracts the text content of the first element matching the CSS selector.
- **`extract_func`** — Delegates to the extractor's `extract()` method for custom parsing logic.

### Adding a new category

1. Create a YAML config in `src/scraper/extractors/configs/`.
2. Create an extractor class that extends `BaseExtractor` and implements `extract()`.
3. Register it in `src/scraper/config.py` under `EXTRACTOR_CONF`.
4. Export the class from `src/scraper/extractors/__init__.py`.

## Project Structure

```
src/scraper/
├── main.py                # CLI entry point (argparse)
├── config.py              # Settings, user-agent, timeouts, extractor registry
├── dynamic_scraper.py     # Playwright-based browser scraping + extractor dispatch
├── utils.py               # Logger setup, retry decorator
├── extractors/
│   ├── base_extractor.py  # Base class — YAML-driven CSS selector extraction
│   ├── bus_extractor.py   # Bus route extractor (stops, directions)
│   └── configs/
│       └── bus_info.yaml  # CSS selectors for bus route pages
└── storage/
    ├── json_store.py      # Save results to JSON files
    └── sqlite_store.py    # Save results to SQLite database
```

## Running Tests

```bash
uv run pytest tests/ -v
```
