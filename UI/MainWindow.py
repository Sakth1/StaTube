import os
import sys
import time

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QStackedWidget, QFrame, QWidget,
    QVBoxLayout, QHBoxLayout, QToolButton, QMessageBox
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QSize, QThread, Signal

# ---- Import Pages ----
from .Homepage import Home
from .VideoPage import Video
from .CommentPage import Comment
from .TranscriptPage import Transcript
from .SettingsPage import Settings
from .SplashScreen import SplashScreen

from Data.DatabaseManager import DatabaseManager
from utils.CheckInternet import Internet

# ---- Import AppState ----
from utils.AppState import app_state


class StartupWorker(QThread):
    """
    Background worker for startup tasks such as internet checks.
    Keeps UI responsive while doing blocking work.
    """
    status_updated = Signal(str)
    finished = Signal(bool)  # True = internet OK, False = still offline after retries

    def __init__(self, parent=None, max_retries: int = 3, retry_delay: float = 2.0):
        super().__init__(parent)
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def run(self) -> None:
        internet = Internet()
        connected = False

        for attempt in range(self.max_retries):
            # R2: general “soft” messages, not attempt counts
            if attempt == 0:
                self.status_updated.emit("Checking internet connection...")
            elif attempt == 1:
                self.status_updated.emit("Still checking your connection...")
            else:
                self.status_updated.emit("Almost there, verifying network...")

            connected = internet.check_internet()

            if connected:
                break

            # Small delay before retrying (background thread, so safe)
            time.sleep(self.retry_delay)

        self.finished.emit(bool(connected))


class MainWindow(QMainWindow):
    """
    Main window of the application.
    """
    def __init__(self):
        """
        Initializes the main window.
        """
        super().__init__()

        # Base dir and icon setup
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.base_dir = os.path.dirname(base_dir)
        icon_path = os.path.join(self.base_dir, "icon", "youtube.ico")

        self.setWindowTitle("StaTube - YouTube Data Analysis Tool")
        self.setWindowIcon(QIcon(icon_path))
        # Initial geometry (window can be resized later)
        self.setGeometry(500, 200, 1000, 700)

        # Placeholder central widget until UI is fully ready
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Create stacked widget (pages will be added later in setup_ui)
        self.stack = QStackedWidget()

        # Sidebar button list
        self.sidebar_buttons = []

        # Splash screen
        gif_path = os.path.join(self.base_dir, "assets", "splash", "loading.gif")
        self.splash = SplashScreen(parent=self, gif_path=gif_path)
        # self.splash = SplashScreen(parent=self)
        self.splash.set_title("StaTube - YouTube Data Analysis Tool")
        self.splash.update_status("Starting application...")
        self.splash.show()

        # Start asynchronous startup flow
        self.start_startup_sequence()

    # ---------- Startup Sequence ----------

    def start_startup_sequence(self):
        """
        Kick off background startup tasks (internet checks, etc.)
        while showing the splash screen.
        """
        self.startup_worker = StartupWorker(self, max_retries=3, retry_delay=2.0)
        self.startup_worker.status_updated.connect(self.splash.update_status)
        self.startup_worker.finished.connect(self.on_startup_finished)
        self.startup_worker.start()

    def on_startup_finished(self, connected: bool):
        """
        Called when the startup worker finishes internet checks.
        """
        if not connected:
            # Show dialog: Continue Offline / Quit
            self.splash.close()
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Connection Issue")
            msg.setText(
                "No internet connection detected.\n\n"
                "StaTube can continue in offline mode, but some features may not work.\n"
                "What would you like to do?"
            )
            continue_btn = msg.addButton("Continue Offline", QMessageBox.AcceptRole)
            quit_btn = msg.addButton("Quit", QMessageBox.RejectRole)
            msg.setDefaultButton(continue_btn)

            msg.exec()

            if msg.clickedButton() == quit_btn:
                # User chose to quit; close the app
                QApplication.instance().quit()
                return

            # If user chose to continue offline, just carry on to setup
            self.splash.update_status("Continuing in offline mode...")

        else:
            self.splash.update_status("Internet connection established. Preparing application...")

        # Now perform remaining init (DB, stylesheet, pages)
        self.finish_initialization()

    def finish_initialization(self):
        """
        Perform remaining initialization once startup checks are done.
        """
        # Load stylesheet
        self.load_stylesheet()

        # Initialize database and store in app_state
        db: DatabaseManager = DatabaseManager()
        app_state.db = db

        # Setup the full UI now
        self.setup_ui()

        # Smooth fade-out of the splash, then show main window fully ready
        self.splash.fade_and_close(duration_ms=700)

        # Debug log
        print("[DEBUG] Main UI initialized successfully")

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

            with open(qss_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())

        except FileNotFoundError:
            print(base_dir)
            print(f"Warning: Stylesheet not found at {qss_path}")
        except Exception as e:
            print(f"Error loading stylesheet: {e}")

    # ---------- UI Setup ----------

    def setup_ui(self):
        """
        Setup the main UI once all startup tasks are done.
        """
        # Root layout for central widget
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
            (self.settings_btn, "light_settings.ico", "Settings"),
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
        self.stack.addWidget(self.settings_page)

        # Default page
        self.switch_page(0)
        if self.sidebar_buttons:
            self.sidebar_buttons[0].setChecked(True)

        # Cross-page signals
        self.homepage.home_page_scrape_video_signal.connect(self.switch_and_scrape_video)
        self.video_page.video_page_scrape_transcript_signal.connect(self.switch_and_scrape_transcripts)
        self.video_page.video_page_scrape_comments_signal.connect(self.switch_and_scrape_comments)

    # ---------- Sidebar navigation ----------

    def switch_page(self, index: int):
        """
        Switches to the specified page index.
        """
        self.stack.setCurrentIndex(max(0, index))

    def switch_and_scrape_video(self, scrape_shorts: bool = False):
        """
        Switches to the video page and scrapes videos.
        """
        if len(self.sidebar_buttons) >= 2:
            self.sidebar_buttons[0].setChecked(False)
            self.sidebar_buttons[1].setChecked(True)
        self.switch_page(1)
        self.video_page.video_page_scrape_video_signal.emit(scrape_shorts)

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
