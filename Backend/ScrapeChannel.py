import scrapetube
import requests
import threading
import time
from typing import Dict, List, Callable, Optional

from utils.AppState import app_state

def download_img(url, save_path):
    try:
        # Fix malformed URLs
        if url.startswith("https:https://"):
            url = url.replace("https:https://", "https://", 1)

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

class Search:
    def __init__(self):
        self.db = app_state.db
        self.channels = {}
        self.completed_downloads = 0
        self.total_downloads = 0
        self.download_lock = threading.Lock()
        self.all_threads_complete = threading.Event()

    def update_db(self, channel_id, title, sub_count, desc, profile_url, progress_callback=None):
        try:
            profile_save_path = rf"{self.db.profile_pic_dir}/{channel_id}.png"
            success = download_img(profile_url, profile_save_path)
            
            if progress_callback and success:
                progress_callback(f"Downloaded profile for: {title}")
        except Exception as e:
            print(f"Failed to save profile picture: {e}")
            import traceback
            traceback.print_exc()
            success = False

        if channel_id:
            url = f"https://www.youtube.com/channel/{channel_id}"
            
            # Use lock to safely update channels dictionary
            with self.download_lock:
                self.channels[channel_id] = {"title": title, "url": url, "sub_count": sub_count}

            # Check if channel already exists
            existing_channels = self.db.fetch(table="CHANNEL", where="channel_id = ?", params=(channel_id,))
            
            if not existing_channels:
                # Channel doesn't exist, insert new one
                self.db.insert(
                    "CHANNEL",
                    {
                        "channel_id": channel_id,
                        "name": title,
                        "url": url,
                        "sub_count": str(sub_count),
                        "desc": desc,
                        "profile_pic": profile_save_path,
                    },
                )
                print(f"Added new channel: {title}")

        # Update completion counter
        with self.download_lock:
            self.completed_downloads += 1
            if progress_callback:
                progress = (self.completed_downloads / self.total_downloads) * 100
                progress_callback(progress, f"Processed {self.completed_downloads}/{self.total_downloads} channels")
            
            # Check if all downloads are complete
            if self.completed_downloads >= self.total_downloads:
                self.all_threads_complete.set()

    def search_channel(self, name: str = None, limit: int = 6, stop_event=None, 
                      final=False, progress_callback: Optional[Callable] = None):
        if not name:
            return {"None": {"title": None, "url": None}}

        self.channels = {}
        self.completed_downloads = 0
        self.total_downloads = 0
        self.all_threads_complete.clear()
        
        search_results = scrapetube.get_search(name, results_type="channel", limit=limit)
        
        # Collect all channel data first
        channel_data = []
        for ch in search_results:
            # Check if we should stop
            if stop_event and stop_event.is_set():
                print("Search interrupted")
                return self.channels
            
            title = ch.get("title", {}).get("simpleText")
            sub_count = ch.get("videoCountText", {}).get("accessibility", {}).get("accessibilityData", {}).get("label")
            desc = ch.get("descriptionSnippet", {}).get("runs")[0].get("text") if ch.get("descriptionSnippet") else None
            channel_id = ch.get("channelId")
            profile_url = "https:" + ch.get("thumbnail", {}).get("thumbnails")[0].get("url")

            if channel_id:
                url = f"https://www.youtube.com/channel/{channel_id}"
                # Store temporarily
                self.channels[channel_id] = {"title": title, "url": url, "sub_count": sub_count}
                channel_data.append((channel_id, title, sub_count, desc, profile_url))

        # Start download threads for all channels
        self.total_downloads = len(channel_data)
        threads = []
        
        if progress_callback and final:
            progress_callback(0, f"Starting download of {self.total_downloads} channel profiles...")
        
        for data in channel_data:
            thread = threading.Thread(
                target=self.update_db, 
                args=(*data, progress_callback), 
                daemon=True
            )
            thread.start()
            threads.append(thread)

        # Wait for all downloads to complete if this is a final search
        if final and self.total_downloads > 0:
            # Wait with timeout to prevent hanging
            self.all_threads_complete.wait(timeout=120)  # 2 minute timeout
            
            if progress_callback:
                progress_callback(100, "All downloads completed!")

        return self.channels