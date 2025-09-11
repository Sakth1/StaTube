import scrapetube

class Search():
    def __init__(self):
        self.channels = list()

    def search_channel(self, name=None):
        if name is not None:
            self.channels = []
            self.search = scrapetube.get_search(name, results_type='channel', limit=6)
            for vid in self.search:
                title = vid.get('title', {}).get('simpleText')
                self.channels.append(title)

            return self.channels

        else:
            return ["None"]
