from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QGridLayout,
    QScrollArea, QSizePolicy
)
from typing import Optional, Dict, List
import re
import json
import os

from Backend.ScrapeComments import CommentFetcher
from Analysis.SentimentAnalysis import run_sentiment_summary
from Analysis.WordCloud import WordCloudAnalyzer
from utils.AppState import app_state


def comments_to_sentences(data):
    """
    Flatten a list (or nested structure) of comment dicts into
    a list of plain text sentences.
    """
    sentences: List[str] = []

    def extract_sentences(text: str) -> List[str]:
        parts = re.split(r"[.!?]\s+|\n+", text)
        return [p.strip() for p in parts if p.strip()]

    def walk(item):
        # Raw text
        if isinstance(item, str):
            sentences.extend(extract_sentences(item))
            return

        # Only handle dict comments
        if not isinstance(item, dict):
            return

        text = item.get("text")
        if isinstance(text, str):
            sentences.extend(extract_sentences(text))

        # Recurse into replies
        for r in item.get("replies", []):
            walk(r)

    if isinstance(data, dict):
        for _, comments in data.items():
            for c in comments:
                walk(c)
    elif isinstance(data, list):
        for c in data:
            walk(c)
    else:
        raise TypeError("Input must be dict or list")

    return sentences


class Comment(QWidget):

    comment_page_scrape_comments_signal = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super(Comment, self).__init__(parent)

        self.db = app_state.db
        self.comment_fetcher = CommentFetcher()
        self.comment_page_scrape_comments_signal.connect(self.scrape_comments)

        # ----------------------------
        # MAIN SCROLLABLE PAGE SETUP
        # ----------------------------
        self.layout = QVBoxLayout(self)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.layout.addWidget(self.scroll_area)

        # Content widget inside scroll area
        self.scroll_content = QWidget()
        self.scroll_layout = QGridLayout(self.scroll_content)
        self.scroll_area.setWidget(self.scroll_content)

        self.comments: List[str] = []

    def scrape_comments(self):
        """
        Fetch comments for selected videos, load JSON from disk,
        convert to sentences, and trigger analysis.
        """
        video_details = app_state.video_list  # expected: Dict[channel_id, List[video_id]]

        if not video_details:
            print("No videos in app_state.video_list")
            return

        # If it's a plain list, wrap it under a dummy key
        if isinstance(video_details, list):
            video_details = {"default": video_details}

        # 1) Scrape + save comments (and get filepaths)
        results = self.comment_fetcher.fetch_comments(video_details)
        if not results:
            print("fetch_comments returned no results")
            return

        # 2) Load all comment JSONs from disk using the filepaths
        all_comment_dicts: List[dict] = []

        for channel_id, videos_dict in results.items():
            # videos_dict: { video_id: { 'filepath': ..., ... } }
            for video_id, meta in videos_dict.items():
                filepath = meta.get("filepath")
                if not filepath:
                    print(f"No filepath for {video_id} (channel {channel_id})")
                    continue

                if not os.path.exists(filepath):
                    print(f"Comment file not found: {filepath}")
                    continue

                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        comments_for_video = json.load(f)

                    if isinstance(comments_for_video, list):
                        all_comment_dicts.extend(comments_for_video)
                    else:
                        print(f"Unexpected JSON format in {filepath}: {type(comments_for_video)}")

                except Exception as e:
                    print(f"Failed to read comments from {filepath}: {e}")

        # 3) Convert all these comment dicts into sentences
        self.comments = comments_to_sentences(all_comment_dicts)
        self.display_analysis()

    def display_analysis(self):
        # Clear previous widgets from scroll layout
        for i in reversed(range(self.scroll_layout.count())):
            item = self.scroll_layout.itemAt(i)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        if not self.comments:
            msg = QLabel("No comments found.")
            self.scroll_layout.addWidget(msg, 0, 0)
            return

        # ---------------------------
        # RUN ANALYSIS
        # ---------------------------
        sentimental_analysis_img = run_sentiment_summary(self.comments)

        word_cloud = WordCloudAnalyzer(max_words=100)
        word_cloud_img = word_cloud.generate_wordcloud(self.comments)

        # ---------------------------
        # AUTO RESIZE IMAGES
        # ---------------------------
        def scaled_label(qimage):
            label = QLabel()
            pix = QPixmap.fromImage(qimage)

            target_width = self.scroll_area.viewport().width() - 40
            if target_width > 0:
                scaled = pix.scaledToWidth(target_width, Qt.SmoothTransformation)
            else:
                scaled = pix

            label.setPixmap(scaled)
            label.setAlignment(Qt.AlignCenter)
            label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            return label

        sent_label = scaled_label(sentimental_analysis_img)
        wc_label = scaled_label(word_cloud_img)

        # ---------------------------
        # PLACE INTO SCROLL LAYOUT
        # ---------------------------
        self.scroll_layout.addWidget(QLabel("<b>Sentimental Analysis</b>"), 0, 0)
        self.scroll_layout.addWidget(sent_label, 1, 0)

        self.scroll_layout.addWidget(QLabel("<b>Word Cloud</b>"), 2, 0)
        self.scroll_layout.addWidget(wc_label, 3, 0)

        self.scroll_layout.setRowStretch(4, 1)
