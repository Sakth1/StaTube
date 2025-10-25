from PySide6 import QtCore
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout

class Video(QWidget):
    def __init__(self, parent=None):
        super(Video, self).__init__(parent)

        self.main_layout = QVBoxLayout(self)
        self.set_coming_soon()

    def set_coming_soon(self):
        coming_soon = QLabel("Video Analysis Coming Soon")
        coming_soon.setAlignment(QtCore.Qt.AlignCenter)
        coming_soon.setStyleSheet("font-size: 30px;")
        self.main_layout.addWidget(coming_soon)
