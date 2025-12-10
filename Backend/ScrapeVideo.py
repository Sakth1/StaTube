import os
import scrapetube
import yt_dlp
from datetime import datetime, timedelta, timezone
import re
import asyncio
import aiohttp
from typing import List, Dict, Optional, Callable
from PySide6.QtCore import QObject, Signal, Slot, QMetaObject, Qt, Q_ARG

from Data.DatabaseManager import DatabaseManager
from utils.AppState import app_state
from utils.Logger import logger


def parse_duration(duration: str) -> int:
    """
    Converts a duration string from YouTube (e.g. "10:20" or "1:10:20") to an approximate number of seconds.
    Returns 0 if parsing fails.
    """
    try:
        minutes, seconds = map(int, duration.split(":"))
        return minutes * 60 + seconds
    
    except ValueError:
        try:
            hours, minutes, seconds = map(int, duration.split(":"))
            return hours * 3600 + minutes * 60 + seconds
        except Exception:
            return 0
    
    except Exception:
        return 0
    
def parse_time_since_published(text: str) -> int:
    """
    Converts '3 weeks ago' or '2 days ago' to an approximate Unix timestamp.

    Parameters:
        text (str): The text to parse.

    Returns:
        int: The parsed timestamp or the current timestamp if parsing fails.
    """
    now: datetime = datetime.now(timezone.utc)
    if not text:
        return int(now.timestamp())

    text = text.strip().lower()

    try:
        match = re.match(r"(\d+)\s+(\w+)", text)
        if not match:
            return int(now.timestamp())

        value: int = int(match.group(1))
        unit: str = match.group(2)

        if "minute" in unit:
            delta: timedelta = timedelta(minutes=value)
        elif "hour" in unit:
            delta: timedelta = timedelta(hours=value)
        elif "day" in unit:
            delta: timedelta = timedelta(days=value)
        elif "week" in unit:
            delta: timedelta = timedelta(weeks=value)
        elif "month" in unit:
            delta: timedelta = timedelta(days=value * 30)
        elif "year" in unit:
            delta: timedelta = timedelta(days=value * 365)
        else:
            delta: timedelta = timedelta(0)

        return int((now - delta).timestamp())

    except Exception:
        return int(now.timestamp())


async def download_img_async(url: str, save_path: str, session: aiohttp.ClientSession, semaphore: asyncio.Semaphore) -> bool:
    """
    Download thumbnail image asynchronously.

    Parameters:
    url (str): The URL of the image to download.
    save_path (str): The path where the image should be saved.
    session (aiohttp.ClientSession): The aiohttp session to use for the request.
    semaphore (asyncio.Semaphore): The semaphore to use for limiting concurrent requests.

    Returns:
    bool: True if the image was downloaded successfully, False otherwise.
    """
    async with semaphore:  # Use existing semaphore
        try:
            url = str(url)
            save_path = str(save_path)

            # Fix double https issue
            if url.startswith("https:https://"):
                url = url.replace("https:https://", "https://", 1)

            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as response:
                response.raise_for_status()

                with open(save_path, "wb") as f:
                    async for chunk in response.content.iter_chunked(8192):
                        f.write(chunk)

            return True

        except Exception:
            logger.error(f"Failed to download thumbnail: {url}")
            logger.exception("Thumbnail download error:")
            return False


async def fetch_shorts_metadata_async(video_id: str, session: aiohttp.ClientSession, semaphore: asyncio.Semaphore) -> dict:
    """
    Fetch complete metadata for a short video using yt-dlp asynchronously.

    Parameters:
    video_id (str): The YouTube video ID.
    session (aiohttp.ClientSession): The aiohttp session to use for the request.
    semaphore (asyncio.Semaphore): The semaphore to use for limiting concurrent requests.

    Returns:
    dict: A dictionary containing the fetched metadata.
    """
    async with semaphore:
        try:
            # Run yt-dlp in executor to avoid blocking
            loop = asyncio.get_event_loop()
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                'socket_timeout': 10,
                'no_check_certificate': True,
            }
            
            def extract_info():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    return ydl.extract_info(f"https://www.youtube.com/shorts/{video_id}", download=False)
            
            info = await loop.run_in_executor(None, extract_info)
            
            return {
                'video_id': str(video_id),
                'duration': int(info.get('duration', 0)),
                'upload_date': info.get('upload_date'),
                'description': str(info.get('description', '')),
                'view_count': int(info.get('view_count', 0)),
                'title': str(info.get('title', 'Untitled')),
            }
        except Exception as e:
            logger.error(f"Failed to fetch metadata for short video: {video_id}")
            logger.exception("Short metadata fetch error:")
            return {'video_id': str(video_id), 'error': True}


async def fetch_shorts_batch_async(
    video_ids: List[str], 
    progress_callback: Optional[Callable[[int, int], None]] = None, 
    max_concurrent: int = 100
) -> Dict[str, Dict]:
    """
    Fetch metadata for multiple shorts in parallel using asyncio.

    Parameters:
    video_ids (List[str]): List of YouTube video IDs to fetch metadata.
    progress_callback (Optional[Callable[[int, int], None]]): Callback to update progress in main thread.
    max_concurrent (int): Maximum number of concurrent requests.

    Returns:
    Dict[str, Dict]: Dictionary containing the fetched metadata, with video_id as key.
    """
    results = {}
    total = len(video_ids)
    completed = 0
    
    # Semaphore to limit concurrent requests
    semaphore = asyncio.Semaphore(max_concurrent)
    
    # Create aiohttp session
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        
        async def fetch_with_progress(video_id: str):
            nonlocal completed
            result = await fetch_shorts_metadata_async(str(video_id), session, semaphore)
            completed += 1
            
            if progress_callback:
                # Execute callback in main thread using Qt's signal mechanism
                QMetaObject.invokeMethod(
                    progress_callback,
                    "update_from_async",
                    Qt.QueuedConnection,
                    Q_ARG(int, completed),
                    Q_ARG(int, total)
                )
            
            return result
        
        # Create all tasks
        tasks = [fetch_with_progress(str(vid)) for vid in video_ids]
        
        # Execute all tasks concurrently
        all_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for result in all_results:
            if isinstance(result, dict) and 'video_id' in result:
                results[result['video_id']] = result
    
    return results


def run_async_shorts_fetch(video_ids: list, progress_callback=None, max_concurrent: int = 100) -> dict:
    """
    Wrapper to run async shorts fetching in a new event loop.
    """
    try:
        # Try to get existing loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is running, create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        # No loop exists, create one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        return loop.run_until_complete(
            fetch_shorts_batch_async(video_ids, progress_callback, max_concurrent)
        )
    finally:
        # Don't close the loop if it was running before
        pass


class VideoWorker(QObject):
    progress_updated = Signal(str)
    progress_percentage = Signal(int)
    finished = Signal()

    def __init__(self, channel_id: str, channel_url: str, scrape_shorts: bool):
        super().__init__()
        self.db: DatabaseManager = app_state.db
        self.channel_id = channel_id
        self.channel_url = channel_url
        self.scrape_shorts = scrape_shorts

        self.types = {
            "videos": "videos",
            "shorts": "shorts",
            "live": "streams"
        }

        if not self.scrape_shorts:
            self.types.pop("shorts", None)

        self.current_type_counter = 0

    @Slot()
    def run(self):
        """
        SAFE ENTRY POINT FOR QTHREAD
        """
        try:
            asyncio.run(self._fetch_video_urls_async())
        except Exception:
            logger.exception("VideoWorker crashed:")
        finally:
            # ✅ GUARANTEED EXIT PATH
            self.finished.emit()

    @Slot(int, int)
    def update_from_async(self, completed: int, total: int):
        msg = f"[Shorts] Fetching metadata: {completed}/{total}"
        self.progress_updated.emit(msg)
        pct = int((self.current_type_counter - 1) * 33 + (completed / total) * 20)
        self.progress_percentage.emit(min(pct, 95))

    # ✅ INTERRUPTION SAFE CHECK
    def _should_stop(self):
        from PySide6.QtCore import QThread
        return QThread.currentThread().isInterruptionRequested()

    async def _fetch_video_urls_async(self):
        try:
            self.progress_updated.emit("Starting scrapetube scraping...")
            self.progress_percentage.emit(0)

            total_processed = 0

            channel_thumb_dir = os.path.join(self.db.thumbnail_dir, str(self.channel_id))
            os.makedirs(channel_thumb_dir, exist_ok=True)

            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                thumbnail_semaphore = asyncio.Semaphore(20)

                for i, (vtype, ctype) in enumerate(self.types.items(), start=1):

                    # ✅ USER CANCEL SUPPORT
                    if self._should_stop():
                        self.progress_updated.emit("Scraping cancelled by user")
                        return

                    self.current_type_counter = i
                    self.progress_updated.emit(f"Fetching {vtype.capitalize()}...")
                    self.progress_percentage.emit(int((i - 1) * 33))

                    videos = list(scrapetube.get_channel(
                        channel_url=self.channel_url,
                        content_type=ctype
                    ))

                    if not videos:
                        continue

                    self.progress_updated.emit(f"Fetched {len(videos)} {vtype}")

                    # === SHORTS METADATA ===
                    shorts_metadata = {}
                    if vtype == "shorts":
                        video_ids = [v.get("videoId") for v in videos if v.get("videoId")]
                        shorts_metadata = await fetch_shorts_batch_async(
                            video_ids,
                            progress_callback=self,
                            max_concurrent=30
                        )

                    thumbnail_tasks = []
                    videos_to_insert = []

                    for idx, video in enumerate(videos):

                        if self._should_stop():
                            self.progress_updated.emit("Scraping cancelled by user")
                            return

                        video_id = video.get("videoId")
                        if not video_id:
                            continue

                        title = (
                            video.get("title", {})
                            .get("runs", [{}])[0]
                            .get("text", "Untitled")
                        )

                        thumbnails = video.get("thumbnail", {}).get("thumbnails", [])
                        thumbnail_url = thumbnails[-1].get("url") if thumbnails else None

                        thumb_path = os.path.join(channel_thumb_dir, f"{video_id}.png")

                        if thumbnail_url and not os.path.exists(thumb_path):
                            thumbnail_tasks.append(
                                download_img_async(
                                    thumbnail_url,
                                    thumb_path,
                                    session,
                                    thumbnail_semaphore
                                )
                            )

                        videos_to_insert.append({
                            "video_id": video_id,
                            "channel_id": self.channel_id,
                            "video_type": vtype,
                            "video_url": f"https://www.youtube.com/watch?v={video_id}",
                            "title": title,
                            "desc": "",
                            "duration": None,
                            "duration_in_seconds": 0,
                            "thumbnail_path": thumb_path,
                            "view_count": 0,
                            "time_since_published": None,
                            "upload_timestamp": int(datetime.now(timezone.utc).timestamp())
                        })

                        if (idx + 1) % 10 == 0:
                            self.progress_updated.emit(
                                f"[{vtype.capitalize()}] {idx+1}/{len(videos)}"
                            )

                    # === DOWNLOAD THUMBNAILS ===
                    if thumbnail_tasks:
                        self.progress_updated.emit(f"[{vtype.capitalize()}] Downloading thumbnails...")
                        await asyncio.gather(*thumbnail_tasks, return_exceptions=True)

                    # === DATABASE SAVE ===
                    for video_data in videos_to_insert:
                        self.db.insert("VIDEO", video_data)

                    total_processed += len(videos_to_insert)

                    self.progress_percentage.emit(min(i * 33, 95))

            self.progress_updated.emit(f"Completed scraping! Total {total_processed} videos saved.")
            self.progress_percentage.emit(100)

        except Exception:
            logger.exception("Async scrape failure")

