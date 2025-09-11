import scrapetube

class Search():
    def __init__(self):
        self.channels = list()

    def search_channel(self, name=None):
        if name is not None:
            self.channels = {}
            channel_name = []
            self.search = scrapetube.get_search(name, results_type='channel', limit=6)
            for vid in self.search:
                title = vid.get('title', {}).get('simpleText')
                channelid = vid.get('channelId')
                self.channels[channelid] = title

            return self.channels

        else:
            return ["None"]
