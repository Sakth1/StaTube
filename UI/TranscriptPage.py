from PySide6.QtCore import Signal
from PySide6.QtWidgets import (QWidget, QLabel, QVBoxLayout, QGridLayout, QPushButton,
                               QComboBox)
from typing import Optional, Dict, List

from Backend.ScrapeTranscription import TranscriptFetcher
from Data.DatabaseManager import DatabaseManager
from utils.AppState import app_state

class Transcript(QWidget):
    """
    A widget to display and scrape YouTube video transcripts.

    Attributes:
        transcript_page_scrape_transcripts_signal (Signal): Emitted when transcript scraping is complete.
    """

    transcript_page_scrape_transcripts_signal = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initializes the Transcript widget.

        Args:
            parent (QWidget): The parent widget.
        """
        super(Transcript, self).__init__(parent)

        self.db: DatabaseManager = app_state.db
        self.transcript_fetcher: TranscriptFetcher = TranscriptFetcher()
        self.transcript_page_scrape_transcripts_signal.connect(self.scrape_transcript)

        self.main_layout: QGridLayout = QGridLayout(self)
        self.setLayout(self.main_layout)

        self.scrape_transcript_button: QPushButton = QPushButton("Scrape Transcript")
        self.scrape_transcript_button.clicked.connect(self.scrape_transcript)
        self.main_layout.addWidget(self.scrape_transcript_button)

        self.language_selection: QComboBox = QComboBox()
        self.language_selection.addItems(["en", "es"])

    def scrape_transcript(self) -> None:
        """
        Scrapes YouTube video transcripts for a list of videos.

        Returns:
            dict: A dictionary with video_id as key and video transcript as value.
        """
        video_list: List[str] = app_state.video_list
        if not video_list:
            return
        languages: str = self.language_selection.currentText()
        transcripts: Dict[str, str] = self.transcript_fetcher.fetch_transcripts(video_list, languages)
