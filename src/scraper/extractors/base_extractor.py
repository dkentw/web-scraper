from selectolax.lexbor import LexborHTMLParser

import yaml

from scraper.config import EXTRACTOR_CONF

class BaseExtractor:
    def __init__(self, parser: LexborHTMLParser, category: str):
        self.category = category
        self.parser = parser
        self.model: dict = {}
        self.data = {}

        with open(EXTRACTOR_CONF[category]['config']) as f:
                self.model = yaml.safe_load(f)
        
        for key, value in self.model.items():
            if value.get('type') == 'text':
                node = self.parser.css_first(value['selector'])
                if node is None:
                    raise ValueError(
                        f"Selector {value['selector']!r} for field {key!r} matched nothing"
                    )
                self.data[key] = node.text()

            if value.get('type') == 'extract_func':
                self.extract()

    def extract(self):
        raise Exception('extract function need to be implemented.')