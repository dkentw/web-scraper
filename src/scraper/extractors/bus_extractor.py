from .base_extractor import BaseExtractor


class BusExtractor(BaseExtractor):
    def extract(self):
        self.data['mapstops'] = []
    
        for node in self.parser.css(self.model['mapstops']['selector']):
            stop_info = []

            if node.text() == '':
                continue

            for item in node.text().split('\n'):
                stop = item.strip( ) 
                if stop != '':
                    stop_info.append(stop)
            self.data['mapstops'].append(tuple(stop_info))