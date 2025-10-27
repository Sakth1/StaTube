from PySide6 import QtCore
from PySide6.QtWidgets import (QApplication, QMainWindow, QStackedWidget, QWidget, 
                               QLineEdit, QListWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QListWidgetItem, QCompleter, QGridLayout)
from PySide6.QtCore import Qt, QStringListModel, QSize
from PySide6.QtGui import QPixmap, QIcon
import threading
import time
import traceback

from Backend.ScrapeChannel import Search
from Backend.ScrapeVideo import Videos
from Backend.ScrapeTranscription import Transcription
from Data.DatabaseManager import DatabaseManager

class Home(QWidget):
    results_ready = QtCore.Signal(list)
    videos = {}
    video_url = []
    live = {}
    shorts = {}
    content = {}

    def __init__(self, parent: QMainWindow = None):
        super(Home, self).__init__(parent)

        self.mainwindow = parent

        self.top_panel = QWidget()
        self.central_layout = QVBoxLayout()
        self.central_widget = QStackedWidget()
        
        # Replace ComboBox with LineEdit and ListWidget
        self.searchbar = QLineEdit()
        self.select_button = QPushButton("Select")
        self.channel_list = QListWidget()
        self.model = QStringListModel()
        self.completer = QCompleter(self.model, self.searchbar)
        self.completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)
        self.searchbar.setCompleter(self.completer)
        self.searchbar.mousePressEvent = lambda event, e=self.searchbar.mousePressEvent: (e(event), self.completer.complete())
        self.searchbar.focusInEvent = lambda event, e=self.searchbar.focusInEvent: (e(event), self.completer.complete())

        self.completer_active = False

        self.search_timer = QtCore.QTimer()
        self.stop_event = threading.Event()
        self.search_thread_instance = None
        self.channels = None
        self.search_channel_button = QPushButton("Search")
        self.scrap_video_button = QPushButton("Scrape Video")
        self.scrape_transcription_button = QPushButton("screpe transcription")

        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.search_keyword)

        #self.top_layout = QGridLayout()
        #self.top_panel.setLayout(self.top_layout)
        #self.central_widget.addWidget(self.top_panel)
        
        # Setup search components
        self.searchbar.setPlaceholderText("Search")
        self.searchbar.textChanged.connect(self.reset_search_timer)
        self.completer.activated.connect(self.on_completer_activated)
        
        self.scrap_video_button.clicked.connect(self.scrape_videos)
        self.search_channel_button.clicked.connect(self.search_channel)
        self.scrape_transcription_button.clicked.connect(self.scrape_transcription)
        self.results_ready.connect(self.update_results)

        self.setupUi()
        self.initiatemodule()
        self.setLayout(self.central_layout)
        self.central_layout.addWidget(self.top_panel)
        self.main_widget = self.central_widget

    def on_completer_activated(self, text):
        """Handle completer selection"""
        self.completer_active = True
        self.search_timer.stop()  # Stop any pending search
        # Reset flag after a short delay
        QtCore.QTimer.singleShot(50, lambda: setattr(self, 'completer_active', False))
    
    def setupUi(self):
        """
        Set up the user interface of the main window.
        """
        self.mainwindow.setGeometry(500, 200, 500, 300)
        self.setuptop()

    def initiatemodule(self):
        self.db = DatabaseManager()

    def setuptop(self):
        self.top_layout = QGridLayout()
        self.top_panel.setLayout(self.top_layout)
        self.top_layout.addWidget(self.searchbar, 0, 0, alignment=Qt.AlignTop)
        self.top_layout.addWidget(self.search_channel_button, 0, 1)
        self.top_layout.addWidget(self.select_button, 2, 0, 1, 2, alignment=Qt.AlignBottom)
        self.top_panel.show()

    def reset_search_timer(self):
        if not self.completer_active:
            self.search_timer.start(100)

    def on_item_selected(self, item):
        """Handle item selection from dropdown"""
        if item:
            self.searchbar.blockSignals(True)
            selected_text = item.text()
            self.searchbar.setText(selected_text)
            # Return focus to input after selection
            QtCore.QTimer.singleShot(10, lambda: self.searchbar.setFocus())
            self.searchbar.blockSignals(False)

    def search_thread(self, query, final=False):
        print("search channel thread triggered")
        
        search = Search(self.db)  # Pass db instance
        if final:
            self.channels = search.search_channel(query, limit=20)
        else:
            self.channels = search.search_channel(query, limit=6)

        self.channel_name = [item.get('title') for key, item in self.channels.items()]

        if not final:
            self.results_ready.emit(self.channel_name)
        else:
            self.update_channel_list()
            
    def update_results(self, channels):
        """Update dropdown list with search results"""
        text = self.searchbar.text()
        
        # Clear and populate dropdown list
        
        if channels:
            for channel in channels:
                item = QListWidgetItem(channel)
                self.model.setStringList(channels)
                self.completer.complete()
    
    def update_channel_list(self):
        self.channel_list.clear()
        for channel_id, channel_info in self.channels.items():
            inf = self.db.fetch("CHANNEL", "channel_id=?", (channel_id,))
            sub_count = inf[0].get("sub_count")
            channel_name = inf[0].get("name")
            icon_label = QIcon(inf[0].get("profile_pic"))
            text_label = f'\n{channel_name}\n{sub_count}\n'
            item = QListWidgetItem(icon_label, text_label)
            self.channel_list.addItem(item)
        self.channel_list.setIconSize(QSize(32, 32))
        self.top_layout.addWidget(self.channel_list, 1, 0, 1, 2)

    def search_keyword(self, final=False):
        try:
            if self.search_thread_instance and self.search_thread_instance.is_alive():
                self.stop_event.set()
                self.search_thread_instance.join(timeout=0.1)

            self.stop_event.clear()

            query = self.searchbar.text()
            if query:
                self.search_thread_instance = threading.Thread(target=self.search_thread, daemon=True, args=(query,final))
                self.search_thread_instance.start()
        
        except Exception as e:
            traceback.print_exc()
            print(e)

    def search_channel(self):
        self.search_keyword(True)

    def scrape_videos(self):
        print("search video triggered")
        channel_name = self.searchbar.text()
        for id, val in self.channels.items():
            if val['title'] == channel_name:
                channel_url = val['url']
                channel_id = id
                break

        # Remove cache logic and use database directly
        videos = Videos(self.db)  # Pass db instance
        self.content = videos.fetch_video_urls(channel_id, channel_url)
        self.channel_id = channel_id

        print("Videos Fetched")

        if 'video_url' in self.content:
            self.video_url = self.content.get('video_url')

    def scrape_transcription(self):
        """
        Scrape transcription for the first video in self.video_url
        and store it as JSON in Data/.
        """
        if not self.video_url:
            print("No video URL available. Please scrape videos first.")
            return

        try:
            video_url = self.video_url[:1]  # Take the first video for now
            print(f"Fetching transcript for: {video_url}")

            transcription = Transcription(self.db)  # Already uses DatabaseManager internally
            transcript_data = transcription.get_transcripts(video_url, self.channel_id, lang="en")

            if transcript_data:
                print(f"Transcript fetched and saved")
            else:
                print("Failed to fetch transcript.")

        except Exception as e:
            traceback.print_exc()
            print(f"Error while scraping transcription: {e}")

