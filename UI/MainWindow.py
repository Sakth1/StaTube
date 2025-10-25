from PySide6.QtWidgets import (
    QApplication, QMainWindow, QStackedWidget, QFrame, QWidget,
    QVBoxLayout, QHBoxLayout, QToolButton
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QSize, QThread
import threading

from UI.Homepage import Homepage
from .SplashScreen import ProxyThread

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YTA")
        self.setGeometry(500, 200, 500, 300)
        
        # ---- Setup threading properly ----
        self.proxy_thread = ProxyThread()
        self.proxy_thread.start()

        # Central container and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        main_layout = QHBoxLayout(self.central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Sidebar
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(80)
        side_layout = QVBoxLayout(self.sidebar)
        side_layout.setAlignment(Qt.AlignTop)
        side_layout.setContentsMargins(10, 20, 10, 20)
        side_layout.setSpacing(25)

        # Stacked widget
        self.stack = QStackedWidget()

        # Create icons + buttons
        icons = [
            ("Home", "Home"),
            ("videos", "Videos from selected channel"),
            ("TA", "Transcription Analysis"),
            ("CA", "Comment Analysis"),
            ("settings", "Settings")
        ]

        self.buttons = []
        for i, (icon_name, tooltip) in enumerate(icons):
            btn = QToolButton()
            btn.setText(icon_name)
            btn.setIconSize(QSize(28, 28))
            btn.setToolTip(tooltip)
            btn.setCheckable(True)
            btn.setAutoExclusive(True)
            btn.clicked.connect(lambda checked, idx=i: self.switch_page(idx))
            side_layout.addWidget(btn)
            self.buttons.append(btn)

        # Add sidebar + stacked widget to main layout
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.stack, stretch=1)

        # Setup pages
        self.homepage = Homepage(self)
        self.stack.addWidget(self.homepage)
        # TODO: add other pages here

        self.switch_page(-1)

    def switch_page(self, index):
        if index > 0:
            self.stack.setCurrentIndex(index)

        else:
            self.stack.setCurrentIndex(0)

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
