import scrapetube

class Videos():
    def __init__(self):
        self.videos = list()

    def search_video(self, id=None):
        if id is not None:
            self.videos = []
            videos = scrapetube.get_search(id, results_type='video', limit=6)
            for vid in videos:
                video_id = vid.get('videoId', {})
                self.videos.append(video_id)

        else:
            print('no id')

        return self.videos
            