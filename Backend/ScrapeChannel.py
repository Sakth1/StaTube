import scrapetube

class Search:
    def __init__(self):
        self.channels = {}

    def search_channel(self, name=None):
        if name is not None:
            self.channels = {}
            search_results = scrapetube.get_search(name, results_type='channel', limit=6)

            for ch in search_results:
                title = ch.get('title', {}).get('simpleText')
                channel_id = ch.get('channelId')

                if channel_id:
                    url = f"https://www.youtube.com/channel/{channel_id}"
                    self.channels[channel_id] = {
                        "title": title,
                        "url": url
                    }

            return self.channels

        else:
            return {"None": {"title": None, "url": None}}


# Example usage
if __name__ == "__main__":
    search = Search()
    results = search.search_channel("mrbeast")
    for cid, data in results.items():
        print(f"Title: {data['title']} | URL: {data['url']}")
