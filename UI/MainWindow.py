from PySide6 import QtCore, QtGui
from PySide6.QtWidgets import (QApplication, QMainWindow, QStackedWidget, QWidget, 
                               QLineEdit, QComboBox, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton)
import threading
import time
import traceback

from Backend.ScrapeChannel import Search
from Backend.ScrapeVideo import Videos
from Backend.ScrapeTranscription import Transcription


class MainWindow(QMainWindow):
    results_ready = QtCore.Signal(list)
    def __init__(self):
        super(MainWindow, self).__init__()

        self.top_panel = QWidget()
        self.bottom_panel = QWidget()
        self.central_layout = QVBoxLayout()
        self.central_widget = QStackedWidget()
        self.searchbar = QComboBox()
        self.search_timer = QtCore.QTimer()
        self.stop_event = threading.Event()
        self.search_thread_instance = None
        self.channels = None
        self.scrap_video_button = QPushButton("Scrape Video")
        self.scrape_transcription_button = QPushButton("screpe transcription")

        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.search_keyword)

        self.central_widget.addWidget(self.top_panel)
        self.central_widget.addWidget(self.bottom_panel)
        
        self.searchbar.setEditable(True)
        self.searchbar.setPlaceholderText("Search")
        self.searchbar.lineEdit().textEdited.connect(self.reset_search_timer)
        self.scrap_video_button.clicked.connect(self.scrape_videos)
        self.scrape_transcription_button.clicked.connect(self.scrape_transcription)
        self.results_ready.connect(self.update_results)

        self.setupUi()

        self.setCentralWidget(self.central_widget)
    
    def setupUi(self):
        """
        Set up the user interface of the main window.
        """
        self.setGeometry(500, 200, 500, 300)
        self.setuptop()
        self.setupbottom()

    def setuptop(self):
        self.top_layout = QVBoxLayout()
        self.top_layout.addWidget(self.searchbar)
        self.top_layout.addWidget(self.scrap_video_button)
        self.top_layout.addWidget(self.scrape_transcription_button)
        self.top_panel.setLayout(self.top_layout)
        self.top_panel.show()
    
    def setupbottom(self):
        self.bottom_layout = QVBoxLayout()
        self.bottom_panel.setLayout(self.bottom_layout)
        self.bottom_panel.show()

    def reset_search_timer(self):
        self.search_timer.start(400)

    def search_thread(self, query):
        print("search channel thread triggered")
        search = Search()
        self.channels = search.search_channel(query)
        self.channel_name = []
        for key, item in self.channels.items():
            self.channel_name.append(item)
        self.results_ready.emit(self.channel_name)

    def update_results(self, channels):
        text = self.searchbar.currentText()
        self.searchbar.blockSignals(True)
        self.searchbar.clear()
        self.searchbar.setCurrentText(text)
        self.searchbar.addItems(channels)
        self.searchbar.showPopup()
        
        self.searchbar.blockSignals(False)

    def search_keyword(self):
        try:
            if self.search_thread_instance and self.search_thread_instance.is_alive():
                self.stop_event.set()
                self.search_thread_instance.join(timeout=0.1)

            self.stop_event.clear()

            query = self.searchbar.currentText()
            self.search_thread_instance = threading.Thread(target=self.search_thread, daemon=True, args=(query,))
            self.search_thread_instance.start()
        
        except Exception as e:
            traceback.print_exc()
            print(e)

    def scrape_videos(self):
        print("search video trigggered")
        channel_name = self.searchbar.currentText()
        for id, name in self.channels.items():
            if name == channel_name:
                print(name, id)
                break
        videos = Videos()
        self.video_ids = videos.search_video(id)
        print(self.video_ids)

    def scrape_transcription(self):
        print("transcription triggered")
        transcription = Transcription()
        self.transcriptions = {}
        for id in self.video_ids:
            transcripts = transcription.get_transcript(id)
            self.transcriptions[id] = transcripts
        print(self.transcriptions)