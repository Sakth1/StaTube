import os
import sys
import time

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QIcon, QColor
from PySide6.QtCore import Qt, QThread, Signal, QObject

from qfluentwidgets import (
    MSFluentWindow,
    NavigationItemPosition,
    setTheme,
    setThemeColor,
    Theme,
    FluentIcon as FIF,  # not used yet, but handy if you want built-in icons later
)

# ---- Import Pages ----
from .Homepage import Home
from .VideoPage import Video
from .CommentPage import Comment
from .TranscriptPage import Transcript
from .SettingsPage import Settings
from .SplashScreen import SplashScreen

from Data.DatabaseManager import DatabaseManager
from utils.CheckInternet import Internet
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
            if attempt == 0:
                self.status_updated.emit("Checking internet connection...")
            elif attempt == 1:
                self.status_updated.emit("Still checking your connection...")
            else:
                self.status_updated.emit("Almost there, verifying network...")

            connected = internet.check_internet()
            if connected:
                break

            time.sleep(self.retry_delay)

        self.finished.emit(bool(connected))


class MainWindow(MSFluentWindow):
    """
    Main window of the application using QFluentWidgets navigation shell.
    """

    def __init__(self):
        super().__init__()

        # ---- Paths & icons ----
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.base_dir = os.path.dirname(base_dir)
        icon_path = os.path.join(self.base_dir, "icon", "youtube.ico")

        # ---- Fluent theme ----
        setTheme(Theme.DARK)
        # Accent color close to YouTube red
        setThemeColor(QColor("#FF3B3B"))

        self.setWindowTitle("StaTube - YouTube Data Analysis Tool")
        self.setWindowIcon(QIcon(icon_path))
        self.resize(1000, 700)

        # Alias old attribute name so other modules can still use self.stack if needed
        # MSFluentWindow already has a stackedWidget for its interfaces
        self.stack = self.stackedWidget

        # Route keys used by navigationInterface
        self.route_keys = {
            "home": "homeInterface",
            "video": "videoInterface",
            "transcript": "transcriptInterface",
            "comment": "commentInterface",
            "settings": "settingsInterface",
        }

        # ---- Splash screen ----
        gif_path = os.path.join(self.base_dir, "assets", "splash", "loading.gif")
        self.splash = SplashScreen(parent=self, gif_path=gif_path)
        self.splash.set_title("StaTube - YouTube Data Analysis Tool")
        self.splash.update_status("Starting application...")
        self.splash.show()

        # Async startup
        self.start_startup_sequence()

    # ---------- Startup sequence ----------

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
                QApplication.instance().quit()
                return

            # If user chose to continue offline, just carry on to setup
            self.splash.update_status("Continuing in offline mode...")

        else:
            self.splash.update_status("Internet connection established. Preparing application...")

        # Now perform remaining init (DB, pages, nav)
        self.finish_initialization()

    def finish_initialization(self):
        """
        Perform remaining initialization once startup checks are done.
        """
        # Initialize database and store in app_state
        db: DatabaseManager = DatabaseManager()
        app_state.db = db

        # Setup the Fluent interfaces & nav shell
        self.init_interfaces()
        self.init_window_shell()

        # Smooth fade-out of the splash, then main window is ready
        self.splash.fade_and_close(duration_ms=700)

        # Debug log
        print("[DEBUG] Main UI (QFluentWidgets) initialized successfully")

    # ---------- Fluent window / navigation ----------

    def init_interfaces(self):
        """
        Create page widgets and register them as sub-interfaces.
        """
        # Instantiate pages
        self.homepage = Home(self)
        self.video_page = Video(self)
        self.transcript_page = Transcript(self)
        self.comment_page = Comment(self)
        self.settings_page = Settings(self)

        # Give each page a unique objectName (used by QFluent navigation)
        self.homepage.setObjectName(self.route_keys["home"])
        self.video_page.setObjectName(self.route_keys["video"])
        self.transcript_page.setObjectName(self.route_keys["transcript"])
        self.comment_page.setObjectName(self.route_keys["comment"])
        self.settings_page.setObjectName(self.route_keys["settings"])

        # Icon path
        light_icon_path = os.path.join(self.base_dir, "assets", "icon", "light")

        # Register sub-interfaces with Fluent navigation
        self.addSubInterface(
            self.homepage,
            QIcon(os.path.join(light_icon_path, "light_home.ico")),
            "Home",
            position=NavigationItemPosition.TOP,
        )

        self.addSubInterface(
            self.video_page,
            QIcon(os.path.join(light_icon_path, "light_video.ico")),
            "Videos",
            position=NavigationItemPosition.TOP,
        )

        self.addSubInterface(
            self.transcript_page,
            QIcon(os.path.join(light_icon_path, "light_transcript.ico")),
            "Transcription Analysis",
            position=NavigationItemPosition.TOP,
        )

        self.addSubInterface(
            self.comment_page,
            QIcon(os.path.join(light_icon_path, "light_comment.ico")),
            "Comment Analysis",
            position=NavigationItemPosition.TOP,
        )

        self.addSubInterface(
            self.settings_page,
            QIcon(os.path.join(light_icon_path, "light_settings.ico")),
            "Settings",
            position=NavigationItemPosition.BOTTOM,
        )

        # Cross-page signals (same logic as before, just different switching)
        self.homepage.home_page_scrape_video_signal.connect(self.switch_and_scrape_video)
        self.video_page.video_page_scrape_transcript_signal.connect(self.switch_and_scrape_transcripts)
        self.video_page.video_page_scrape_comments_signal.connect(self.switch_and_scrape_comments)

    def init_window_shell(self):
        """
        Final MSFluentWindow tweaks (size, centering, default page).
        """
        # Center window on primary screen
        screen_geo = QApplication.primaryScreen().availableGeometry()
        self.move(
            screen_geo.center().x() - self.width() // 2,
            screen_geo.center().y() - self.height() // 2,
        )

        # Default interface is home
        self.switch_to_interface(self.homepage)

    # ---------- Helper to switch interfaces programmatically ----------

    def switch_to_interface(self, widget: QObject):
        """
        Switch both the stacked widget and navigation selection to `widget`.
        """
        if widget is None:
            return

        try:
            # Switch stack
            self.stackedWidget.setCurrentWidget(widget)

            # Sync nav selection
            if hasattr(self, "navigationInterface"):
                route = widget.objectName()
                if route:
                    self.navigationInterface.setCurrentItem(route)
        except Exception as e:
            print(f"[WARN] Failed to switch interface: {e}")

    # ---------- Cross-page helpers (kept from old API) ----------

    def switch_and_scrape_video(self, scrape_shorts: bool = False):
        """
        Switches to the video page and scrapes videos.
        """
        self.switch_to_interface(self.video_page)
        # Trigger existing signal that VideoPage already listens to
        self.video_page.video_page_scrape_video_signal.emit(scrape_shorts)

    def switch_and_scrape_transcripts(self):
        """
        Switches to the transcript page and scrapes transcripts.
        """
        self.switch_to_interface(self.transcript_page)
        self.transcript_page.transcript_page_scrape_transcripts_signal.emit()

    def switch_and_scrape_comments(self):
        """
        Switches to the comment page and scrapes comments.
        """
        self.switch_to_interface(self.comment_page)
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

    # Recommended HiDPI settings for QFluentWidgets
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())
