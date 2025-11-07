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
    progress_percentage = Signal(int)
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
        Downloads thumbnails and writes data to DB.
        Only after successful insert and image save, update UI.
        """
        try:
            self.progress_updated.emit("Initializing...")
            self.progress_percentage.emit(0)
            
            ydl_opts = {
                'extract_flat': True,
                'skip_download': True,
                'quiet': True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                self.progress_updated.emit("Fetching channel information...")
                self.progress_percentage.emit(5)
                info = ydl.extract_info(self.channel_url, download=False)

                if 'entries' not in info:
                    self.progress_updated.emit("No videos found!")
                    self.progress_percentage.emit(100)
                    self.finished.emit()
                    return {}

                channel_name = info.get('title')
                entries = info.get('entries')

                # Count total videos
                self.progress_updated.emit("Counting videos...")
                self.progress_percentage.emit(10)
                total_available_videos = 0
                for entry in entries:
                    entry_name = entry.get('title')
                    if any(x in entry_name for x in [f'{channel_name} - Videos', 
                                                    f'{channel_name} - Shorts', 
                                                    f'{channel_name} - Live']):
                        video_entries = entry.get('entries')
                        if video_entries:
                            total_available_videos += len(video_entries)

                total_videos_scraped = 0
                self.progress_updated.emit(f"Found {total_available_videos} videos to process")
                self.progress_percentage.emit(15)

                # Process videos
                for entry in entries:
                    entry_name = entry.get('title')
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

                    for i, video_entry in enumerate(video_entries):
                        video_id = video_entry.get('id')
                        title = video_entry.get('title')
                        url = video_entry.get('url')
                        views = video_entry.get('view_count')
                        duration = video_entry.get('duration')
                        thumbnail_url = video_entry.get("thumbnails")[-1].get("url")

                        # Download thumbnail
                        os.makedirs(f"{self.db.thumbnail_dir}/{self.channel_id}", exist_ok=True)
                        save_path = rf"{self.db.thumbnail_dir}/{self.channel_id}/{video_id}.png"
                        downloaded = download_img(thumbnail_url, save_path)

                        # Only insert and update progress if download successful
                        if downloaded:
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
                            # Now update the UI (only after success)
                            self.progress_updated.emit(
                                f"✔ Saved {video_type.title()}: {title[:50]}..."
                            )

                            if total_available_videos > 0:
                                progress_percent = 15 + int((total_videos_scraped / total_available_videos) * 80)
                                self.progress_percentage.emit(progress_percent)

                            if total_videos_scraped % 5 == 0:
                                self.progress_updated.emit(
                                    f"Progress: {total_videos_scraped}/{total_available_videos} videos saved"
                                )
                        else:
                            self.progress_updated.emit(f"⚠ Failed to download thumbnail for {title[:50]}...")

            self.progress_updated.emit(f"Completed! {total_videos_scraped}/{total_available_videos} videos saved successfully.")
            self.progress_percentage.emit(100)
            self.finished.emit()
            return

        except Exception as e:
            import traceback
            traceback.print_exc()
            error_msg = f"Error while fetching video URLs: {e}"
            print(error_msg)
            self.progress_updated.emit(error_msg)
            self.progress_percentage.emit(0)
            self.finished.emit()
            return {}
