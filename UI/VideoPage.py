from PySide6 import QtCore
from PySide6.QtWidgets import QWidget, QLabel, QGridLayout, QVBoxLayout, QHBoxLayout, QPushButton

from Backend.ScrapeVideo import Videos
from utils.AppState import app_state

class Video(QWidget):
    videos:dict = None
    video_url:dict = None
    live:dict = None
    shorts:dict = None
    content:dict = None

    def __init__(self, parent=None):
        super(Video, self).__init__(parent)
        self.mainwindow = parent
        self.db = app_state.db
        self.videos_scraper = Videos(self.db)

        self.channel_label = QLabel()
        self.central_layout = QGridLayout()
        self.scrap_video_button = QPushButton("Scrape Videos")
        self.scrap_video_button.clicked.connect(self.scrape_videos)

        self.central_layout.addWidget(self.channel_label, 0, 0, 1, 3, alignment=QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        self.central_layout.addWidget(self.scrap_video_button, 0, 1, 1, 1, alignment=QtCore.Qt.AlignRight | QtCore.Qt.AlignTop)
        
        app_state.channel_name_changed.connect(self.update_channel_label)
        self.update_channel_label(app_state.channel_name)

        self.setLayout(self.central_layout)

    def update_channel_label(self, name=None):
        self.channel_label.setText(f"Selected channel: {name or 'None'}")
        self.central_layout.replaceWidget(self.channel_label, self.channel_label)

    def scrape_videos(self):
        channel_name = app_state.channel_name
        channel_id = app_state.channel_id
        channel_url = app_state.channel_url

        if not channel_name or not channel_id or not channel_url:
            print("No channel selected")
            return
        
        self.content = self.videos_scraper.fetch_video_urls(channel_id, channel_url)

