import yt_dlp
import json
import os
from typing import Dict, List
from PySide6.QtCore import QObject, Signal

from Data.DatabaseManager import DatabaseManager
from utils.AppState import app_state
from utils.logger import logger


class CommentWorker(QObject):
    """
    Worker thread for fetching comments to keep UI responsive.
    """
    progress_updated = Signal(str)
    progress_percentage = Signal(int)
    finished = Signal()

    def __init__(self, video_details: Dict[str, List[str]]) -> None:
        """
        Initializes the CommentWorker.

        Args:
            video_details (Dict[str, List[str]]): Dictionary of channel IDs and video ID lists.
        """
        super().__init__()
        self.video_details = video_details
        self.fetcher = CommentFetcher()

    def run(self) -> None:
        """
        Executes the comment fetching process.
        """
        try:
            total_videos = sum(len(v_list) for v_list in self.video_details.values())
            processed_count = 0
            
            self.progress_updated.emit("Starting comment scrape...")
            self.progress_percentage.emit(0)

            for channel_id, video_id_list in self.video_details.items():
                for video_id in video_id_list:
                    self.progress_updated.emit(f"Fetching comments for {video_id}...")
                    
                    # Perform fetch
                    result = self.fetcher._fetch(video_id, channel_id)
                    
                    processed_count += 1
                    percentage = int((processed_count / total_videos) * 100)
                    self.progress_percentage.emit(percentage)
                    
                    if result.get("filepath"):
                        count = result.get("comment_count", 0)
                        self.progress_updated.emit(f"Saved {count} comments for {video_id}")
                    else:
                        self.progress_updated.emit(f"Skipped: {video_id} ({result.get('remarks')})")

            self.progress_updated.emit("Comment scraping completed!")
            self.progress_percentage.emit(100)
            self.finished.emit()

        except Exception as e:
            logger.exception("Error while fetching comments:")
            self.progress_updated.emit(f"Error: {str(e)}")
            self.finished.emit()


class CommentFetcher:
    """
    A class to fetch YouTube video comments with threads using yt-dlp.
    
    Attributes:
        db (DatabaseManager): The database manager instance.
        video_comments (dict): A dictionary storing the fetched comments.
    """
    def __init__(self) -> None:
        """
        Initializes the CommentFetcher instance.
        """
        self.db: DatabaseManager = app_state.db
        self.video_comments: Dict[str, List[Dict[str, str]]] = {}

    def _fetch(self, video_id: str, channel_id: str) -> Dict[str, str]:
        """
        Fetch comments for a single video including replies (threads).
        
        Args:
            video_id (str): YouTube video ID
            channel_id (str): Channel ID for organizing storage
            
        Returns:
            Dictionary with video_id, filepath, comment_count, and remarks
        """
        try:
            ydl_opts = {
                'skip_download': True,
                'getcomments': True,
                'extractor_args': {'youtube': {'comment_sort': ['top']}},
                'quiet': True,
                'no_warnings': True,
            }
            
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                
                # Check if comments are available
                if 'comments' not in info or info['comments'] is None:
                    logger.warning(f"Comments disabled or unavailable for {video_id}")
                    return {
                        'video_id': video_id,
                        'filepath': None,
                        'comment_count': 0,
                        'remarks': "Comments disabled"
                    }
                
                # Process comments with thread structure
                all_comments = []
                comments_dict = {}  # To track parent comments
                
                # First pass: comments by ID
                for comment in info['comments']:
                    comment_data = {
                        'comment_id': comment.get('id'),
                        'author': comment.get('author'),
                        'author_id': comment.get('author_id'),
                        'text': comment.get('text'),
                        'like_count': comment.get('like_count', 0),
                        'is_favorited': comment.get('is_favorited', False),
                        'timestamp': comment.get('timestamp'),
                        'parent': comment.get('parent', 'root'),
                        'replies': []
                    }
                    comments_dict[comment_data['comment_id']] = comment_data
                
                # Second pass: build thread structure
                for comment_id, comment_data in comments_dict.items():
                    parent = comment_data['parent']
                    if parent == 'root':
                        # Top-level comment
                        all_comments.append(comment_data)
                    else:
                        # Reply to another comment
                        if parent in comments_dict:
                            comments_dict[parent]['replies'].append(comment_data)
                
                # Save comments to file
                filename = f"{video_id}.json"
                filepath = self.save_comments(all_comments, channel_id, filename)
                
                result = {
                    'video_id': video_id,
                    'filepath': filepath,
                    'comment_count': len(all_comments),
                    'remarks': None
                }
                
        except yt_dlp.utils.DownloadError as e:
            error_msg = str(e)
            if 'comments are turned off' in error_msg.lower() or 'disabled comments' in error_msg.lower():
                logger.warning(f"Comments disabled for {video_id}")
                result = {
                    'video_id': video_id,
                    'filepath': None,
                    'comment_count': 0,
                    'remarks': "Comments disabled"
                }
            elif 'video unavailable' in error_msg.lower() or 'video not found' in error_msg.lower():
                logger.warning(f"Video not found: {video_id}")
                result = {
                    'video_id': video_id,
                    'filepath': None,
                    'comment_count': 0,
                    'remarks': "Video not found"
                }
            else:
                logger.error(f"Download error fetching comments for {video_id}")
                logger.exception("Comment fetch error:")
                result = {
                    'video_id': video_id,
                    'filepath': None,
                    'comment_count': 0,
                    'remarks': f"Error: {error_msg}"
                }
                
        except Exception as e:
            logger.error(f"Error fetching comments for {video_id}")
            logger.exception("Comment fetch general error:")
            result = {
                'video_id': video_id,
                'filepath': None,
                'comment_count': 0,
                'remarks': f"Error: {str(e)}"
            }
        
        finally:
            return result

    def fetch_comments(self, video_details: Dict[str, List[str]]) -> Dict[str, List[Dict[str, str]]]:
        """
        Fetch comments for multiple videos organized by channel.
        
        Args:
            video_details (Dict[str, List[str]]): Dictionary with channel_id as key and list of video_ids as value
            
        Returns:
            Dictionary with channel_id as key and video comments as value
        """
        try:
            for channel_id, video_id_list in video_details.items():
                comments = {}
                for video_id in video_id_list:
                    result = self._fetch(video_id, channel_id)
                    comments[video_id] = result
                
                self.video_comments[channel_id] = comments
            
            return self.video_comments
            
        except Exception as e:
            logger.error("Error fetching comments for multiple videos")
            logger.exception("Comment fetch general error:")
            return None

    def save_comments(self, comments_data: List[Dict[str, str]], channel_id: str, filename: str) -> str:
        """
        Saves comment data to a JSON file.
        
        Args:
            comments_data (List[Dict[str, str]]): List of comment dictionaries
            channel_id (str): Channel ID for organizing storage
            filename (str): Name of the file to save
            
        Returns:
            Filepath if successful, False otherwise
        """
        if not comments_data:
            return False
        
        filepath = os.path.join(self.db.comment_dir, channel_id, filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(comments_data, f, indent=2, ensure_ascii=False)
            return filepath
        
        except Exception as e:
            logger.error(f"Error saving comments for {filename}")
            logger.exception("Comment save error:")
            return False