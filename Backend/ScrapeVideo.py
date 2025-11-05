import yt_dlp
import requests
import os
from PySide6.QtCore import QObject, Signal

from utils.AppState import app_state

def download_img(url, save_path):
    try:
        response = requests.get(url, timeout=15.0, stream=True)
        response.raise_for_status()
        with open(save_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"[ERROR] Failed to download {url}: {e}")
        import traceback
        traceback.print_exc()
        return False

class VideoWorker(QObject):
    progress_updated = Signal(str)
    finished = Signal()
    
    def __init__(self, channel_id, channel_url):
        super().__init__()
        self.db = app_state.db
        self.channel_id = channel_id
        self.channel_url = channel_url
        self.content = {}
        self.videos = {}
        self.live = {}
        self.shorts = {}
        self.video_url = []

    def fetch_video_urls(self):
        """
        Fetch video URLs and metadata for a YouTube channel.
        Downloads thumbnails.
        """
        try:
            self.progress_updated.emit("Initializing...")
            
            # yt_dlp options
            ydl_opts = {
                'extract_flat': True,
                'skip_download': True,
                'quiet': True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                self.progress_updated.emit("Fetching channel information...")
                info = ydl.extract_info(self.channel_url, download=False)

                if 'entries' not in info:
                    self.progress_updated.emit("No videos found!")
                    self.finished.emit()
                    return {}

                channel_name = info.get('title')
                entries = info.get('entries')

                # Count total videos first
                self.progress_updated.emit("Counting videos...")
                total_available_videos = 0
                for entry in entries:
                    entry_name = entry.get('title')
                    if any(x in entry_name for x in [f'{channel_name} - Videos', 
                                                    f'{channel_name} - Shorts', 
                                                    f'{channel_name} - Live']):
                        video_entries = entry.get('entries')
                        if video_entries:
                            total_available_videos += len(video_entries)

                self.progress_updated.emit(f"Found {total_available_videos} videos to process")

                # Process videos
                total_videos_scraped = 0
                for entry in entries:
                    entry_name = entry.get('title')

                    # Determine video type
                    if entry_name == f'{channel_name} - Videos':
                        video_type = 'video'
                    elif entry_name == f'{channel_name} - Shorts':
                        video_type = 'shorts'
                    elif entry_name == f'{channel_name} - Live':
                        video_type = 'live'
                    else:
                        continue

                    video_entries = entry.get('entries')
                    if not video_entries:
                        continue

                    total_content = 0
                    for i in video_entries:
                        total_content += 1

                    for i, video_entry in enumerate(video_entries):
                        video_id = video_entry.get('id')
                        title = video_entry.get('title')
                        url = video_entry.get('url')
                        views = video_entry.get('view_count')
                        duration = video_entry.get('duration')

                        self.progress_updated.emit(f"Processing: ( {i+1}/{total_content} ) videos\nVideo: {title[:50]}...")

                        # Download thumbnail
                        thumbnail_url = video_entry.get("thumbnails")[-1].get("url")
                        os.makedirs(f"{self.db.thumbnail_dir}/{self.channel_id}", exist_ok=True)
                        profile_save_path = rf"{self.db.thumbnail_dir}/{self.channel_id}/{video_id}.png"
                        download_img(thumbnail_url, profile_save_path)

                        # Insert into DB
                        self.db.insert("VIDEO", {
                            "video_id": video_id,
                            "channel_id": self.channel_id,
                            "video_type": video_type,
                            "video_url": url,
                            "title": title,
                            "desc": video_entry.get("description"),
                            "duration": duration,
                            "view_count": views,
                            "like_count": video_entry.get("like_count"),
                            "pub_date": video_entry.get("upload_date"),
                        })

                        total_videos_scraped += 1
                        if total_videos_scraped % 5 == 0:
                            self.progress_updated.emit(f"Progress: {total_videos_scraped}/{total_available_videos} videos processed")

            self.progress_updated.emit(f"Completed! Processed {total_videos_scraped} videos")
            self.finished.emit()
            return

        except Exception as e:
            import traceback
            traceback.print_exc()
            error_msg = f"Error while fetching video URLs: {e}"
            print(error_msg)
            self.progress_updated.emit(error_msg)
            self.finished.emit()
            return {}