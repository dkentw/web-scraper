"""Default settings and constants."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"
DB_PATH = OUTPUT_DIR / "scraper.db"

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)

REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_DELAY = 2

EXTRACTOR_CONF = {
    'bus': {
        'config': PROJECT_ROOT / 'src' / 'scraper' / 'extractors' / 'configs' / 'bus_info.yaml',
        'extractors': 'BusExtractor'
    }
}
