from PySide6.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout,
    QToolButton, QStackedWidget, QLabel, QFrame
)
from PySide6.QtCore import Qt
import sys, os

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Dashboard")
        self.resize(900, 600)

        main_layout = QHBoxLayout(self)

        # Sidebar
        sidebar = QVBoxLayout()
        sidebar_widget = QWidget()
        sidebar_widget.setObjectName("sidebar")
        sidebar_widget.setLayout(sidebar)

        self.pages = QStackedWidget()
        self.pages.addWidget(self.create_home_page())
        self.pages.addWidget(self.create_video_page())
        self.pages.addWidget(self.create_analysis_page())

        # Sidebar buttons
        for i, name in enumerate(["Home", "Videos", "Analysis"]):
            btn = QToolButton()
            btn.setText(name)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, index=i: self.pages.setCurrentIndex(index))
            sidebar.addWidget(btn)
        sidebar.addStretch()

        main_layout.addWidget(sidebar_widget, 1)
        main_layout.addWidget(self.pages, 4)

    def create_home_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        header = QLabel("Homepage")
        header.setObjectName("headerLabel")

        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.addWidget(QLabel("Video List Item"))

        layout.addWidget(header)
        layout.addWidget(card)
        return page

    def create_video_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel("Video Page"))
        return page

    def create_analysis_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel("Transcript Analysis"))
        return page


def load_stylesheet(app:QApplication, path):
    with open(path, "r") as f:
        app.setStyleSheet(f.read())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()

    qss_path = os.path.join(os.path.dirname(__file__), "styles/dark_theme.qss")
    load_stylesheet(app, qss_path)

    window.show()
    sys.exit(app.exec())
