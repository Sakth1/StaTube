# video_worker.py
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


def parse_duration(duration: Optional[str]) -> int:
    """
    Converts a duration string from YouTube (e.g. "10:20" or "1:10:20") to seconds.
    Returns 0 if parsing fails or duration is None.
    """
    if not duration:
        return 0

    parts = duration.split(":")
    try:
        parts = [int(p) for p in parts]
    except Exception:
        return 0

    if len(parts) == 2:
        minutes, seconds = parts
        return minutes * 60 + seconds
    elif len(parts) == 3:
        hours, minutes, seconds = parts
        return hours * 3600 + minutes * 60 + seconds
    else:
        # fallback: try single number as seconds
        try:
            return int(parts[0])
        except Exception:
            return 0


def parse_time_since_published(text: Optional[str]) -> int:
    """
    Converts '3 weeks ago' or '2 days ago' to an approximate Unix timestamp.
    If text is None or unparsable, returns current timestamp.
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
    """
    async with semaphore:
        try:
            url = str(url)
            save_path = str(save_path)

            # Fix double https issue
            if url.startswith("https:https://"):
                url = url.replace("https:https://", "https://", 1)

            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as response:
                response.raise_for_status()
                # Ensure parent dir exists
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
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
    Uses run_in_executor so it doesn't block the event loop.
    """
    async with semaphore:
        try:
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
                    # Use the shorts URL to get short-specific extractor behavior
                    return ydl.extract_info(f"https://www.youtube.com/shorts/{video_id}", download=False)

            info = await loop.run_in_executor(None, extract_info)

            return {
                'video_id': str(video_id),
                'duration': int(info.get('duration', 0)) if info.get('duration') is not None else 0,
                'upload_date': info.get('upload_date'),  # YYYYMMDD or None
                'description': str(info.get('description', '') or ''),
                'view_count': int(info.get('view_count', 0) or 0),
                'title': str(info.get('title', '') or 'Untitled'),
            }
        except Exception:
            logger.error(f"Failed to fetch metadata for short video: {video_id}")
            logger.exception("Short metadata fetch error:")
            return {'video_id': str(video_id), 'error': True}


async def fetch_shorts_batch_async(
    video_ids: List[str],
    progress_callback: Optional[Callable[[int, int], None]] = None,
    max_concurrent: int = 100
) -> Dict[str, Dict]:
    """
    Fetch metadata for multiple shorts concurrently.
    """
    results: Dict[str, Dict] = {}
    total = len(video_ids)
    completed = 0

    semaphore = asyncio.Semaphore(max_concurrent)
    timeout = aiohttp.ClientTimeout(total=30)

    async with aiohttp.ClientSession(timeout=timeout) as session:

        async def fetch_with_progress(video_id: str):
            nonlocal completed
            result = await fetch_shorts_metadata_async(str(video_id), session, semaphore)
            completed += 1

            if progress_callback:
                try:
                    QMetaObject.invokeMethod(
                        progress_callback,
                        "update_from_async",
                        Qt.QueuedConnection,
                        Q_ARG(int, completed),
                        Q_ARG(int, total)
                    )
                except Exception:
                    # fallback: call directly (shouldn't happen in Qt main thread)
                    try:
                        progress_callback.update_from_async(completed, total)
                    except Exception:
                        pass

            return result

        tasks = [fetch_with_progress(vid) for vid in video_ids]
        all_results = await asyncio.gather(*tasks, return_exceptions=True)

        for r in all_results:
            if isinstance(r, dict) and 'video_id' in r:
                results[r['video_id']] = r

    return results


def run_async_shorts_fetch(video_ids: list, progress_callback=None, max_concurrent: int = 100) -> dict:
    """
    Helper to run the fetch_shorts_batch_async from synchronous context if needed.
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    try:
        return loop.run_until_complete(
            fetch_shorts_batch_async(video_ids, progress_callback, max_concurrent)
        )
    finally:
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
        self.scrape_shorts = bool(scrape_shorts)

        # types that scrapetube accepts for content_type parameter
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
        Entry point callable by a QThread. Uses asyncio.run for the coroutine root.
        Guarantees finished signal in finally block of _fetch_video_urls_async.
        """
        try:
            asyncio.run(self._fetch_video_urls_async())
        except Exception:
            logger.exception("VideoWorker crashed in run():")
        finally:
            # ensure finished if not already emitted
            try:
                self.finished.emit()
            except Exception:
                pass

    @Slot(int, int)
    def update_from_async(self, completed: int, total: int):
        """
        Slot used by the shorts metadata fetcher to push progress back to GUI.
        """
        msg = f"[Shorts] Fetching metadata: {completed}/{total}"
        self.progress_updated.emit(msg)
        try:
            pct = int((self.current_type_counter - 1) * 33 + (completed / total) * 20)
        except Exception:
            pct = 0
        self.progress_percentage.emit(min(pct, 95))

    def _should_stop(self):
        # This uses QThread interruption mechanism to check for cancellation.
        from PySide6.QtCore import QThread
        try:
            return QThread.currentThread().isInterruptionRequested()
        except Exception:
            return False

    async def _fetch_video_urls_async(self):
        """
        Main coroutine that scrapes channel pages via scrapetube, optionally
        enriches shorts via yt-dlp, downloads thumbnails, and inserts into DB.
        """
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
                    # cancellation check
                    if self._should_stop():
                        self.progress_updated.emit("Scraping cancelled by user")
                        return

                    self.current_type_counter = i
                    self.progress_updated.emit(f"Fetching {vtype.capitalize()}...")
                    self.progress_percentage.emit(int((i - 1) * 33))

                    # scrapetube yields video dicts for the channel and content type
                    try:
                        videos = list(scrapetube.get_channel(channel_url=self.channel_url, content_type=ctype))
                    except Exception:
                        logger.exception("scrapetube.get_channel failed:")
                        videos = []

                    if not videos:
                        self.progress_updated.emit(f"No {vtype} found.")
                        continue

                    self.progress_updated.emit(f"Fetched {len(videos)} {vtype}")

                    # If shorts, prefetch extended metadata via yt-dlp (more reliable)
                    shorts_metadata = {}
                    if vtype == "shorts":
                        video_ids = [v.get("videoId") for v in videos if v.get("videoId")]
                        if video_ids:
                            self.progress_updated.emit(f"[Shorts] Fetching metadata for {len(video_ids)} shorts (async)...")
                            shorts_metadata = await fetch_shorts_batch_async(video_ids, progress_callback=self, max_concurrent=30)
                            self.progress_updated.emit(f"[Shorts] Metadata fetched ({len(shorts_metadata)}).")

                    thumbnail_tasks = []
                    videos_to_insert = []

                    for idx, video in enumerate(videos):
                        if self._should_stop():
                            self.progress_updated.emit("Scraping cancelled by user")
                            return

                        video_id = video.get("videoId")
                        if not video_id:
                            continue

                        # Default fields
                        title = (
                            video.get("title", {})
                            .get("runs", [{}])[0]
                            .get("text", "Untitled")
                        )

                        description = ""
                        duration_text = None
                        duration_in_seconds = 0
                        time_since_published = None
                        upload_timestamp = int(datetime.now(timezone.utc).timestamp())
                        views = 0

                        # Thumbnail from scrapetube if available
                        thumbnails = video.get("thumbnail", {}).get("thumbnails", [])
                        thumbnail_url = thumbnails[-1].get("url") if thumbnails else None
                        thumb_path = os.path.join(channel_thumb_dir, f"{video_id}.png")

                        # SHORTS: enrich from yt-dlp results when available
                        if vtype == "shorts":
                            meta = shorts_metadata.get(video_id, {})
                            if meta and not meta.get("error"):
                                title = meta.get("title", title)
                                description = meta.get("description", "")
                                duration_in_seconds = int(meta.get("duration", 0) or 0)
                                if duration_in_seconds:
                                    # format duration text as M:SS or H:MM:SS
                                    h, rem = divmod(duration_in_seconds, 3600)
                                    m, s = divmod(rem, 60)
                                    duration_text = (f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}")
                                else:
                                    duration_text = None

                                views = int(meta.get("view_count", 0) or 0)

                                upload_date_str = meta.get("upload_date")  # YYYYMMDD
                                if upload_date_str:
                                    try:
                                        dt = datetime.strptime(upload_date_str, "%Y%m%d").replace(tzinfo=timezone.utc)
                                        upload_timestamp = int(dt.timestamp())
                                        days_ago = (datetime.now(timezone.utc) - dt).days
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
                                # fallback to scrapetube partial info if yt-dlp failed
                                title = (
                                    video.get("title", {})
                                    .get("runs", [{}])[0]
                                    .get("text", "Untitled")
                                )
                                description = ""
                                duration_text = None
                                duration_in_seconds = 0
                                views = 0
                                upload_timestamp = int(datetime.now(timezone.utc).timestamp())
                                time_since_published = None

                        else:
                            # NON-SHORTS: parse fields from scrapetube payload (same logic as old module)
                            # Title already pulled above
                            description = (
                                video.get("descriptionSnippet", {})
                                .get("runs", [{}])[0]
                                .get("text", "")
                            )

                            duration_text = (
                                video.get("lengthText", {}).get("simpleText")
                                or video.get("lengthText", {}).get("runs", [{}])[0].get("text")
                                or None
                            )
                            duration_in_seconds = parse_duration(duration_text) if duration_text else 0

                            time_since_published = (
                                video.get("publishedTimeText", {}).get("simpleText")
                                or video.get("publishedTimeText", {}).get("runs", [{}])[0].get("text")
                                or None
                            )
                            upload_timestamp = parse_time_since_published(time_since_published)

                            # Parse view count text (may be like "1,234,567 views" or "1.2M views")
                            view_text = (
                                video.get("viewCountText", {}).get("simpleText")
                                or video.get("viewCountText", {}).get("runs", [{}])[0].get("text", "")
                            )
                            views = 0
                            if view_text:
                                try:
                                    # Normalize common formats:
                                    # - "1,234 views"
                                    # - "1.2M views"
                                    # - "1.2K views"
                                    # Remove trailing "views" and whitespace
                                    vt = view_text.replace("views", "").strip().lower()
                                    # Handle suffixes
                                    if vt.endswith("k"):
                                        views = int(float(vt[:-1].replace(",", "")) * 1_000)
                                    elif vt.endswith("m"):
                                        views = int(float(vt[:-1].replace(",", "")) * 1_000_000)
                                    elif vt.endswith("b"):
                                        views = int(float(vt[:-1].replace(",", "")) * 1_000_000_000)
                                    else:
                                        views = int(vt.replace(",", "").replace(".", ""))
                                except Exception:
                                    # best-effort fallback to remove non-digits
                                    digits = re.sub(r"[^\d]", "", view_text)
                                    try:
                                        views = int(digits) if digits else 0
                                    except Exception:
                                        views = 0

                        # Schedule thumbnail download if needed
                        if thumbnail_url and not os.path.exists(thumb_path):
                            thumbnail_tasks.append(download_img_async(thumbnail_url, thumb_path, session, thumbnail_semaphore))

                        # Prepare DB record per your (new) schema
                        video_record = {
                            "video_id": video_id,
                            "channel_id": self.channel_id,
                            "video_type": vtype,
                            "video_url": f"https://www.youtube.com/watch?v={video_id}",
                            "title": title,
                            "desc": description,
                            "duration": duration_text,
                            "duration_in_seconds": int(duration_in_seconds or 0),
                            "thumbnail_path": thumb_path,
                            "view_count": int(views or 0),
                            "time_since_published": time_since_published,
                            "upload_timestamp": int(upload_timestamp or int(datetime.now(timezone.utc).timestamp()))
                        }

                        videos_to_insert.append(video_record)

                        # progress update per chunk
                        if (idx + 1) % 10 == 0 or idx == len(videos) - 1:
                            self.progress_updated.emit(f"[{vtype.capitalize()}] Processing: {idx+1}/{len(videos)}")

                    # Wait thumbnails
                    if thumbnail_tasks:
                        self.progress_updated.emit(f"[{vtype.capitalize()}] Downloading {len(thumbnail_tasks)} thumbnails...")
                        await asyncio.gather(*thumbnail_tasks, return_exceptions=True)
                        self.progress_updated.emit(f"[{vtype.capitalize()}] ✓ All thumbnails downloaded")

                    # Insert into DB (one by one to allow DB layer to handle duplicates/constraints)
                    self.progress_updated.emit(f"[{vtype.capitalize()}] Saving {len(videos_to_insert)} videos to database...")
                    for video_data in videos_to_insert:
                        try:
                            # Depending on your DB manager, you may prefer upsert.
                            # Here we call insert() and let DatabaseManager handle uniqueness/constraints.
                            self.db.insert("VIDEO", video_data)
                        except Exception:
                            logger.exception("DB insert failed for video_id=%s", video_data.get("video_id"))

                    total_processed += len(videos_to_insert)
                    self.progress_updated.emit(f"[{vtype.capitalize()}] ✓ Saved {len(videos_to_insert)} videos")
                    self.progress_percentage.emit(min(i * 33, 95))

            self.progress_updated.emit(f"Completed scraping! Total {total_processed} videos saved.")
            self.progress_percentage.emit(100)

        except Exception:
            logger.exception("Async scrape failure")
            self.progress_updated.emit("Scraping failed — check logs.")
            self.progress_percentage.emit(0)
            # Do not swallow the exception silently — finalizer will emit finished
