import json
import re
import os
from typing import Optional, List

from PySide6.QtCore import Signal, QTimer
from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QScrollArea, QSizePolicy
)

from Backend.ScrapeTranscription import TranscriptFetcher
from Analysis.SentimentAnalysis import run_sentiment_summary
from Analysis.WordCloud import WordCloudAnalyzer
from utils.AppState import app_state
from utils.Logger import logger
from widgets.DownloadableImage import DownloadableImage


def transcript_to_sentences(transcript_list: List[dict]) -> List[str]:
    sentences = []
    for seg in transcript_list:
        text = seg.get("text")
        if isinstance(text, str) and text.strip():
            parts = re.split(r"[.!?]\s+|\n+", text.strip())
            sentences.extend([p.strip() for p in parts if p.strip()])
    return sentences


class Transcript(QWidget):
    transcript_page_scrape_transcripts_signal = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self.db = app_state.db
        self.transcript_fetcher = TranscriptFetcher()
        self.transcript_page_scrape_transcripts_signal.connect(self.scrape_transcript)

        # images
        self.sentiment_image = None
        self.wordcloud_image = None

        # main layout: only a scroll area with content
        self.main_layout = QVBoxLayout(self)
        self.setLayout(self.main_layout)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.main_layout.addWidget(self.scroll_area)

        # content widget that will hold full-size images stacked vertically
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_area.setWidget(self.scroll_content)

        self.transcript_sentences: List[str] = []

        # Auto-run on load (post-init)
        QTimer.singleShot(0, self.scrape_transcript)

    def scrape_transcript(self):
        video_list = app_state.video_list
        if not video_list:
            logger.warning("TranscriptPage: No videos in app_state.video_list")
            # clear content
            for i in reversed(range(self.scroll_layout.count())):
                w = self.scroll_layout.itemAt(i).widget()
                if w:
                    w.deleteLater()
            self.scroll_layout.addWidget(QLabel("No transcript found."))
            return

        result = self.transcript_fetcher.fetch_transcripts(video_list)

        all_segments = []
        for channel_id, video_dict in result.items():
            if not isinstance(video_dict, dict):
                continue
            for video_id, meta in video_dict.items():
                filepath = None
                if isinstance(meta, dict):
                    filepath = meta.get("filepath")
                if not filepath or not os.path.exists(filepath):
                    continue
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if isinstance(data, list):
                        all_segments.extend(data)
                except Exception:
                    logger.exception("TranscriptPage: Error reading transcript file")

        self.transcript_sentences = transcript_to_sentences(all_segments)
        self._generate_and_display_images()

    def _generate_and_display_images(self):
        # clear previous
        for i in reversed(range(self.scroll_layout.count())):
            w = self.scroll_layout.itemAt(i).widget()
            if w:
                w.deleteLater()

        if not self.transcript_sentences:
            self.scroll_layout.addWidget(QLabel("No transcript found."))
            return

        # Fixed HD sizes (Option A)
        sent_w = 1600
        sent_h = int(sent_w * 0.33)
        wc_w = 2800
        wc_h = int(wc_w * 0.6)

        logger.info(f"TranscriptPage: Generating sentiment {sent_w}x{sent_h}, wordcloud {wc_w}x{wc_h}")

        try:
            sentiment_img = run_sentiment_summary(self.transcript_sentences, width=sent_w, height=sent_h)
            wc_img = WordCloudAnalyzer(max_words=120).generate_wordcloud(self.transcript_sentences, width=wc_w, height=wc_h)
        except Exception:
            logger.exception("TranscriptPage: Error generating images")
            self.scroll_layout.addWidget(QLabel("Failed to generate analysis images."))
            return

        self.sentiment_image = sentiment_img
        self.wordcloud_image = wc_img

        channel_name = next(iter(app_state.video_list.keys()), "unknown")

        # Title label
        self.scroll_layout.addWidget(QLabel("<b>Sentiment Analysis</b>"))

        # DownloadableImage displays at natural size and provides download overlay
        sent_widget = DownloadableImage(sentiment_img, default_name=f"transcript_sentiment_{channel_name}.png")
        sent_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.scroll_layout.addWidget(sent_widget)

        self.scroll_layout.addWidget(QLabel("<b>Word Cloud</b>"))
        wc_widget = DownloadableImage(wc_img, default_name=f"transcript_wordcloud_{channel_name}.png")
        wc_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.scroll_layout.addWidget(wc_widget)

        # Spacer
        self.scroll_layout.addStretch(1)
