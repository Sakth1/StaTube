from PySide6.QtWidgets import QSplashScreen
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QPixmap, QFont, QPainter

class SplashScreen(QSplashScreen):
    def __init__(self):
        pixmap = QPixmap(500, 300)
        pixmap.fill(Qt.white)
        super().__init__(pixmap, Qt.WindowStaysOnTopHint)
        self.title = ""
        self.status = ""

    def set_title(self, title):
        self.title = title
        self.repaint()

    def update_status(self, message):
        self.status = message
        self.repaint()

    def drawContents(self, painter: QPainter):
        painter.setPen(Qt.black)

        # Draw title near the top
        painter.setFont(QFont("Segoe UI Semibold", 18))
        title_rect = QRect(0, 80, self.width(), 40)  # top margin + height
        painter.drawText(title_rect, Qt.AlignCenter, self.title)

        # Draw status below title
        painter.setFont(QFont("Segoe UI", 12))
        status_rect = QRect(0, 160, self.width(), 40)  # lower vertical position
        painter.drawText(status_rect, Qt.AlignCenter, self.status)
