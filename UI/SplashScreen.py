from PySide6.QtWidgets import QSplashScreen, QProgressBar, QLabel
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QPixmap, QFont, QPainter, QMovie

class SplashScreen(QSplashScreen):
    def __init__(self, gif_path=None):
        pixmap = QPixmap(500, 400)  # Increased height for GIF and progress bar
        pixmap.fill(Qt.white)
        super().__init__(pixmap, Qt.WindowStaysOnTopHint)
        self.title = ""
        self.status = ""
        self.has_gif = False
        
        # Create progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setGeometry(50, 220, 400, 25)  # x, y, width, height
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        
        # Load GIF only if path is provided
        self.movie_label = None
        self.movie = None
        
        if gif_path:
            self.movie_label = QLabel(self)
            self.movie_label.setGeometry(150, 50, 200, 150)  # Centered GIF area
            self.movie_label.setAlignment(Qt.AlignCenter)
            
            self.movie = QMovie(gif_path)
            if self.movie.isValid():
                self.movie_label.setMovie(self.movie)
                self.movie.start()
                self.has_gif = True
            else:
                print(f"Failed to load GIF from {gif_path}")
                self.movie_label.hide()

    def set_title(self, title):
        self.title = title
        self.repaint()

    def update_status(self, message):
        self.status = message
        self.repaint()
    
    def set_progress(self, value):
        """Set progress bar value (0-100)"""
        self.progress_bar.setValue(value)

    def drawContents(self, painter: QPainter):
        painter.setPen(Qt.black)

        # Draw title near the top
        painter.setFont(QFont("Segoe UI Semibold", 16))
        title_rect = QRect(0, 10, self.width(), 30)
        painter.drawText(title_rect, Qt.AlignCenter, self.title)

        # Draw status below progress bar
        painter.setFont(QFont("Segoe UI", 11))
        status_rect = QRect(0, 260, self.width(), 60)
        painter.drawText(status_rect, Qt.AlignCenter | Qt.TextWordWrap, self.status)