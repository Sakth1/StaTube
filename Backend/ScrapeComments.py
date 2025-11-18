import yt_dlp
import json
import os
from typing import Dict, List

from Data.DatabaseManager import DatabaseManager
from utils.AppState import app_state


class CommentFetcher:
    """
    A class to fetch YouTube video comments with threads using yt-dlp.
    """
    def __init__(self):
        self.db: DatabaseManager = app_state.db
        self.video_comments: dict = {}

    def _fetch(self, video_id: str, channel_id: str) -> Dict:
        """
        Fetch comments for a single video including replies (threads).
        
        Args:
            video_id: YouTube video ID
            channel_id: Channel ID for organizing storage
            
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
                    print(f"Comments disabled or unavailable for {video_id}")
                    return {
                        'video_id': video_id,
                        'filepath': None,
                        'comment_count': 0,
                        'remarks': "Comments disabled"
                    }
                
                # Process comments with thread structure
                all_comments = []
                comments_dict = {}  # To track parent comments
                
                # First pass: organize comments by ID
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
                print(f"Comments disabled for {video_id}")
                result = {
                    'video_id': video_id,
                    'filepath': None,
                    'comment_count': 0,
                    'remarks': "Comments disabled"
                }
            elif 'video unavailable' in error_msg.lower() or 'video not found' in error_msg.lower():
                print(f"Video not found: {video_id}")
                result = {
                    'video_id': video_id,
                    'filepath': None,
                    'comment_count': 0,
                    'remarks': "Video not found"
                }
            else:
                print(f"Download Error fetching comments for {video_id}: {e}")
                result = {
                    'video_id': video_id,
                    'filepath': None,
                    'comment_count': 0,
                    'remarks': f"Error: {error_msg}"
                }
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Error fetching comments for {video_id}: {e}")
            result = {
                'video_id': video_id,
                'filepath': None,
                'comment_count': 0,
                'remarks': f"Error: {str(e)}"
            }
        
        finally:
            return result

    def fetch_comments(self, video_details: Dict[str, List[str]]) -> Dict:
        """
        Fetch comments for multiple videos organized by channel.
        
        Args:
            video_details: Dictionary with channel_id as key and list of video_ids as value
            
        Returns:
            Dictionary with channel_id as key and video comments as value
        """
        try:
            for channel_id, video_id_list in video_details.items():
                comments = {}
                for video_id in video_id_list:
                    result = self._fetch(video_id, channel_id)
                    if result.get("filepath") is None:
                        print(f"{video_id}: {result.get('remarks')}")
                    comments[video_id] = result
                
                self.video_comments[channel_id] = comments
            
            return self.video_comments
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Error fetching comments: {e}")
            return None

    def save_comments(self, comments_data: List[Dict], channel_id: str, filename: str) -> str:
        """
        Saves comment data to a JSON file.
        
        Args:
            comments_data: List of comment dictionaries
            channel_id: Channel ID for organizing storage
            filename: Name of the file to save
            
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
            print(f"Comments saved to: {filepath}")
            return filepath
        
        except Exception as e:
            print(f"Error saving comments for {filename}: {e}")
            return False    
