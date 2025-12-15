import os
import sys
import time

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QStackedWidget, QFrame, QWidget,
    QVBoxLayout, QHBoxLayout, QToolButton,
    QMenuBar, QMenu, QToolBar,
    QMessageBox, QDialog, QLabel, QPushButton
)
from PySide6.QtGui import QIcon, QDesktopServices, QAction
from PySide6.QtCore import Qt, QSize, QTimer, QUrl

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
        logger.info("MainWindow initialization started.")
        super().__init__()

        # Base dir and icon setup
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.base_dir = os.path.dirname(base_dir)
        icon_path = os.path.join(self.base_dir, "assets", "icon", "StaTube.ico")
        startup_img_path = os.path.join(self.base_dir, "assets", "StaTube.png")

        self.setWindowTitle("StaTube - YouTube Data Analysis Tool")
        self.setWindowIcon(QIcon(icon_path))
        self.setGeometry(500, 200, 1000, 700)

        # Central widget placeholder
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Stack & splash
        self.stack = QStackedWidget()
        self.splash = SplashScreen(parent=self, img_path=startup_img_path)

        # Sidebar buttons
        self.sidebar_buttons = []

        # Menu + toolbar
        self.setup_menu_and_toolbar()

    # ---------- Final init ----------
    def finish_initialization(self):
        logger.info("Starting final initialization sequence.")

        self.splash.update_status("Loading theme...")
        self.load_stylesheet()
        self.splash.set_progress(40)

        self.splash.update_status("Connecting database...")
        app_state.db = DatabaseManager()
        self.splash.set_progress(70)

        self.splash.update_status("Building UI layout...")
        self.setup_ui()
        self.splash.set_progress(95)

        self.splash.update_status("Startup complete")

    # ---------- Stylesheet ----------
    def load_stylesheet(self):
        try:
            if getattr(sys, 'frozen', False):
                base_dir = os.path.dirname(sys.argv[0])
            else:
                base_dir = os.path.dirname(os.path.abspath(__file__))
                base_dir = os.path.dirname(base_dir)

            qss_path = os.path.join(base_dir, "UI", "Style.qss")
            with open(qss_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())

        except Exception:
            logger.exception("Error loading stylesheet")

    # ---------- Menu & Toolbar ----------
    def setup_menu_and_toolbar(self):
        menubar = self.menuBar()

        # File
        file_menu = menubar.addMenu("File")
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Settings
        settings_menu = menubar.addMenu("Settings")
        settings_action = QAction("Open Settings", self)
        settings_action.triggered.connect(self.open_settings_page)
        settings_menu.addAction(settings_action)

        # Help
        help_menu = menubar.addMenu("Help")
        docs_action = QAction("Documentation", self)
        docs_action.triggered.connect(self.open_docs)
        help_menu.addAction(docs_action)

        # About
        about_menu = menubar.addMenu("About")
        about_action = QAction("About StaTube", self)
        about_action.triggered.connect(self.show_about_dialog)
        about_menu.addAction(about_action)

        # Toolbar (text-only)
        toolbar = QToolBar("Main Toolbar", self)
        toolbar.setMovable(False)
        self.addToolBar(Qt.TopToolBarArea, toolbar)

        toolbar.addAction(settings_action)
        toolbar.addSeparator()
        toolbar.addAction(docs_action)
        toolbar.addSeparator()
        toolbar.addAction(about_action)

    # ---------- UI Setup ----------
    def setup_ui(self):
        main_layout = QHBoxLayout(self.central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Sidebar
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(80)
        side_layout = QVBoxLayout(self.sidebar)
        side_layout.setAlignment(Qt.AlignCenter)
        side_layout.setContentsMargins(20, 0, 0, 0)
        side_layout.setSpacing(25)

        icon_path = os.path.join(self.base_dir, "assets", "icon", "light")

        self.home_btn = QToolButton()
        self.video_btn = QToolButton()
        self.transcript_btn = QToolButton()
        self.comment_btn = QToolButton()

        buttons_config = [
            (self.home_btn, "light_home.ico", "Home"),
            (self.video_btn, "light_video.ico", "Videos"),
            (self.transcript_btn, "light_transcript.ico", "Transcription Analysis"),
            (self.comment_btn, "light_comment.ico", "Comment Analysis"),
        ]

        self.sidebar_buttons.clear()
        for i, (btn, icon, tooltip) in enumerate(buttons_config):
            btn.setIcon(QIcon(os.path.join(icon_path, icon)))
            btn.setIconSize(QSize(28, 28))
            btn.setToolTip(tooltip)
            btn.setCheckable(True)
            btn.setAutoExclusive(True)
            btn.clicked.connect(lambda _, idx=i: self.switch_page(idx))
            side_layout.addWidget(btn)
            self.sidebar_buttons.append(btn)

        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.stack, stretch=1)

        # Pages
        self.homepage = Home(self)
        self.video_page = Video(self)
        self.transcript_page = Transcript(self)
        self.comment_page = Comment(self)
        self.settings_page = Settings(self)

        self.stack.addWidget(self.homepage)
        self.stack.addWidget(self.video_page)
        self.stack.addWidget(self.transcript_page)
        self.stack.addWidget(self.comment_page)

        self.switch_page(0)
        self.sidebar_buttons[0].setChecked(True)

        # Signals
        self.homepage.home_page_scrape_video_signal.connect(self.switch_and_scrape_video)
        self.video_page.video_page_scrape_transcript_signal.connect(self.switch_and_scrape_transcripts)
        self.video_page.video_page_scrape_comments_signal.connect(self.switch_and_scrape_comments)

    # ---------- Navigation ----------
    def switch_page(self, index: int):
        self.stack.setCurrentIndex(index)

    def open_settings_page(self):
        if self.stack.indexOf(self.settings_page) == -1:
            self.stack.addWidget(self.settings_page)
        self.stack.setCurrentWidget(self.settings_page)

    def open_docs(self):
        QDesktopServices.openUrl(QUrl("https://github.com/your-username/StaTube"))

    def show_about_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("About StaTube")
        dialog.setFixedSize(420, 260)

        layout = QVBoxLayout(dialog)
        layout.setAlignment(Qt.AlignCenter)

        logo = QLabel()
        logo_path = os.path.join(self.base_dir, "assets", "StaTube.png")
        logo.setPixmap(QIcon(logo_path).pixmap(96, 96))
        logo.setAlignment(Qt.AlignCenter)

        title = QLabel("<b>StaTube</b>")
        title.setAlignment(Qt.AlignCenter)

        version = QLabel("Version 1.0.0")
        version.setAlignment(Qt.AlignCenter)

        desc = QLabel(
            "Desktop application for YouTube\n"
            "analytics, transcripts, and comments."
        )
        desc.setAlignment(Qt.AlignCenter)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)

        layout.addWidget(logo)
        layout.addWidget(title)
        layout.addWidget(version)
        layout.addWidget(desc)
        layout.addSpacing(10)
        layout.addWidget(close_btn)

        dialog.exec()

    # ---------- Cross-page helpers ----------
    def switch_and_scrape_video(self, scrape_shorts=False):
        self.sidebar_buttons[1].setChecked(True)
        self.switch_page(1)
        QTimer.singleShot(
            50,
            lambda: self.video_page.video_page_scrape_video_signal.emit(scrape_shorts)
        )

    def switch_and_scrape_transcripts(self):
        self.sidebar_buttons[2].setChecked(True)
        self.switch_page(2)
        self.transcript_page.transcript_page_scrape_transcripts_signal.emit()

    def switch_and_scrape_comments(self):
        self.sidebar_buttons[3].setChecked(True)
        self.switch_page(3)
        self.comment_page.comment_page_scrape_comments_signal.emit()
