import json
import re
import os
from typing import Optional, List, Dict

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QGridLayout, QPushButton,
    QComboBox, QScrollArea, QSizePolicy
)
from PySide6.QtGui import QPixmap

from Backend.ScrapeTranscription import TranscriptFetcher
from Analysis.SentimentAnalysis import run_sentiment_summary
from Analysis.WordCloud import WordCloudAnalyzer
from utils.AppState import app_state
from utils.logger import logger


# -------------------------------------------------------------
# Convert transcript → sentences
# -------------------------------------------------------------
def transcript_to_sentences(transcript_list: List[dict]) -> List[str]:
    sentences = []
    for seg in transcript_list:
        text = seg.get("text")
        if isinstance(text, str) and text.strip():
            parts = re.split(r"[.!?]\s+|\n+", text.strip())
            sentences.extend([p.strip() for p in parts if p.strip()])
    return sentences


# -------------------------------------------------------------
# Transcript Page
# -------------------------------------------------------------
class Transcript(QWidget):

    transcript_page_scrape_transcripts_signal = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super(Transcript, self).__init__(parent)

        self.db = app_state.db
        self.transcript_fetcher = TranscriptFetcher()
        self.transcript_page_scrape_transcripts_signal.connect(self.scrape_transcript)

        # UI Layout ------------------------------------------------
        self.main_layout = QVBoxLayout(self)
        self.setLayout(self.main_layout)

        self.scrape_btn = QPushButton("Scrape Transcript")
        self.scrape_btn.clicked.connect(self.scrape_transcript)
        self.main_layout.addWidget(self.scrape_btn)

        self.language_selection = QComboBox()
        self.language_selection.addItems(["en", "es"])
        self.main_layout.addWidget(self.language_selection)

        # Scroll area for analysis output
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.main_layout.addWidget(self.scroll_area)

        self.scroll_content = QWidget()
        self.scroll_layout = QGridLayout(self.scroll_content)
        self.scroll_area.setWidget(self.scroll_content)

        self.transcript_sentences: List[str] = []


    # ---------------------------------------------------------
    # SCRAPE + LOAD + ANALYZE
    # ---------------------------------------------------------
    def scrape_transcript(self):
        video_list = app_state.video_list
        if not video_list:
            logger.warning("TranscriptPage: No videos in app_state.video_list")
            return

        language = self.language_selection.currentText()

        result = self.transcript_fetcher.fetch_transcripts(video_list, language)

        all_segments = []

        # loop channels
        for channel_id, video_dict in result.items():

            # if fetcher returns a list instead of dict, skip safely
            if not isinstance(video_dict, dict):
                logger.error(f"TranscriptPage: Unexpected structure for {channel_id}: {video_dict}")
                continue

            # loop videos under channel
            for video_id, meta in video_dict.items():

                filepath = None

                # meta must be dict containing "filepath"
                if isinstance(meta, dict):
                    filepath = meta.get("filepath")

                # validate filepath
                if not filepath or not isinstance(filepath, str):
                    logger.error(f"TranscriptPage: Invalid filepath for {channel_id}/{video_id}: {meta}")
                    continue

                if not os.path.exists(filepath):
                    logger.error(f"TranscriptPage: Transcript file not found: {filepath}")
                    continue

                # Load JSON transcript
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)

                    if isinstance(data, list):
                        all_segments.extend(data)
                    else:
                        logger.error(f"TranscriptPage: Unexpected transcript JSON in {filepath}: {type(data)}")

                except Exception as e:
                    logger.error(f"TranscriptPage: Error reading transcript {filepath}")
                    logger.exception(e)


        # Convert → sentences
        self.transcript_sentences = transcript_to_sentences(all_segments)

        self.display_analysis()


    # ---------------------------------------------------------
    # SHOW ANALYSIS
    # ---------------------------------------------------------
    def display_analysis(self):

        # Clear previous widget content
        for i in reversed(range(self.scroll_layout.count())):
            w = self.scroll_layout.itemAt(i).widget()
            if w:
                w.deleteLater()

        if not self.transcript_sentences:
            self.scroll_layout.addWidget(QLabel("No transcript found."), 0, 0)
            return
        
        logger.info(f"TranscriptPage: Running analysis on {len(self.transcript_sentences)} sentences")

        # Run sentiment + wordcloud
        sentiment_img = run_sentiment_summary(self.transcript_sentences)

        wc = WordCloudAnalyzer(max_words=120)
        wordcloud_img = wc.generate_wordcloud(self.transcript_sentences)

        # scaled label helper
        def scaled_label(qimage):
            label = QLabel()
            pix = QPixmap.fromImage(qimage)

            viewport_width = self.scroll_area.viewport().width()
            target_width = max(200, viewport_width - 40)  # safe width

            scaled = pix.scaledToWidth(target_width, Qt.SmoothTransformation)
            label.setPixmap(scaled)
            label.setAlignment(Qt.AlignCenter)
            label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            return label

        # Insert into layout
        self.scroll_layout.addWidget(QLabel("<b>Sentiment Analysis</b>"), 0, 0)
        self.scroll_layout.addWidget(scaled_label(sentiment_img), 1, 0)

        self.scroll_layout.addWidget(QLabel("<b>Word Cloud</b>"), 2, 0)
        self.scroll_layout.addWidget(scaled_label(wordcloud_img), 3, 0)

        self.scroll_layout.setRowStretch(4, 1)
