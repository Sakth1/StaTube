from PySide6.QtCore import Signal
from PySide6.QtWidgets import (QWidget, QLabel, QVBoxLayout, QGridLayout, QPushButton)
from typing import Optional, Dict, List
import re

from Backend.ScrapeComments import CommentFetcher
from Analysis.SentimentAnalysis import SentimentSummaryRenderer
from Analysis.WordCloud import WordCloudAnalyzer
from utils.AppState import app_state


def comments_to_sentences(data):
    """
    Converts:
        Dict[str, List[Dict]] OR just List[Dict]
    into a flat list of sentences.
    """
    sentences = []

    def extract_sentences(text: str):
        parts = re.split(r'[.!?]\s+|\n+', text)
        return [p.strip() for p in parts if p.strip()]

    def walk(comment):
        if not isinstance(comment, dict):   # skip bad/invalid items
            return

        # Extract main text
        if "text" in comment and isinstance(comment["text"], str):
            sentences.extend(extract_sentences(comment["text"]))

        # Process replies recursively
        for r in comment.get("replies", []):
            walk(r)

    # Accept either dict or direct list
    if isinstance(data, dict):
        # data = {video_id: [comments]}
        for video_id, comments in data.items():
            for c in comments:
                walk(c)
    elif isinstance(data, list):
        # data = [comments]
        for c in data:
            walk(c)
    else:
        raise TypeError("Input must be dict or list")

    return sentences

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
        self.comments = comments_to_sentences(comments)
        self.display_analysis()

    def display_analysis(self):
        """
        Displays sentiment analysis and word cloud for the fetched comments.
        """
        sentiment_analysis = SentimentSummaryRenderer()
        sentimental_analysis_img = sentiment_analysis.render_summary(self.comments)
        word_cloud = WordCloudAnalyzer(max_words=100)
        word_cloud_img = word_cloud.generate_wordcloud(self.comments)

        self.main_layout.addWidget(QLabel("Sentimental Analysis"), 0, 0)
        self.main_layout.addWidget(QLabel("Word Cloud"), 0, 1)
        self.main_layout.addWidget(sentimental_analysis_img, 1, 0)
        self.main_layout.addWidget(word_cloud_img, 1, 1)
