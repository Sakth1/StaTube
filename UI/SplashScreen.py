from PySide6.QtWidgets import QDialog, QProgressBar, QLabel, QVBoxLayout, QWidget
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import QPixmap, QFont, QPainter, QMovie, QColor, QPen, QLinearGradient

class SplashScreen(QDialog):
    def __init__(self, parent=None, gif_path=None):
        super().__init__(parent)
        
        # Set up as a frameless dialog that follows parent
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(True)  # Makes it block parent interaction
        
        # Fixed size
        self.setFixedSize(550, 450)
        
        # Center on parent or screen
        if parent:
            parent_geo = parent.geometry()
            x = parent_geo.x() + (parent_geo.width() - 550) // 2
            y = parent_geo.y() + (parent_geo.height() - 450) // 2
            self.move(x, y)
        else:
            self.move(100, 100)
        
        self.title = ""
        self.status = ""
        self._opacity = 1.0
        
        # Create main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Title label with modern styling
        self.title_label = QLabel("")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.title_label.setStyleSheet("color: #ffffff; padding: 10px;")
        layout.addWidget(self.title_label)
        
        # GIF/Animation area
        self.movie_label = QLabel(self)
        self.movie_label.setAlignment(Qt.AlignCenter)
        self.movie_label.setFixedSize(200, 200)
        self.movie = None
        
        if gif_path:
            self.movie = QMovie(gif_path)
            if self.movie.isValid():
                self.movie_label.setMovie(self.movie)
                self.movie.start()
            else:
                self.movie_label.setText("●●●")
                self.movie_label.setFont(QFont("Segoe UI", 48))
                self.movie_label.setStyleSheet("color: #64b5f6;")
        
        layout.addWidget(self.movie_label, alignment=Qt.AlignCenter)
        
        # Modern progress bar with glow effect
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 3px;
                background-color: rgba(255, 255, 255, 0.1);
            }
            QProgressBar::chunk {
                border-radius: 3px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1e88e5, stop:0.5 #42a5f5, stop:1 #64b5f6);
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # Status label with modern styling
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFont(QFont("Segoe UI", 11))
        self.status_label.setStyleSheet("color: #b0bec5; padding: 5px;")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        
        layout.addStretch()
    
    def paintEvent(self, event):
        """Draw modern gradient background with border"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw shadow effect
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(0, 0, 0, 80))
        painter.drawRoundedRect(5, 5, self.width() - 10, self.height() - 10, 15, 15)
        
        # Draw gradient background
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(26, 35, 39))      # #1a2327
        gradient.setColorAt(0.5, QColor(38, 50, 56))    # #263238
        gradient.setColorAt(1, QColor(55, 71, 79))      # #37474f
        
        painter.setBrush(gradient)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 12, 12)
        
        # Draw border with accent color
        painter.setPen(QPen(QColor(100, 181, 246, 100), 2))  # #64b5f6 with transparency
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(1, 1, self.width() - 2, self.height() - 2, 12, 12)
    
    def set_title(self, title):
        self.title = title
        self.title_label.setText(title)
    
    def update_status(self, message):
        self.status = message
        self.status_label.setText(message)
    
    def set_progress(self, value):
        """Set progress bar value (0-100)"""
        self.progress_bar.setValue(int(value))
    
    def closeEvent(self, event):
        """Clean up movie when closing"""
        if self.movie:
            self.movie.stop()
        super().closeEvent(event)
    
    # Opacity property for animations
    def get_opacity(self):
        return self._opacity
    
    def set_opacity(self, value):
        self._opacity = value
        self.setWindowOpacity(value)
    
    opacity = Property(float, get_opacity, set_opacity)