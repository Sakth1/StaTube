from PySide6.QtWidgets import QSplashScreen, QLabel, QVBoxLayout, QWidget
from PySide6.QtCore import Qt, QMetaObject, Q_ARG
from PySide6.QtGui import QPixmap, QFont


class SplashScreen(QSplashScreen):
    def __init__(self):
        pixmap = QPixmap(500, 300)
        pixmap.fill(Qt.white)
        super().__init__(pixmap, Qt.WindowStaysOnTopHint)

        self.container = QWidget(self)
        self.main_layout = QVBoxLayout(self.container)
        self.main_layout.setAlignment(Qt.AlignCenter)

        self.title_label = QLabel()
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(Qt.AlignCenter)

        self.status_label = QLabel()
        status_font = QFont()
        status_font.setPointSize(12)
        self.status_label.setFont(status_font)
        self.status_label.setAlignment(Qt.AlignCenter)

        self.main_layout.addWidget(self.title_label)
        self.main_layout.addWidget(self.status_label)
        self.container.setGeometry(0, 0, 500, 300)

    def set_title(self, title: str):
        QMetaObject.invokeMethod(
            self.title_label, "setText", Qt.QueuedConnection, Q_ARG(str, title)
        )

    def update_status(self, message: str):
        QMetaObject.invokeMethod(
            self.status_label, "setText", Qt.QueuedConnection, Q_ARG(str, message)
        )
