import os
import sys
import time

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QStackedWidget, QFrame, QWidget,
    QVBoxLayout, QHBoxLayout, QToolButton
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QSize, QTimer

# ---- Import Pages ----
from .Homepage import Home
from .VideoPage import Video
from .CommentPage import Comment
from .TranscriptPage import Transcript
from .SettingsPage import Settings
from .SplashScreen import SplashScreen

from Data.DatabaseManager import DatabaseManager
from utils.Logger import logger

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
        logger.info("MainWindow initialization started.")
        super().__init__()

        # Base dir and icon setup
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.base_dir = os.path.dirname(base_dir)
        icon_path = os.path.join(self.base_dir, "assets", "icon", "StaTube.ico")
        startup_img_path = os.path.join(self.base_dir, "assets", "StaTube.png")
        gif_path = os.path.join(self.base_dir, "assets", "splash", "loading.gif")
        logger.debug(f"Resolved application base directory: {self.base_dir}")
        logger.debug(f"Using icon path: {icon_path}")

        self.setWindowTitle("StaTube - YouTube Data Analysis Tool")
        self.setWindowIcon(QIcon(icon_path))
        # Initial geometry (window can be resized later)
        self.setGeometry(500, 200, 1000, 700)

        # Placeholder central widget until UI is fully ready
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Create stacked widget (pages will be added later in setup_ui)
        self.stack = QStackedWidget()
        self.splash = SplashScreen(parent=self, img_path=startup_img_path)

        # Sidebar button list
        self.sidebar_buttons = []

    def finish_initialization(self):
        logger.info("Starting final initialization sequence.")

        self.splash.update_status("Loading theme...")
        self.load_stylesheet()
        self.splash.set_progress(40)

        self.splash.update_status("Connecting database...")
        db = DatabaseManager()
        app_state.db = db
        self.splash.set_progress(70)

        self.splash.update_status("Building UI layout...")
        self.setup_ui()
        self.splash.set_progress(95)

        self.splash.update_status("Startup complete")


    # ---------- Stylesheet ----------
    def load_stylesheet(self):
        """
        Load and apply QSS stylesheet.
        """
        try:
            # For Nuitka onefile builds, use sys.argv[0]
            if getattr(sys, 'frozen', False):
                # Running as compiled executable
                base_dir = os.path.dirname(sys.argv[0])
            else:
                # Running as script
                base_dir = os.path.dirname(os.path.abspath(__file__))
                base_dir = os.path.dirname(base_dir)  # Go up to project root

            qss_path = os.path.join(base_dir, "UI", "Style.qss")
            logger.debug(f"Attempting to load QSS stylesheet from: {qss_path}")

            with open(qss_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())

            logger.info("Stylesheet loaded successfully.")

        except FileNotFoundError:
            logger.warning(f"Stylesheet not found at {qss_path}")
        except Exception as e:
            logger.exception("Error loading stylesheet:")

    # ---------- UI Setup ----------
    def setup_ui(self):
        """
        Setup the main UI once all startup tasks are done.
        """
        logger.info("Setting up main UI components...")
        # Root layout for central widget
        main_layout = QHBoxLayout(self.central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Sidebar frame
        logger.debug("Sidebar navigation buttons initialized.")
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(80)
        side_layout = QVBoxLayout(self.sidebar)
        side_layout.setAlignment(Qt.AlignCenter)
        side_layout.setContentsMargins(20, 0, 0, 0)
        side_layout.setSpacing(25)

        # Icons path
        icon_path = os.path.join(self.base_dir, "assets", "icon", "light")

        # Create buttons
        self.home_btn = QToolButton()
        self.video_btn = QToolButton()
        self.transcript_btn = QToolButton()
        self.comment_btn = QToolButton()
        self.settings_btn = QToolButton()

        buttons_config = [
            (self.home_btn, "light_home.ico", "Home"),
            (self.video_btn, "light_video.ico", "Videos"),
            (self.transcript_btn, "light_transcript.ico", "Transcription Analysis"),
            (self.comment_btn, "light_comment.ico", "Comment Analysis"),
        ]

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

        # Add sidebar + stack
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.stack, stretch=1)

        # Add pages
        self.homepage = Home(self)
        self.video_page = Video(self)
        self.transcript_page = Transcript(self)
        self.comment_page = Comment(self)
        self.settings_page = Settings(self)

        self.stack.addWidget(self.homepage)
        self.stack.addWidget(self.video_page)
        self.stack.addWidget(self.transcript_page)
        self.stack.addWidget(self.comment_page)
        logger.debug("All pages instantiated and added to QStackedWidget.")

        # Default page
        self.switch_page(0)
        if self.sidebar_buttons:
            self.sidebar_buttons[0].setChecked(True)

        # Cross-page signals
        self.homepage.home_page_scrape_video_signal.connect(self.switch_and_scrape_video)
        self.video_page.video_page_scrape_transcript_signal.connect(self.switch_and_scrape_transcripts)
        self.video_page.video_page_scrape_comments_signal.connect(self.switch_and_scrape_comments)
        logger.debug("Cross-page signals connected.")
        logger.info("Main UI fully constructed.")


    # ---------- Sidebar navigation ----------
    def switch_page(self, index: int):
        """
        Switches to the specified page index.
        """
        logger.debug(f"Switching to page index: {index}")
        self.stack.setCurrentIndex(max(0, index))

    def switch_and_scrape_video(self, scrape_shorts: bool = False):
        """
        Switches to the video page and scrapes videos.
        """
        if len(self.sidebar_buttons) >= 2:
            self.sidebar_buttons[0].setChecked(False)
            self.sidebar_buttons[1].setChecked(True)
        self.switch_page(1)
        # Add a small delay to ensure page switch completes before showing splash
        QTimer.singleShot(50, lambda: self.video_page.video_page_scrape_video_signal.emit(scrape_shorts))

    def switch_and_scrape_transcripts(self):
        """
        Switches to the transcript page and scrapes transcripts.
        """
        if len(self.sidebar_buttons) >= 3:
            self.sidebar_buttons[1].setChecked(False)
            self.sidebar_buttons[2].setChecked(True)
        self.switch_page(2)
        self.transcript_page.transcript_page_scrape_transcripts_signal.emit()

    def switch_and_scrape_comments(self):
        """
        Switches to the comment page and scrapes comments.
        """
        if len(self.sidebar_buttons) >= 4:
            self.sidebar_buttons[2].setChecked(False)
            self.sidebar_buttons[3].setChecked(True)
        self.switch_page(3)
        self.comment_page.comment_page_scrape_comments_signal.emit()

    # ---------- Close Event ----------
    def closeEvent(self, event):
        """
        Handle window close event (cleanup if needed).
        """
        # If you need to close DB connections or save state, do it here.
        super().closeEvent(event)


# Entry Point
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
