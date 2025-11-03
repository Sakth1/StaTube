from PySide6.QtWidgets import (
    QApplication, QMainWindow, QStackedWidget, QFrame, QWidget,
    QVBoxLayout, QHBoxLayout, QToolButton
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QSize, QThread
import threading
import os, sys

# ---- Import Pages ----
from .Homepage import Home
from .VideoPage import Video
from .CommentPage import Comment
from .TranscriptPage import Transcript
from .SettingsPage import Settings
from .SplashScreen import SplashScreen

from Data.DatabaseManager import DatabaseManager

# ---- Import Proxy and AppState ----
from utils.ProxyThread import ProxyThread
from utils.AppState import app_state


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        db = DatabaseManager()
        app_state.db = db
        self.setWindowTitle("YTA")
        self.setGeometry(500, 200, 500, 300)
        
        # Show splash screen before starting proxy thread
        self.splash = SplashScreen()
        self.splash.show()
        QApplication.processEvents()

        # Start Proxy Thread
        self.proxy_thread = ProxyThread()

        self.proxy_thread.proxy_ready.connect(self.on_proxy_ready, Qt.QueuedConnection)
        self.proxy_thread.proxy_status.connect(self.splash.update_status, Qt.QueuedConnection)

        print(f"[DEBUG] Connected signals — main thread id={threading.get_ident()}")

        self.proxy_thread.start()
        print("[DEBUG] Proxy thread started — waiting for signal.")


    def on_proxy_ready(self):
        print(f"[DEBUG] on_proxy_ready() received in thread {threading.get_ident()}")
        self.splash.update_status("Proxy initialization complete! Launching app...")
        self.splash.close()
        QApplication.processEvents()
        self.setup_ui()
        print("[DEBUG] Main UI initialized successfully")

    def setup_ui(self):
        """Setup the main UI after proxy is ready"""
        # Setup Main UI
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Create stacked widget
        self.stack = QStackedWidget()

        # Sidebar setup
        self.setupsidebar()
        
        # Add pages
        self.homepage = Home(self)
        self.video_page = Video(self)
        self.comment_page = Comment(self)
        self.transcript_page = Transcript(self)
        self.settings_page = Settings(self)

        # Add to stacked layout
        self.stack.addWidget(self.homepage)
        self.stack.addWidget(self.video_page)
        self.stack.addWidget(self.comment_page)
        self.stack.addWidget(self.transcript_page)
        self.stack.addWidget(self.settings_page)

        # Default page
        self.switch_page(0)
        self.sidebar_buttons[0].setChecked(True)
    
    # Sidebar navigation logic
    def switch_page(self, index):
        self.stack.setCurrentIndex(max(0, index))

    def setupsidebar(self):
        """
        Creates the left-side vertical toolbar with icons for navigation.
        """
        main_layout = QHBoxLayout(self.central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Sidebar frame
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(80)
        side_layout = QVBoxLayout(self.sidebar)
        side_layout.setAlignment(Qt.AlignCenter)
        side_layout.setContentsMargins(20, 0, 0, 0)
        side_layout.setSpacing(25)

        # Icons path
        base_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.dirname(base_dir)
        icon_path = os.path.join(base_dir, "assets", "icon", "light")

        icons = [
            ("light_home.ico", "Home"),
            ("light_video.ico", "Videos"),
            ("light_transcript.ico", "Transcription Analysis"),
            ("light_comment.ico", "Comment Analysis"),
            ("light_settings.ico", "Settings")
        ]

        # Create sidebar buttons
        self.sidebar_buttons = []
        for i, (filename, tooltip) in enumerate(icons):
            btn = QToolButton()
            btn.setIcon(QIcon(os.path.join(icon_path, filename)))
            btn.setIconSize(QSize(28, 28))
            btn.setToolTip(tooltip)
            btn.setCheckable(True)
            btn.setAutoExclusive(True)
            btn.clicked.connect(lambda checked, idx=i: self.switch_page(idx))
            side_layout.addWidget(btn)
            self.sidebar_buttons.append(btn)

        # Add sidebar + stack to layout
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.stack, stretch=1)

    def closeEvent(self, event):
        """Handle window close event"""
        if hasattr(self, 'proxy_thread'):
            self.proxy_thread.stop()
        event.accept()


# Entry Point
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())