from PySide6.QtWidgets import (
    QApplication, QMainWindow, QStackedWidget, QFrame, QWidget,
    QVBoxLayout, QHBoxLayout, QToolButton
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QSize, QThread
import os

from .Homepage import Home
from .VideoPage import Video
from .CommentPage import Comment
from .TranscriptPage import Transcript
from .SettingsPage import Settings
from .SplashScreen import InitiateProxy
from utils.AppState import proxy_thread

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YTA")
        self.setGeometry(500, 200, 500, 300)
        
        # ---- Setup threading properly ----
        initiate_proxy = InitiateProxy()
        return_value = initiate_proxy.start()

        proxy_thread.start()

        # Central container and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Stacked widget
        self.stack = QStackedWidget()

        # setup sidebar
        self.setupsidebar()

        # Setup pages
        self.homepage = Home(self)
        self.video_page = Video(self)
        self.comment_page = Comment(self)
        self.transcript_page = Transcript(self)
        self.settings_page = Settings(self)

        self.stack.addWidget(self.homepage)
        self.stack.addWidget(self.video_page)
        self.stack.addWidget(self.comment_page)
        self.stack.addWidget(self.transcript_page)
        self.stack.addWidget(self.settings_page)

        self.switch_page(-1)
        self.sidebar_buttons[0].setChecked(True)

    def switch_page(self, index):
        if index > 0:
            self.stack.setCurrentIndex(index)
        else:
            self.stack.setCurrentIndex(0)

    def setupsidebar(self):
        main_layout = QHBoxLayout(self.central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Sidebar
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(80)
        side_layout = QVBoxLayout(self.sidebar)
        side_layout.setAlignment(Qt.AlignCenter)
        side_layout.setContentsMargins(20, 0, 0, 0)
        side_layout.setSpacing(25)

        # Create icons + buttons
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

        self.sidebar_buttons = []
        for i, (filename, tooltip) in enumerate(icons):
            icon_file = os.path.join(icon_path, filename)
            btn = QToolButton()
            btn.setIcon(QIcon(icon_file))
            btn.setIconSize(QSize(28, 28))
            btn.setToolTip(tooltip)
            btn.setCheckable(True)
            btn.setAutoExclusive(True)
            btn.clicked.connect(lambda checked, idx=i: self.switch_page(idx))
            side_layout.addWidget(btn)
            self.sidebar_buttons.append(btn)

        # Add sidebar + stacked widget to main layout
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.stack, stretch=1)

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
