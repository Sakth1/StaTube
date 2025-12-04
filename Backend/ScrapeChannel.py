import scrapetube
import requests
import threading
import os
from typing import Callable, Optional

from utils.AppState import app_state
from utils.Logger import logger

def download_img(url: str, save_path: str) -> bool:
    """
    Downloads an image from a given URL and saves it to the given save path.

    Args:
        url (str): URL of the image to download
        save_path (str): Path where the image should be saved

    Returns:
        bool: True if the image was downloaded and saved successfully, False otherwise
    """
    try:
        # Fix malformed URLs
        if url.startswith("https:https://"):
            url = url.replace("https:https://", "https://", 1)

        response = requests.get(str(url), timeout=15.0, stream=True)
        response.raise_for_status()
        with open(str(save_path), "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        logger.error(f"Failed to download image: {url}")
        logger.exception("Download image error:")
        return False

class Search:
    """
    Class to handle searching for YouTube channels.
    
    This class is responsible for searching and downloading profile pictures of YouTube channels.
    """
    def __init__(self):
        """
        Initializes a new Search object.
        """
        self.db = app_state.db
        self.channels = {}
        self.completed_downloads = 0
        self.total_downloads = 0
        self.download_lock = threading.Lock()
        self.all_threads_complete = threading.Event()

    def update_db(self, channel_id: str, title: str, sub_count: str, desc: str, profile_url: str, 
                progress_callback: Optional[Callable] = None):
        """
        Updates the database with the given channel information.
        
        Args:
            channel_id (str): ID of the channel to update
            title (str): Title of the channel
            sub_count (str): Number of subscribers of the channel
            desc (str): Description of the channel
            profile_url (str): URL of the channel profile picture
            progress_callback (Optional[Callable]): A callback function to report progress
        
        Returns:
            bool: True if the channel was updated successfully, False otherwise
        """
        try:
            profile_save_path = os.path.join(self.db.profile_pic_dir, f"{channel_id}.png")
            success = download_img(profile_url, profile_save_path)
            
            if progress_callback and success:
                progress_callback(f"Downloaded profile for: {title}")
        except Exception as e:
            logger.error(f"Failed to save profile picture for {channel_id}: {e}")
            logger.exception("Error saving profile picture:")
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
                logger.info(f"Added new channel: {title}")

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
        """
        Searches for YouTube channels with the given name and limit.
        
        Args:
            name (str): Name of the channel to search for
            limit (int): Number of results to fetch
            stop_event (Optional[threading.Event]): An event to stop the search
            final (bool): Whether this is the final search
            progress_callback (Optional[Callable]): A callback function to report progress
        
        Returns:
            dict: A dictionary containing the search results. The keys are the channel IDs and the values are dictionaries containing the channel title, URL, number of subscribers, description, and profile picture URL.
        """
        if not name:
            return {"None": {"title": None, "url": None}}

        logger.debug(f"Searching channels: name={name}, limit={limit}, final={final}")
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
                logger.warning("Search thread interrupted by stop_event")
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

        logger.debug(f"Search completed. Found {len(self.channels)} channels.")

        return self.channels
