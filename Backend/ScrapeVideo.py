import yt_dlp
from datetime import datetime
import json
from pathlib import Path

from utils.Proxy import Proxy
from Data.DatabaseManager import DatabaseManager  # Your DB class


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

            # Choose proxy
            proxy = Proxy().get_working_proxy()
            if proxy:
                ydl_opts['proxy'] = proxy
                print(f"[INFO] Using proxy for videos: {proxy}")

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(channel_url, download=False)

                if 'entries' not in info:
                    return {}

                channel_name = info.get('title')
                entries = info.get('entries')

                with open ("channel.json", "w", encoding="utf-8") as f:
                    json.dump(info, f, indent=2, ensure_ascii=False)

                for entry in entries:
                    entry_name = entry.get('title')

                    # --- Normal Videos ---
                    if entry_name == f'{channel_name} - Videos':
                        video_entries = entry.get('entries')
                        for i, video_entry in enumerate(video_entries):
                            video_id = video_entry.get('id')
                            title = video_entry.get('title')
                            url = video_entry.get('url')
                            views = video_entry.get('view_count')
                            duration = video_entry.get('duration')

                            # Save JSON file for raw data
                            file_path = self.db.save_json_file(
                                self.db.video_dir, f"video_{video_id}", video_entry
                            )

                            # Insert into DB
                            self.db.insert("VIDEO", {
                                "channel_id": channel_id,
                                "title": title,
                                "desc": video_entry.get("description"),
                                "duration": duration,
                                "view_count": views,
                                "like_count": video_entry.get("like_count"),
                                "pub_date": video_entry.get("upload_date"),
                                "status": "active",
                                "created_at": datetime.now().isoformat(),
                                "file_path": str(file_path)
                            })

                            self.videos[i] = {
                                "title": title,
                                "url": url,
                                "views": views,
                                "duration": duration
                            }
                            self.video_url.append(url)

                    # --- Live Videos ---
                    elif entry_name == f'{channel_name} - Live':
                        live_entries = entry.get('entries')
                        for i, live_entry in enumerate(live_entries):
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

                    # --- Shorts ---
                    elif entry_name == f'{channel_name} - Shorts':
                        shorts_entries = entry.get('entries')
                        for i, shorts_entry in enumerate(shorts_entries):
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

                # Final structured dict (for immediate use)
                self.content = {
                    "live": self.live,
                    "shorts": self.shorts,
                    "videos": self.videos,
                    "video_url": self.video_url
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
