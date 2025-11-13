import os
import scrapetube
import requests
import yt_dlp
from datetime import datetime, timedelta, timezone
import re
import asyncio
import aiohttp

from PySide6.QtCore import QObject, Signal
from Data.DatabaseManager import DatabaseManager
from utils.AppState import app_state


def parse_duration(duration: str) -> int:
    try:
        minutes, seconds = duration.split(":")
        return int(minutes) * 60 + int(seconds)
    
    except ValueError:
        try:
            hours, minutes, seconds = duration.split(":")
            return int(hours) * 3600 + int(minutes) * 60 + int(seconds)
        except Exception:
            return 0
    
    except Exception:
        return 0
    
def parse_time_since_published(text: str) -> int:
    """
    Converts '3 weeks ago' or '2 days ago' to an approximate Unix timestamp.
    Returns current timestamp if parsing fails.
    """
    now = datetime.now(timezone.utc)
    if not text:
        return int(now.timestamp())

    text = text.lower().strip()

    try:
        match = re.match(r"(\d+)\s+(\w+)", text)
        if not match:
            return int(now.timestamp())

        value, unit = int(match.group(1)), match.group(2)

        if "minute" in unit:
            delta = timedelta(minutes=value)
        elif "hour" in unit:
            delta = timedelta(hours=value)
        elif "day" in unit:
            delta = timedelta(days=value)
        elif "week" in unit:
            delta = timedelta(weeks=value)
        elif "month" in unit:
            delta = timedelta(days=value * 30)
        elif "year" in unit:
            delta = timedelta(days=value * 365)
        else:
            delta = timedelta(0)

        return int((now - delta).timestamp())

    except Exception:
        return int(now.timestamp())


async def download_img_async(url: str, save_path: str, session: aiohttp.ClientSession, semaphore: asyncio.Semaphore) -> bool:
    """Download thumbnail image asynchronously."""
    async with semaphore:
        try:
            if url.startswith("https:https://"):
                url = url.replace("https:https://", "https://", 1)
            
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as response:
                response.raise_for_status()
                with open(save_path, "wb") as f:
                    async for chunk in response.content.iter_chunked(8192):
                        f.write(chunk)
                return True
        except Exception as e:
            print(f"[ERROR] Failed to download {url}: {e}")
            return False


async def fetch_shorts_metadata_async(video_id: str, session: aiohttp.ClientSession, semaphore: asyncio.Semaphore) -> dict:
    """
    Fetch complete metadata for a short video using yt-dlp asynchronously.
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
                'video_id': video_id,
                'duration': info.get('duration', 0),
                'upload_date': info.get('upload_date'),
                'description': info.get('description', ''),
                'view_count': info.get('view_count', 0),
                'title': info.get('title', 'Untitled'),
            }
        except Exception as e:
            print(f"[ERROR] Failed to fetch metadata for {video_id}: {e}")
            return {'video_id': video_id, 'error': True}


async def fetch_shorts_batch_async(video_ids: list, progress_callback=None, max_concurrent: int = 100) -> dict:
    """
    Fetch metadata for multiple shorts in parallel using asyncio.
    """
    results = {}
    total = len(video_ids)
    completed = 0
    
    # Semaphore to limit concurrent requests
    semaphore = asyncio.Semaphore(max_concurrent)
    
    # Create aiohttp session
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        
        async def fetch_with_progress(video_id):
            nonlocal completed
            result = await fetch_shorts_metadata_async(video_id, session, semaphore)
            completed += 1
            
            if progress_callback:
                # Schedule callback in main thread
                progress_callback(completed, total)
            
            return result
        
        # Create all tasks
        tasks = [fetch_with_progress(vid) for vid in video_ids]
        
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

    def __init__(self, channel_id, channel_url):
        super().__init__()
        self.db: DatabaseManager = app_state.db
        self.channel_id = channel_id
        self.channel_url = channel_url
        self.types = {
            "videos": "videos",
            "shorts": "shorts",
            "live": "streams"
        }

    def fetch_video_urls(self):
        """Wrapper to run async video fetching."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._fetch_video_urls_async())
        except Exception as e:
            import traceback
            traceback.print_exc()
            error_msg = f"Error while fetching video URLs: {e}"
            print(error_msg)
            self.progress_updated.emit(error_msg)
            self.progress_percentage.emit(0)
            self.finished.emit()
        finally:
            try:
                loop.close()
            except Exception:
                pass

    async def _fetch_video_urls_async(self):
        """
        Fetch and process videos by type (videos, shorts, live) using scrapetube.
        Downloads thumbnails asynchronously and updates DB in batches.
        """
        try:
            self.progress_updated.emit("Starting scrapetube scraping...")
            self.progress_percentage.emit(0)

            all_videos = []
            total_processed = 0
            type_counter = 0
            channel_thumb_dir = os.path.join(self.db.thumbnail_dir, str(self.channel_id))
            os.makedirs(channel_thumb_dir, exist_ok=True)

            # Create aiohttp session for all downloads
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                thumbnail_semaphore = asyncio.Semaphore(20)  # Limit concurrent thumbnail downloads

                # === Process each content type ===
                for vtype, ctype in self.types.items():
                    type_counter += 1
                    self.progress_updated.emit(f"Fetching {vtype.capitalize()}...")
                    self.progress_percentage.emit(int((type_counter - 1) * 33))

                    # scrapetube.get_channel(channel_url=..., content_type="shorts"/"streams"/None)
                    videos = list(scrapetube.get_channel(channel_url=self.channel_url, content_type=ctype))
                    if not videos:
                        self.progress_updated.emit(f"No {vtype} found.")
                        continue    

                    self.progress_updated.emit(f"Fetched {len(videos)} {vtype}. Parsing data...")
                    all_videos.extend(videos)

                    # === For shorts, fetch all metadata in parallel first ===
                    if vtype == "shorts":
                        video_ids = [v.get("videoId") for v in videos if v.get("videoId")]
                        self.progress_updated.emit(f"[Shorts] Fetching metadata for {len(video_ids)} shorts (async mode)...")
                        
                        # Progress callback for shorts fetching
                        def shorts_progress(completed, total):
                            progress_msg = f"[Shorts] Fetching metadata: {completed}/{total} shorts"
                            self.progress_updated.emit(progress_msg)
                            type_progress = int((type_counter - 1) * 33 + (completed / total) * 20)
                            self.progress_percentage.emit(min(type_progress, 95))
                        
                        shorts_metadata = await fetch_shorts_batch_async(
                            video_ids, 
                            progress_callback=shorts_progress, 
                            max_concurrent=30
                        )
                        self.progress_updated.emit(f"[Shorts] Metadata fetched! Now processing {len(videos)} shorts...")
                    else:
                        shorts_metadata = {}

                    # === Collect all thumbnail download tasks and video data ===
                    thumbnail_tasks = []
                    videos_to_insert = []

                    for idx, video in enumerate(videos):
                        video_id = video.get("videoId")
                        if not video_id:
                            continue

                        # For shorts, use pre-fetched metadata
                        if vtype == "shorts":
                            shorts_meta = shorts_metadata.get(video_id)
                            
                            if shorts_meta and not shorts_meta.get('error'):
                                title = shorts_meta['title']
                                description = shorts_meta['description']
                                duration_in_seconds = shorts_meta['duration']
                                duration = f"{duration_in_seconds // 60}:{duration_in_seconds % 60:02d}" if duration_in_seconds else None
                                views = shorts_meta['view_count']
                                
                                # Convert upload_date (YYYYMMDD) to timestamp
                                if shorts_meta['upload_date']:
                                    try:
                                        upload_date = datetime.strptime(shorts_meta['upload_date'], '%Y%m%d')
                                        upload_timestamp = int(upload_date.timestamp())
                                        
                                        # Calculate "time since published" text
                                        days_ago = (datetime.now(timezone.utc) - upload_date.replace(tzinfo=timezone.utc)).days
                                        if days_ago == 0:
                                            time_since_published = "Today"
                                        elif days_ago == 1:
                                            time_since_published = "1 day ago"
                                        elif days_ago < 7:
                                            time_since_published = f"{days_ago} days ago"
                                        elif days_ago < 30:
                                            weeks = days_ago // 7
                                            time_since_published = f"{weeks} week{'s' if weeks > 1 else ''} ago"
                                        elif days_ago < 365:
                                            months = days_ago // 30
                                            time_since_published = f"{months} month{'s' if months > 1 else ''} ago"
                                        else:
                                            years = days_ago // 365
                                            time_since_published = f"{years} year{'s' if years > 1 else ''} ago"
                                    except Exception:
                                        upload_timestamp = int(datetime.now(timezone.utc).timestamp())
                                        time_since_published = None
                                else:
                                    upload_timestamp = int(datetime.now(timezone.utc).timestamp())
                                    time_since_published = None
                            else:
                                # Fallback to scrapetube data if yt-dlp fails
                                title = (
                                    video.get("title", {})
                                    .get("runs", [{}])[0]
                                    .get("text", "Untitled")
                                )
                                description = ""
                                duration = None
                                duration_in_seconds = 0
                                views = 0
                                upload_timestamp = int(datetime.now(timezone.utc).timestamp())
                                time_since_published = None
                        else:
                            # Original parsing for videos and live streams
                            title = (
                                video.get("title", {})
                                .get("runs", [{}])[0]
                                .get("text", "Untitled")
                            )

                            description = (
                                video.get("descriptionSnippet", {})
                                .get("runs", [{}])[0]
                                .get("text", "")
                            )

                            duration = (
                                video.get("lengthText", {}).get("simpleText")
                                or video.get("lengthText", {}).get("runs", [{}])[0].get("text")
                                or None
                            )

                            duration_in_seconds = parse_duration(duration) if duration else 0

                            time_since_published = (
                                video.get("publishedTimeText", {}).get("simpleText")
                                or video.get("publishedTimeText", {}).get("runs", [{}])[0].get("text")
                                or None
                            )

                            upload_timestamp = parse_time_since_published(time_since_published)

                            # Parse view count text
                            view_text = (
                                video.get("viewCountText", {}).get("simpleText")
                                or video.get("viewCountText", {}).get("runs", [{}])[0].get("text", "")
                            )
                            views = 0
                            if view_text:
                                try:
                                    views = int(
                                        view_text.replace("views", "")
                                        .replace(",", "")
                                        .replace(".", "")
                                        .strip()
                                    )
                                except Exception:
                                    pass

                        thumbnails = video.get("thumbnail", {}).get("thumbnails", [])
                        thumbnail_url = thumbnails[-1].get("url") if thumbnails else None

                        video_url = f"https://www.youtube.com/watch?v={video_id}"
                        thumb_path = os.path.join(channel_thumb_dir, f"{video_id}.png")

                        # Collect thumbnail download task if needed
                        if thumbnail_url and not os.path.exists(thumb_path):
                            thumbnail_tasks.append(
                                download_img_async(thumbnail_url, thumb_path, session, thumbnail_semaphore)
                            )

                        # Collect video data for batch insert
                        videos_to_insert.append({
                            "video_id": video_id,
                            "channel_id": self.channel_id,
                            "video_type": vtype,
                            "video_url": video_url,
                            "title": title,
                            "desc": description,
                            "duration": duration,
                            "duration_in_seconds": duration_in_seconds,
                            "thumbnail_path": thumb_path,
                            "view_count": views,
                            "time_since_published": time_since_published,
                            "upload_timestamp": upload_timestamp
                        })

                        # Update progress periodically
                        if (idx + 1) % 10 == 0 or idx == len(videos) - 1:
                            self.progress_updated.emit(
                                f"[{vtype.capitalize()}] Processing: {idx+1}/{len(videos)}"
                            )

                    # === Wait for all thumbnails to download ===
                    if thumbnail_tasks:
                        self.progress_updated.emit(f"[{vtype.capitalize()}] Downloading {len(thumbnail_tasks)} thumbnails...")
                        await asyncio.gather(*thumbnail_tasks, return_exceptions=True)
                        self.progress_updated.emit(f"[{vtype.capitalize()}] ✓ All thumbnails downloaded")

                    # === Batch insert to database ===
                    self.progress_updated.emit(f"[{vtype.capitalize()}] Saving {len(videos_to_insert)} videos to database...")
                    
                    for video_data in videos_to_insert:
                        existing_videos = self.db.fetch(
                            table="VIDEO", where="video_id = ?", params=(video_data["video_id"],)
                        )
                        video_exists = len(existing_videos) > 0
                        self.db.insert("VIDEO", video_data)

                    total_processed += len(videos_to_insert)
                    self.progress_updated.emit(f"[{vtype.capitalize()}] ✓ Saved {len(videos_to_insert)} videos")
                    
                    overall_progress = int(type_counter * 33)
                    self.progress_percentage.emit(min(overall_progress, 95))

            self.progress_updated.emit(f"✅ Completed scraping! Total {total_processed} videos saved.")
            self.progress_percentage.emit(100)
            self.finished.emit()

        except Exception as e:
            import traceback
            traceback.print_exc()
            error_msg = f"Error while fetching video URLs: {e}"
            print(error_msg)
            self.progress_updated.emit(error_msg)
            self.progress_percentage.emit(0)
            self.finished.emit()