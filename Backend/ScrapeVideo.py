import yt_dlp
from datetime import datetime
import httpx
from pathlib import Path
import os

from utils.Proxy import Proxy
from Data.DatabaseManager import DatabaseManager  # Your DB class


async def download_with_proxy(url, save_path, proxy_url=Proxy().get_working_proxy()):
    async with httpx.AsyncClient(proxies=proxy_url, timeout=15.0) as client:
        async with client.stream("GET", url) as r:
            r.raise_for_status()
            with open(save_path, "wb") as f:
                async for chunk in r.aiter_bytes():
                    f.write(chunk)

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

                    # --- Normal Videos ---
                    if entry_name == f'{channel_name} - Videos':
                        video_type = 'video'
                    elif entry_name == f'{channel_name} - Shorts':
                        video_type = 'shorts'
                    elif entry_name == f'{channel_name} - Live':
                        video_type = 'live'

                    proxy_url = Proxy().get_working_proxy()
                    video_entries = entry.get('entries')
                    for i, video_entry in enumerate(video_entries):
                        video_id = video_entry.get('id')
                        title = video_entry.get('title')
                        url = video_entry.get('url')
                        views = video_entry.get('view_count')
                        duration = video_entry.get('duration')

                        thumbnail_url = "https:" + video_entry.get("thumbnails")[-1].get("url")
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
                            "status": "active",
                        })

                        self.videos[i] = {
                            "title": title,
                            "url": url,
                            "views": views,
                            "duration": duration
                        }
                        self.video_url.append(url)

                # Final structured dict (for immediate use)
                self.content = {
                    "videos": self.videos,
                }

            return self.content

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Error while fetching video URLs: {e}")
            return {}


if __name__ == "__main__":
    db = DatabaseManager()
    videos = Videos(db)

    # Let's say we already inserted a CHANNEL and got its id
    channel_id = 1  
    channel_url = "https://www.youtube.com/@mrbeast"

    results = videos.fetch_video_urls(channel_id, channel_url)

    print("Fetched:", results["videos"])
    print("Saved video entries in DB:", db.fetch("VIDEO", "channel_id=?", (channel_id,)))

    db.close()
