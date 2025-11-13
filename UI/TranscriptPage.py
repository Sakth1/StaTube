from PySide6 import QtCore
from PySide6.QtWidgets import (QWidget, QLabel, QVBoxLayout, QGridLayout, QPushButton,
                               QComboBox)

from Backend.ScrapeTranscription import TranscriptFetcher
from utils.AppState import app_state

class Transcript(QWidget):
    def __init__(self, parent=None):
        super(Transcript, self).__init__(parent)

        self.db = app_state.db
        self.transcript_fetcher = TranscriptFetcher()

        self.main_layout = QGridLayout(self)
        self.setLayout(self.main_layout)

        self.scrape_transcript_button = QPushButton("Scrape Transcript")
        self.scrape_transcript_button.clicked.connect(self.scrape_transcript)
        self.main_layout.addWidget(self.scrape_transcript_button)

        self.language_selection = QComboBox()
        self.language_selection.addItems(["en", "es"])
        
    
    def scrape_transcript(self):
        video_list = app_state.video_list
        if not video_list:
            return
        languages = self.language_selection.currentText()
        transcripts = self.transcript_fetcher.fetch_transcripts(video_list)
        print('transcripts', transcripts)
