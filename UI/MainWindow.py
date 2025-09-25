from PySide6 import QtCore, QtGui
from PySide6.QtWidgets import (QApplication, QMainWindow, QStackedWidget, QWidget, 
                               QLineEdit, QListWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QListWidgetItem)
from PySide6.QtCore import Qt
import threading
import time
import traceback

from Backend.ScrapeChannel import Search
from Backend.ScrapeVideo import Videos
from Backend.ScrapeTranscription import Transcription
from Data.CacheManager import CacheManager
from utils.Proxy import Proxy

class MainWindow(QMainWindow):
    results_ready = QtCore.Signal(list)
    videos = {}
    video_url = [] #temp
    live = {}
    shorts = {}
    content = {}

    def __init__(self):
        super(MainWindow, self).__init__()

        self.top_panel = QWidget()
        self.bottom_panel = QWidget()
        self.central_layout = QVBoxLayout()
        self.central_widget = QStackedWidget()
        self.cache = CacheManager()
        
        # Replace ComboBox with LineEdit and ListWidget
        self.searchbar = QLineEdit()
        self.dropdown_list = QListWidget()
        
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
        
        # Setup search components
        self.searchbar.setPlaceholderText("Search")
        self.searchbar.textChanged.connect(self.reset_search_timer)
        self.dropdown_list.hide()  # Initially hidden
        self.dropdown_list.itemClicked.connect(self.on_item_selected)
        
        # Override key press to handle navigation
        #self.searchbar.keyPressEvent = self.handle_key_press
        
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
        self.top_layout.addWidget(self.dropdown_list)  # Add dropdown list
        self.top_layout.addWidget(self.scrap_video_button)
        self.top_layout.addWidget(self.scrape_transcription_button)
        self.top_panel.setLayout(self.top_layout)
        self.top_panel.show()
        Proxy()
    
    def setupbottom(self):
        self.bottom_layout = QVBoxLayout()
        self.bottom_panel.setLayout(self.bottom_layout)
        self.bottom_panel.show()

    def reset_search_timer(self):
        self.search_timer.start(100)

    def on_item_selected(self, item):
        """Handle item selection from dropdown"""
        if item:
            self.searchbar.blockSignals(True)
            selected_text = item.text()
            self.searchbar.setText(selected_text)
            #self.dropdown_list.hide()
            # Return focus to input after selection
            QtCore.QTimer.singleShot(10, lambda: self.searchbar.setFocus())
            self.searchbar.blockSignals(False)

    def search_thread(self, query):
        print("search channel thread triggered")
        cached_channels = self.cache.load("channels_cache")
        if query in cached_channels:
            print("Using cached channel results")
            self.channels = cached_channels[query]
        else:
            search = Search()
            self.channels = search.search_channel(query)
            cached_channels[query] = self.channels
            self.cache.save("channels_cache", cached_channels)

        self.channel_name = [item.get('title') for key, item in self.channels.items()]
        self.results_ready.emit(self.channel_name)

    def update_results(self, channels):
        """Update dropdown list with search results"""
        text = self.searchbar.text()
        
        # Clear and populate dropdown list
        self.dropdown_list.clear()
        
        if channels:
            for channel in channels:
                item = QListWidgetItem(channel)
                self.dropdown_list.addItem(item)
            
            self.dropdown_list.show()
        else:
            self.dropdown_list.hide()
        
        # Keep focus on search input
        self.searchbar.setFocus()
        
    def search_keyword(self):
        try:
            if self.search_thread_instance and self.search_thread_instance.is_alive():
                self.stop_event.set()
                self.search_thread_instance.join(timeout=0.1)

            self.stop_event.clear()

            query = self.searchbar.text()
            if query:
                self.search_thread_instance = threading.Thread(target=self.search_thread, daemon=True, args=(query,))
                self.search_thread_instance.start()
            else:
                self.dropdown_list.hide()
        
        except Exception as e:
            traceback.print_exc()
            print(e)

    def scrape_videos(self):
        print("search video triggered")
        channel_name = self.searchbar.text()
        for id, val in self.channels.items():
            if val['title'] == channel_name:
                channel_url = val['url']
                channel_id = id
                break

        cached_videos = self.cache.load("videos_cache")
        if channel_id in cached_videos:
            print("Using cached videos")
            self.channel_id = channel_id
            self.content = cached_videos[channel_id]
        else:
            #fetch proxy from pool
            videos = Videos()
            self.content = videos.fetch_video_urls(channel_url)
            cached_videos[channel_id] = self.content
            self.channel_id = channel_id
            self.cache.save("videos_cache", cached_videos)

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

            transcription = Transcription()
            print(self.channel_id)
            transcript_data = transcription.get_transcripts(video_url, self.channel_id, lang="en")

            if transcript_data:
                print(f"Transcript fetched and saved")
            else:
                print("Failed to fetch transcript.")

        except Exception as e:
            traceback.print_exc()
            print(f"Error while scraping transcription: {e}")

if __name__ == "__main__":
    app = QApplication()
    window = MainWindow()
    window.show()
    app.exec()