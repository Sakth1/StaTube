import yt_dlp
import json

class Videos:
    def __init__(self):
        self.content = {}
        self.videos = {}
        self.live = {}
        self.shorts = {}
        self.video_url = []

    def save_json(self, info):
        with open('terminal.json', 'w') as f:
            json.dump(info, f)

    def fetch_video_urls(self, channel_url):
        #for debug
        ydl_opts = {
            'extract_flat': True,
            'skip_download': True,
            'quiet': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(channel_url, download=False)

            #self.save_json(info)

            if 'entries' in info:
                channel_name = info.get('title')
                entries = info.get('entries')
                for entry in entries:
                    entry_name = entry.get('title')

                    if entry_name == f'{channel_name} - Videos':
                        video_entries = entry.get('entries')

                        for i,video_entry in enumerate(video_entries):
                            title = video_entry.get('title')
                            url = video_entry.get('url')
                            views = video_entry.get('view_count')
                            duration = video_entry.get('duration')
                            self.videos[i] = {
                                "title": title,
                                "url": url,
                                "views": views,
                                "duration": duration
                            }

                            self.video_url.append(url)
                    
                    elif entry_name == f'{channel_name} - Live':
                        live_entries = entry.get('entries')
                        for i,live_entry in enumerate(live_entries):
                            title = live_entry.get('title')
                            url = live_entry.get('url')
                            views = live_entry.get('view_count')
                            duration = live_entry.get('duration')
                            self.live[i] = {
                                "title": title,
                                "url": url,
                                "views": views,
                                "duration": duration
                            }

                    elif entry_name == f'{channel_name} - Shorts':
                        shorts_entries = entry.get('entries')
                        for i,shorts_entry in enumerate(shorts_entries):
                            title = shorts_entry.get('title')
                            url = shorts_entry.get('url')
                            views = shorts_entry.get('view_count')
                            duration = shorts_entry.get('duration')
                            self.shorts[i] = {
                                "title": title,
                                "url": url,
                                "views": views,
                                "duration": duration
                            }


                self.content = {
                    "live": self.live,
                    "shorts": self.shorts,
                    "videos": self.videos,
                    "video_url": self.video_url #temp
                }

        return self.content
