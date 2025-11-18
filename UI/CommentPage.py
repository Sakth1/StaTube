from PySide6.QtCore import Signal
from PySide6.QtWidgets import (QWidget, QLabel, QVBoxLayout, QGridLayout, QPushButton)

from Backend.ScrapeComments import CommentFetcher
from utils.AppState import app_state

class Comment(QWidget):
    comment_page_scrape_comments_signal = Signal()

    def __init__(self, parent=None):
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
        video_list = app_state.video_list
        if not video_list:
            return
        comments = self.comment_fetcher.fetch_comments(video_list)
        print('comments', comments)