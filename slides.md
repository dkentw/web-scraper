---
marp: true
theme: default
paginate: true
---

# Web Scraper

A modular, config-driven web scraper for dynamic pages

**Tech stack:** Python 3.12 | Playwright | selectolax | YAML extractors

---

## Problem

- Many websites render content with JavaScript — plain HTTP requests get empty pages
- Different site categories need different parsing logic
- We want structured data output, not raw HTML

---

## Architecture Overview

```
CLI (argparse)
  |
  v
dynamic_scraper.py        -- Playwright headless browser
  |
  v
Extractor (YAML + class)  -- config-driven data extraction
  |
  v
Storage (JSON / SQLite)    -- pluggable output backends
```

---

## Project Structure

```
src/scraper/
├── main.py                # CLI entry point
├── config.py              # Settings + extractor registry
├── dynamic_scraper.py     # Playwright scraping pipeline
├── utils.py               # Logger, retry decorator
├── extractors/
│   ├── base_extractor.py  # YAML-driven base class
│   ├── bus_extractor.py   # Bus route extractor
│   └── configs/
│       └── bus_info.yaml  # CSS selectors for bus pages
└── storage/
    ├── json_store.py      # JSON output
    └── sqlite_store.py    # SQLite output
```

---

## Tech Stack

| Component | Library | Why |
|-----------|---------|-----|
| Browser automation | **Playwright** | Modern, fast, auto-wait, better API than Selenium |
| HTML parsing | **selectolax** (Lexbor) | 30x faster than BeautifulSoup, CSS selector support |
| Config parsing | **PyYAML** | Declarative extraction rules per category |
| Storage | **sqlite3** / **json** | Zero-dependency, stdlib — no external DB needed |
| Env management | **uv** | Fast, single-tool Python project management |

---

## Scraping Pipeline

```python
def scrape(url: str, category: str) -> dict:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent=DEFAULT_USER_AGENT)
        page.goto(url, timeout=REQUEST_TIMEOUT * 1000)

        # Strip scripts/styles, get clean innerHTML
        dom = page.evaluate("() => { ... return document.body.innerHTML }")

        # Parse with selectolax and run extractor
        parser = LexborHTMLParser(dom)
        extractor = get_extractor(parser, category)

        extractor.data.update({'url': url, 'title': page.title()})
        browser.close()
    return extractor.data
```

---

## Extractor System

**YAML config** defines what to extract:

```yaml
bus_number:
  selector: "span.rt_title"
  type: text              # grab text from first match

direction:
  selector: "span.rt_dir_go"
  type: text

mapstops:
  selector: "#plMapStops > div"
  type: extract_func      # delegate to custom method
```

---

## Extractor Classes

**BaseExtractor** reads the YAML and auto-extracts `text` fields via CSS selectors.
For `extract_func` fields, it delegates to a subclass method.

```python
class BaseExtractor:
    def __init__(self, parser, category):
        self.model = yaml.load(config_file)
        for key, value in self.model.items():
            if value['type'] == 'text':
                self.data[key] = parser.css_first(value['selector']).text()
            if value['type'] == 'extract_func':
                self.extract()  # subclass implements this

class BusExtractor(BaseExtractor):
    def extract(self):
        # custom logic for parsing bus stop lists
```

---

## Dynamic Extractor Dispatch

Extractors are resolved at runtime via `importlib`:

```python
EXTRACTOR_CONF = {
    'bus': {
        'config': '...extractors/configs/bus_info.yaml',
        'extractors': 'BusExtractor'
    }
}

def get_extractor(parser, category):
    conf = EXTRACTOR_CONF[category]
    module = importlib.import_module('scraper.extractors')
    extractor_cls = getattr(module, conf['extractors'])
    return extractor_cls(parser, category)
```

Adding a new category = new YAML + new class + one dict entry.

---

## Storage Backends

Both expose the same interface: `save(data, path)`

**JSON** — writes structured dict directly:
```python
json.dump(data, f, indent=2, ensure_ascii=False)
```

**SQLite** — stores URL + full JSON blob with timestamp:
```sql
CREATE TABLE pages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  url TEXT,
  raw_json TEXT,
  scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## CLI Usage

```bash
uv run python -m scraper \
    --url https://example.com/bus/route \
    --category bus \
    --output json
```

| Flag | Required | Values |
|------|----------|--------|
| `--url` | yes | Target URL |
| `--category` | yes | `bus` (extensible) |
| `--output` | no | `json` / `sqlite` / `both` |
| `--output-path` | no | Custom file path |

---

## Key Design Decisions

1. **Playwright over Selenium** — faster, modern async API, built-in auto-wait
2. **selectolax over BeautifulSoup** — C-based Lexbor engine, significantly faster parsing
3. **YAML-driven extraction** — add new site categories without changing scraper code
4. **Inheritance for extractors** — `BaseExtractor` handles common patterns, subclasses handle edge cases
5. **`importlib` dispatch** — extractor classes resolved by name from config, fully decoupled

---

## Extending the Scraper

To add a new site category (e.g. `train`):

```
1. Create extractors/configs/train_info.yaml
2. Create extractors/train_extractor.py
3. Add to EXTRACTOR_CONF in config.py
4. Export from extractors/__init__.py
```

No changes needed in `dynamic_scraper.py` or `main.py`.

---

## Summary

- **Playwright** handles JS-rendered pages via headless Chromium
- **selectolax** provides fast, CSS-selector-based DOM parsing
- **YAML configs** make extraction rules declarative and easy to maintain
- **Pluggable storage** — JSON for quick inspection, SQLite for querying
- **Modular design** — new categories require zero changes to core scraping code
