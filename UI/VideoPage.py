from PySide6 import QtCore
from PySide6.QtWidgets import QWidget, QLabel, QGridLayout, QPushButton
from PySide6.QtCore import QThread, Signal

from Backend.ScrapeVideo import VideoWorker
from UI.SplashScreen import SplashScreen
from utils.AppState import app_state

class Video(QWidget):
    videos: dict = None
    video_url: dict = None
    live: dict = None
    shorts: dict = None
    content: dict = None

    def __init__(self, parent=None):
        super(Video, self).__init__(parent)
        self.mainwindow = parent
        self.db = app_state.db
        
        # Initialize splash screen (but don't show it yet)
        self.splash = None
        
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
        
        # Show splash screen
        self.show_splash_screen()
        
        # Create and start worker thread
        self.worker_thread = QThread()
        self.worker = VideoWorker(channel_id, channel_url)
        self.worker.moveToThread(self.worker_thread)
        
        # Connect signals
        self.worker_thread.started.connect(self.worker.fetch_video_urls)
        self.worker.progress_updated.connect(self.update_splash_progress)
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        
        # Start the thread
        self.worker_thread.start()

    def show_splash_screen(self):
        """Show the splash screen in the main thread"""
        self.splash = SplashScreen()
        self.splash.set_title("Scraping Videos...")
        self.splash.update_status("Starting...")
        self.splash.show()

    def update_splash_progress(self, message):
        """Update splash screen progress (called from main thread via signal)"""
        if self.splash:
            self.splash.update_status(message)

    def on_worker_finished(self):
        """Clean up when worker is finished"""
        if self.splash:
            self.splash.close()
            self.splash = None
        print("Video scraping completed!")