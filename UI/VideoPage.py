from PySide6 import QtCore
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout

from utils.AppState import app_state

class Video(QWidget):
    videos:dict
    video_url:dict
    live:dict
    shorts:dict
    content:dict

    def __init__(self, parent=None):
        super(Video, self).__init__(parent)
        self.mainwindow = parent
        self.channel_label = QLabel()
        self.central_layout = QVBoxLayout()
        self.central_layout.addWidget(self.channel_label, alignment=QtCore.Qt.AlignTop)

        app_state.channel_name_changed.connect(self.update_channel_label)
        self.update_channel_label(app_state.channel_name)

        self.setLayout(self.central_layout)

    def update_channel_label(self, name=None):
        self.channel_label.setText(f"Selected channel: {name or 'None'}")
        self.central_layout.replaceWidget(self.channel_label, self.channel_label)

