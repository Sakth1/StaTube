import yt_dlp
from datetime import datetime
from pathlib import Path
import os

from utils.Proxy import Proxy
from Data.DatabaseManager import DatabaseManager  


def download_with_proxy(url, save_path, proxy_url=None):
    if proxy_url is None:
        return
    
    import requests
    try:
        response = requests.get(url, proxies={'http': proxy_url, 'https': proxy_url}, timeout=15.0, stream=True)
        response.raise_for_status()
        with open(save_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
    except Exception as e:
        print(f"[ERROR] Failed to download {url}: {e}")

class Videos:
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.content = {}
        self.videos = {}
        self.live = {}
        self.shorts = {}
        self.video_url = []

    def fetch_video_urls(self, channel_id: int, channel_url: str):
        try:
            # yt_dlp options
            ydl_opts = {
                'extract_flat': True,
                'skip_download': True,
                'quiet': True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(channel_url, download=False)

                if 'entries' not in info:
                    return {}

                channel_name = info.get('title')
                entries = info.get('entries')

                for entry in entries:
                    entry_name = entry.get('title')
                    proxy_url = Proxy().get_working_proxy()

                    # --- Normal Videos ---
                    if entry_name == f'{channel_name} - Videos':
                        video_type = 'video'
                    elif entry_name == f'{channel_name} - Shorts':
                        video_type = 'shorts'
                    elif entry_name == f'{channel_name} - Live':
                        video_type = 'live'

                    video_entries = entry.get('entries')
                    for i, video_entry in enumerate(video_entries):
                        video_id = video_entry.get('id')
                        title = video_entry.get('title')
                        url = video_entry.get('url')
                        views = video_entry.get('view_count')
                        duration = video_entry.get('duration')

                        thumbnail_url = video_entry.get("thumbnails")[-1].get("url")
                        os.makedirs(f"{self.db.thumbnail_dir}/{channel_id}", exist_ok=True)
                        profile_save_path = rf"{self.db.thumbnail_dir}/{channel_id}/{video_id}.png"
                        download_with_proxy(thumbnail_url, profile_save_path, proxy_url)

                        # Insert into DB
                        self.db.insert("VIDEO", {
                            "video_id": video_id,
                            "channel_id": channel_id,
                            "video_type": video_type,
                            "video_url": url,
                            "title": title,
                            "desc": video_entry.get("description"),
                            "duration": duration,
                            "view_count": views,
                            "like_count": video_entry.get("like_count"),
                            "pub_date": video_entry.get("upload_date"),
                        })

            return

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Error while fetching video URLs: {e}")
            return {}
