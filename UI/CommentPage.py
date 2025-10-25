from PySide6 import QtCore
from PySide6.QtWidgets import (QApplication, QMainWindow, QStackedWidget, QWidget, 
                               QLineEdit, QListWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QListWidgetItem, QCompleter, QGridLayout)


class Comment(QWidget):
    def __init__(self, parent: QMainWindow = None):
        super(Comment, self).__init__(parent)

        self.mainwindow = parent

        self.main_widget = QWidget()
        self.main_layout = QVBoxLayout()
        self.set_coming_soon()
        self.main_widget.setLayout(self.main_layout)

    def set_coming_soon(self):
        coming_soon = QLabel("Comment Analysis Coming Soon")
        coming_soon.setAlignment(QtCore.Qt.AlignCenter)
        coming_soon.setStyleSheet("font-size: 30px;")
        self.main_layout.addWidget(coming_soon)
