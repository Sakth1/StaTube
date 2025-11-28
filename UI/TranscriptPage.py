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


# -------------------------------------------------------------
# Helper: Convert transcript segments → sentences
# -------------------------------------------------------------
def transcript_to_sentences(transcript_list: List[dict]) -> List[str]:
    """
    Convert a list of transcript segments into plain text sentences.
    Expected format:
        [
            { "text": "Hello world", "start": 0.0, "duration": 3.3 },
            ...
        ]
    """
    sentences = []
    for seg in transcript_list:
        text = seg.get("text")
        if isinstance(text, str) and text.strip():
            # split into smaller sentences
            parts = re.split(r"[.!?]\s+|\n+", text.strip())
            parts = [p.strip() for p in parts if p.strip()]
            sentences.extend(parts)

    return sentences


# -------------------------------------------------------------
# Transcript Page Widget
# -------------------------------------------------------------
class Transcript(QWidget):

    transcript_page_scrape_transcripts_signal = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super(Transcript, self).__init__(parent)

        self.db = app_state.db
        self.transcript_fetcher = TranscriptFetcher()
        self.transcript_page_scrape_transcripts_signal.connect(self.scrape_transcript)

        # -----------------------------------------------------
        # MAIN LAYOUT
        # -----------------------------------------------------
        self.main_layout = QVBoxLayout(self)
        self.setLayout(self.main_layout)

        # Scrape button
        self.scrape_transcript_button = QPushButton("Scrape Transcript")
        self.scrape_transcript_button.clicked.connect(self.scrape_transcript)
        self.main_layout.addWidget(self.scrape_transcript_button)

        # Language selector
        self.language_selection = QComboBox()
        self.language_selection.addItems(["en", "es"])
        self.main_layout.addWidget(self.language_selection)

        # -----------------------------------------------------
        # Scroll Area for Display
        # -----------------------------------------------------
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
        """
        Scrape transcript JSON files for selected videos, convert to sentences,
        and display analysis.
        """
        video_list: List[str] = app_state.video_list
        if not video_list:
            print("No videos found in app_state.video_list")
            return

        language = self.language_selection.currentText()

        # Fetch transcripts -> returns { video_id: path OR { "filepath": "path" } }
        result = self.transcript_fetcher.fetch_transcripts(video_list, language)

        all_segments = []

        # Load JSON transcripts
        for vid, meta in result.items():

            # Supports both formats: string or dict
            if isinstance(meta, dict):
                filepath = meta.get("filepath")
            else:
                filepath = meta

            if not filepath or not isinstance(filepath, str):
                print(f"Invalid filepath for {vid}: {filepath}")
                continue

            if not os.path.exists(filepath):
                print(f"Transcript file missing: {filepath}")
                continue

            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)

                if isinstance(data, list):
                    all_segments.extend(data)
                else:
                    print(f"Unexpected transcript JSON format in {filepath}: {type(data)}")

            except Exception as e:
                print(f"Failed to read transcript {filepath}: {e}")

        # Convert → sentences
        self.transcript_sentences = transcript_to_sentences(all_segments)

        # Display analysis
        self.display_analysis()

    # ---------------------------------------------------------
    # DISPLAY ANALYSIS (Sentiment + Word Cloud)
    # ---------------------------------------------------------
    def display_analysis(self):
        # Clear previous widgets
        for i in reversed(range(self.scroll_layout.count())):
            item = self.scroll_layout.itemAt(i)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # Empty?
        if not self.transcript_sentences:
            self.scroll_layout.addWidget(QLabel("No transcript found."), 0, 0)
            return

        # -----------------------------------------------------
        # RUN ANALYSIS
        # -----------------------------------------------------
        sentiment_img = run_sentiment_summary(self.transcript_sentences)

        wc = WordCloudAnalyzer(max_words=120)
        wordcloud_img = wc.generate_wordcloud(self.transcript_sentences)

        # -----------------------------------------------------
        # Safe scaling for QPixmap (fixes QFont warnings)
        # -----------------------------------------------------
        def scaled_label(qimg):
            label = QLabel()
            pix = QPixmap.fromImage(qimg)

            # Ensure width stays >= 200px to avoid Qt font errors
            viewport_width = self.scroll_area.viewport().width()
            target_width = max(200, viewport_width - 40)

            scaled = pix.scaledToWidth(target_width, Qt.SmoothTransformation)

            label.setPixmap(scaled)
            label.setAlignment(Qt.AlignCenter)
            label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            return label

        # -----------------------------------------------------
        # INSERT INTO UI
        # -----------------------------------------------------
        self.scroll_layout.addWidget(QLabel("<b>Sentimental Analysis</b>"), 0, 0)
        self.scroll_layout.addWidget(scaled_label(sentiment_img), 1, 0)

        self.scroll_layout.addWidget(QLabel("<b>Word Cloud</b>"), 2, 0)
        self.scroll_layout.addWidget(scaled_label(wordcloud_img), 3, 0)

        self.scroll_layout.setRowStretch(4, 1)
