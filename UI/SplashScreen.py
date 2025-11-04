from PySide6.QtWidgets import QSplashScreen, QLabel, QVBoxLayout, QWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QFont
import os


class SplashScreen(QSplashScreen):
    def __init__(self):
        # Create a simple colored pixmap as background
        pixmap = QPixmap(500, 300)
        pixmap.fill(Qt.white)
        
        super().__init__(pixmap, Qt.WindowStaysOnTopHint)
        
        # Create a widget to hold our layout
        self.container = QWidget(self)
        self.main_layout = QVBoxLayout(self.container)
        self.main_layout.setAlignment(Qt.AlignCenter)
        
        # App title label
        self.title_label = QLabel()
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("color: #2c3e50; margin-bottom: 20px;")
        
        # Status label
        self.status_label = QLabel()
        status_font = QFont()
        status_font.setPointSize(12)
        self.status_label.setFont(status_font)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #34495e; margin-top: 10px;")
        
        # Add labels to self.main_layout
        self.main_layout.addWidget(self.title_label)
        self.main_layout.addWidget(self.status_label)
        
        # Set the self.container geometry to cover the splash screen
        self.container.setGeometry(0, 0, 500, 300)
        
        # Set splash screen style
        self.setStyleSheet("""
            QSplashScreen {
                background-color: white;
                border: 2px solid #3498db;
                border-radius: 10px;
            }
        """)
    
    def set_title(self, title: str):
        """Set the title text on splash screen"""
        self.title_label.setText(title)
        self.repaint()  # Force immediate repaint

    def update_status(self, message: str):
        """Update the status text on splash screen"""
        self.status_label.setText(message)
        self.repaint()  # Force immediate repaint