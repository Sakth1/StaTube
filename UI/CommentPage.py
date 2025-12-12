from PySide6.QtCore import Signal, QTimer, QThread
from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QScrollArea, QSizePolicy
)
from typing import Optional, List
import re
import json
import os

from Backend.ScrapeComments import CommentFetcher
from Backend.AnalysisWorker import AnalysisWorker
from UI.SplashScreen import SplashScreen
from utils.AppState import app_state
from utils.Logger import logger

from widgets.DownloadableImage import DownloadableImage


def comments_to_sentences(data):
    sentences = []

    def extract(text: str):
        parts = re.split(r"[.!?]\s+|\n+", text)
        return [p.strip() for p in parts if p.strip()]

    def walk(item):
        if isinstance(item, str):
            sentences.extend(extract(item))
            return

        if isinstance(item, dict):
            text = item.get("text")
            if isinstance(text, str):
                sentences.extend(extract(text))
            for r in item.get("replies", []):
                walk(r)

    if isinstance(data, dict):
        for comments in data.values():
            for c in comments:
                walk(c)
    elif isinstance(data, list):
        for c in data:
            walk(c)
    return sentences


class Comment(QWidget):
    comment_page_scrape_comments_signal = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self.db = app_state.db
        self.comment_fetcher = CommentFetcher()
        self.comment_page_scrape_comments_signal.connect(self.scrape_comments)

        self.sentiment_image = None
        self.wordcloud_image = None

        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.layout.addWidget(self.scroll_area)

        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_area.setWidget(self.scroll_content)

        self.comments: List[str] = []

        # Auto-run on load
        QTimer.singleShot(0, self.scrape_comments)

    def scrape_comments(self):
        video_details = app_state.video_list
        if not video_details:
            logger.warning("CommentPage: No videos in app_state.video_list")
            for i in reversed(range(self.scroll_layout.count())):
                w = self.scroll_layout.itemAt(i).widget()
                if w:
                    w.deleteLater()
            self.scroll_layout.addWidget(QLabel("No comments found."))
            return

        if isinstance(video_details, list):
            video_details = {"default": video_details}

        results = self.comment_fetcher.fetch_comments(video_details)
        if not results:
            logger.error("CommentPage: fetch_comments returned no results")
            self.scroll_layout.addWidget(QLabel("No comments found."))
            return

        all_comment_dicts = []
        for channel_id, vids in results.items():
            for vid, meta in vids.items():
                filepath = meta.get("filepath")
                if not filepath or not os.path.exists(filepath):
                    continue
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if isinstance(data, list):
                        all_comment_dicts.extend(data)
                except Exception:
                    logger.exception("Error reading comments file")

        self.comments = comments_to_sentences(all_comment_dicts)
        self._generate_and_display_images()

    def _generate_and_display_images(self):
        # Clear previous
        for i in reversed(range(self.scroll_layout.count())):
            w = self.scroll_layout.itemAt(i).widget()
            if w:
                w.deleteLater()

        if not self.comments:
            self.scroll_layout.addWidget(QLabel("No comments found."))
            return

        # Sizes
        sent_w = 1600
        sent_h = int(sent_w * 0.33)
        wc_w = 2800
        wc_h = int(wc_w * 0.6)

        logger.info(f"CommentPage: Queuing analysis sentiment {sent_w}x{sent_h}, wordcloud {wc_w}x{wc_h}")

        self.analysis_thread = QThread()
        self.analysis_worker = AnalysisWorker(self.comments, sentiment_size=(sent_w, sent_h), wordcloud_size=(wc_w, wc_h), max_words=100)
        self.analysis_worker.moveToThread(self.analysis_thread)

        # Create splash
        parent_win = self.window() if hasattr(self, "window") else None
        self.splash = SplashScreen(parent=parent_win)
        self.splash.set_title("Analyzing comments...")
        self.splash.update_status("Preparing analysis...")
        self.splash.set_progress(0)
        self.splash.enable_runtime_mode(parent_window=parent_win, cancel_callback=self._cancel_analysis)
        self.splash.show_with_animation()

        # Wire signals
        self.analysis_thread.started.connect(self.analysis_worker.run)
        self.analysis_worker.progress_updated.connect(lambda m: (self.splash.update_status(m) if self.splash else None))
        self.analysis_worker.progress_percentage.connect(lambda p: (self.splash.set_progress(p) if self.splash else None))
        self.analysis_worker.sentiment_ready.connect(self._on_sentiment_ready)
        self.analysis_worker.wordcloud_ready.connect(self._on_wordcloud_ready)
        self.analysis_worker.finished.connect(self.analysis_thread.quit)
        self.analysis_worker.finished.connect(self.analysis_worker.deleteLater)
        self.analysis_thread.finished.connect(self.analysis_thread.deleteLater)
        # When thread fully finishes, fade splash
        self.analysis_thread.finished.connect(lambda: (self.splash.fade_and_close(300) if self.splash else None))

        self.analysis_thread.start()

    # helper cancel method
    def _cancel_analysis(self):
        if hasattr(self, "analysis_worker") and self.analysis_worker:
            try:
                self.analysis_worker.cancel()
            except Exception:
                pass
        # also attempt to stop thread gracefully
        if hasattr(self, "analysis_thread") and self.analysis_thread.isRunning():
            try:
                self.analysis_thread.requestInterruption()
                self.analysis_thread.quit()
                self.analysis_thread.wait(200)
            except Exception:
                pass
        # ensure UI shows canceled
        for i in reversed(range(self.scroll_layout.count())):
            w = self.scroll_layout.itemAt(i).widget()
            if w:
                w.deleteLater()
        self.scroll_layout.addWidget(QLabel("Analysis cancelled."))

    # slots to receive images
    def _on_sentiment_ready(self, qimage):
        self.sentiment_image = qimage
        # show immediately (title)
        channel_name = next(iter(app_state.video_list.keys()), "unknown")
        self.scroll_layout.addWidget(QLabel("<b>Sentiment Analysis</b>"))
        sent_widget = DownloadableImage(qimage, default_name=f"comment_sentiment_{channel_name}.png")
        sent_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.scroll_layout.addWidget(sent_widget)

    def _on_wordcloud_ready(self, qimage):
        self.wordcloud_image = qimage
        self.scroll_layout.addWidget(QLabel("<b>Word Cloud</b>"))
        channel_name = next(iter(app_state.video_list.keys()), "unknown")
        wc_widget = DownloadableImage(qimage, default_name=f"comment_wordcloud_{channel_name}.png")
        wc_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.scroll_layout.addWidget(wc_widget)
        self.scroll_layout.addStretch(1)
