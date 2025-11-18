from PySide6.QtWidgets import (
    QApplication, QMainWindow, QStackedWidget, QFrame, QWidget,
    QVBoxLayout, QHBoxLayout, QToolButton
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QSize, QThread, QEvent
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

# ---- Import AppState ----
from utils.AppState import app_state


class MainWindow(QMainWindow):
    """
    Main window of the application.
    """
    def __init__(self):
        """
        Initializes the main window.
        """
        super().__init__()
        self.load_stylesheet()
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.base_dir = os.path.dirname(base_dir)
        icon_path = os.path.join(self.base_dir, "icon", "youtube.ico")
        
        db: DatabaseManager = DatabaseManager()
        app_state.db = db
        self.setWindowTitle("StaTube - YouTube Data Analysis Tool")
        self.setWindowIcon(QIcon(icon_path))
        self.setGeometry(500, 200, 500, 300)
        
        # Show splash screen
        self.splash = SplashScreen(parent=self)
        self.splash.set_title("StaTube - YouTube Data Analysis Tool")
        self.splash.update_status("Initializing ...")
        self.splash.show()
        
        self.initialize()

    def load_stylesheet(self):
        """
        Load and apply QSS stylesheet.
        """
        try:
            # For Nuitka onefile builds, use __file__ to get the correct path
            if getattr(sys, 'frozen', False):
                # Running as compiled executable
                base_dir = os.path.dirname(sys.argv[0])
            else:
                # Running as script
                base_dir = os.path.dirname(os.path.abspath(__file__))
                base_dir = os.path.dirname(base_dir)  # Go up to project root
            
            qss_path = os.path.join(base_dir, "UI", "Style.qss")
            
            with open(qss_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
                
        except FileNotFoundError:
            print(base_dir)
            print(f"Warning: Stylesheet not found at {qss_path}")
        except Exception as e:
            print(f"Error loading stylesheet: {e}")

    def initialize(self):
        """
        Initialization complete! Launching app...
        """
        self.splash.update_status("Initialization complete! Launching app...")
        self.splash.close()
        self.setup_ui()
        print("[DEBUG] Main UI initialized successfully")

    def setup_ui(self):
        """
        Setup the main UI.
        """
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
        self.transcript_page = Transcript(self)
        self.comment_page = Comment(self)
        self.settings_page = Settings(self)

        # Add to stacked layout
        self.stack.addWidget(self.homepage)
        self.stack.addWidget(self.video_page)
        self.stack.addWidget(self.transcript_page)
        self.stack.addWidget(self.comment_page)
        self.stack.addWidget(self.settings_page)

        # Default page
        self.switch_page(0)
        self.sidebar_buttons[0].setChecked(True)

        self.homepage.home_page_scrape_video_signal.connect(self.switch_and_scrape_video)
        self.video_page.video_page_scrape_transcript_signal.connect(self.switch_and_scrape_transcripts)
        self.video_page.video_page_scrape_comments_signal.connect(self.switch_and_scrape_comments)
    
    # Sidebar navigation logic
    def switch_page(self, index: int):
        """
        Switches to the specified page index.
        
        :param index: Index of the page to switch to.
        """
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
        icon_path = os.path.join(self.base_dir, "assets", "icon", "light")

        # Create buttons individually
        self.home_btn = QToolButton()
        self.video_btn = QToolButton()
        self.transcript_btn = QToolButton()
        self.comment_btn = QToolButton()
        self.settings_btn = QToolButton()

        # Store in list with their configurations
        buttons_config = [
            (self.home_btn, "light_home.ico", "Home"),
            (self.video_btn, "light_video.ico", "Videos"),
            (self.transcript_btn, "light_transcript.ico", "Transcription Analysis"),
            (self.comment_btn, "light_comment.ico", "Comment Analysis"),
            (self.settings_btn, "light_settings.ico", "Settings")
        ]

        # Configure all buttons using loop
        self.sidebar_buttons = []
        for i, (btn, filename, tooltip) in enumerate(buttons_config):
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
        """
        Handle window close event.
        """
        pass
    
    def switch_and_scrape_video(self, scrape_shorts: bool = False):
        """
        Switches to the video page and scrapes videos.
        
        :param scrape_shorts: Whether to scrape shorts or not.
        """
        self.sidebar_buttons[0].setChecked(False)
        self.sidebar_buttons[1].setChecked(True)
        self.switch_page(1)
        self.video_page.video_page_scrape_video_signal.emit(scrape_shorts)

    def switch_and_scrape_transcripts(self):
        """
        Switches to the transcript page and scrapes transcripts.
        """
        self.sidebar_buttons[1].setChecked(False)
        self.sidebar_buttons[2].setChecked(True)
        self.switch_page(2)
        self.transcript_page.transcript_page_scrape_transcripts_signal.emit()

    def switch_and_scrape_comments(self):
        """
        Switches to the comment page and scrapes comments.
        """
        self.sidebar_buttons[2].setChecked(False)
        self.sidebar_buttons[3].setChecked(True)
        self.switch_page(3)
        self.comment_page.comment_page_scrape_comments_signal.emit()

# Entry Point
if __name__ == "__main__":
    app = QApplication(sys.argv)
    #app.setStyleSheet(open("UI/Style.qss").read())
    window = MainWindow()
    window.show()
    sys.exit(app.exec())