from PySide6 import QtCore
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout

class Settings(QWidget):
    def __init__(self, parent=None):
        super(Settings, self).__init__(parent)

        self.main_layout = QVBoxLayout(self)

