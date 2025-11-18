from PySide6.QtCore import Signal
from PySide6.QtWidgets import (QWidget, QLabel, QVBoxLayout, QGridLayout, QPushButton)
from typing import Optional, Dict, List

from Backend.ScrapeComments import CommentFetcher
from utils.AppState import app_state

class Comment(QWidget):
    """
    A widget to display and scrape YouTube video comments.
    """

    comment_page_scrape_comments_signal = Signal()
    """
    Emitted when the scrape comments button is clicked.
    """

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initializes the Comment widget.

        Args:
            parent (QWidget): The parent widget.
        """
        super(Comment, self).__init__(parent)

        self.db = app_state.db
        self.comment_fetcher = CommentFetcher()
        self.comment_page_scrape_comments_signal.connect(self.scrape_comments)

        self.main_layout = QGridLayout(self)
        self.setLayout(self.main_layout)

        self.scrape_comments_button = QPushButton("Scrape Comments")
        self.scrape_comments_button.clicked.connect(self.scrape_comments)
        self.main_layout.addWidget(self.scrape_comments_button)
    
    def scrape_comments(self):
        """
        Fetches video comments from the video list.

        Returns:
            Dict[str, List[Dict[str, str]]]: A dictionary with video_id as key and video comments as value.
        """
        video_list: List[str] = app_state.video_list
        if not video_list:
            return
        comments: Dict[str, List[Dict[str, str]]] = self.comment_fetcher.fetch_comments(video_list)
        print('comments', comments)
