import scrapetube

name = input("Channel name: ")

search = scrapetube.get_search(name, results_type='channel', limit=6)
channels = set()

for vid in search:
    title = vid.get('title', {}).get('simpleText')
    channels.add(title)

print(channels)