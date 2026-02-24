"""Dynamic scraper using Playwright for JavaScript-rendered pages."""

import importlib

from playwright.sync_api import sync_playwright
from selectolax.lexbor import LexborHTMLParser

from scraper.config import DEFAULT_USER_AGENT, REQUEST_TIMEOUT, EXTRACTOR_CONF
from scraper.utils import get_logger, retry

log = get_logger(__name__)

def get_extractor(parser: LexborHTMLParser, category: str):
    conf = EXTRACTOR_CONF[category]
    module = importlib.import_module('scraper.extractors')
    extractor_cls = getattr(module, conf['extractors'])
    return extractor_cls(parser, category)

@retry()
def scrape(url: str, category: str) -> dict:
    """Fetch a URL with a headless browser and extract content.

    Returns a dict with url, title, and text content.
    """
    log.info("Dynamic scrape: %s", url)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent=DEFAULT_USER_AGENT)
        page.goto(url, timeout=REQUEST_TIMEOUT * 1000)

        dom = page.evaluate("""
            () => {
                const scripts = document.querySelectorAll('script, style');
                scripts.forEach(el => el.remove());
                return document.body.innerHTML;
            }
        """)

        parser = LexborHTMLParser(dom)
        extractor = get_extractor(parser, category)

        extractor.data.update({'url': url, 'title': page.title()})

        browser.close()

    return extractor.data
