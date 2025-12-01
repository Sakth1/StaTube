from PySide6.QtWidgets import QDialog, QProgressBar, QLabel, QVBoxLayout
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Property, QEvent
from PySide6.QtGui import QPixmap, QFont, QPainter, QMovie, QColor, QPen, QLinearGradient, QGuiApplication


class SplashScreen(QDialog):
    """
    A frameless dialog that shows a GIF/Animation and status messages during startup.
    """
    def __init__(self, parent=None, gif_path=None):
        """
        Initializes the SplashScreen widget.

        Args:
            parent (QWidget): The parent widget (optional).
            gif_path (str): The path to the GIF to display.
        """
        super().__init__(parent)

        # Window flags: frameless, always on top, no taskbar button
        self.setWindowFlags(
            Qt.Dialog
            | Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(True)  # Block interaction with parent while visible

        # Fixed size
        self.setFixedSize(550, 450)

        # Centering flag
        self._centered_once = False

        self.title = ""
        self.status = ""
        self._opacity = 1.0

        # === Layout ===
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Title label
        self.title_label = QLabel("")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.title_label.setStyleSheet("color: #ffffff; padding: 10px;")
        layout.addWidget(self.title_label)

        # GIF / animation area
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
        else:
            # Default fallback when no GIF path is provided
            self.movie_label.setText("●●●")
            self.movie_label.setFont(QFont("Segoe UI", 48))
            self.movie_label.setStyleSheet("color: #64b5f6;")

        layout.addWidget(self.movie_label, alignment=Qt.AlignCenter)

        # Progress bar
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

        # Status label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFont(QFont("Segoe UI", 11))
        self.status_label.setStyleSheet("color: #b0bec5; padding: 5px;")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        layout.addStretch()

        # Keep reference to animation so it is not garbage collected
        self._fade_animation = None

    # ---------- Positioning / Painting ----------

    def showEvent(self, event: QEvent) -> None:
        """
        Ensure the splash is centered on the correct screen when shown.
        """
        super().showEvent(event)

        if not self._centered_once:
            self._centered_once = True

            # Try to center on the same screen as parent if possible
            screen = None
            if self.parent() and self.parent().windowHandle():
                screen = self.parent().windowHandle().screen()

            if screen is None:
                screen = QGuiApplication.primaryScreen()

            if screen:
                geo = screen.availableGeometry()
                self.move(
                    geo.center().x() - self.width() // 2,
                    geo.center().y() - self.height() // 2
                )

    def paintEvent(self, event):
        """
        Draw modern gradient background with border and soft shadow.
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Shadow
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(0, 0, 0, 80))
        painter.drawRoundedRect(5, 5, self.width() - 10, self.height() - 10, 15, 15)

        # Gradient background
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(26, 35, 39))      # #1a2327
        gradient.setColorAt(0.5, QColor(38, 50, 56))    # #263238
        gradient.setColorAt(1, QColor(55, 71, 79))      # #37474f

        painter.setBrush(gradient)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 12, 12)

        # Border
        painter.setPen(QPen(QColor(100, 181, 246, 100), 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(1, 1, self.width() - 2, self.height() - 2, 12, 12)

    # ---------- Public API ----------

    def set_title(self, title: str):
        """
        Set the title of the SplashScreen dialog.
        """
        self.title = title
        self.title_label.setText(title)

    def update_status(self, message: str):
        """
        Update the status message of the SplashScreen dialog.
        """
        self.status = message
        self.status_label.setText(message)

    def set_progress(self, value: int):
        """
        Set the progress bar value (0-100).
        """
        self.progress_bar.setValue(int(value))

    def fade_and_close(self, duration_ms: int = 700):
        """
        Fade out smoothly and close the splash.
        """
        if self._fade_animation is not None:
            # Already fading
            return

        self._fade_animation = QPropertyAnimation(self, b"opacity", self)
        self._fade_animation.setDuration(duration_ms)
        self._fade_animation.setStartValue(1.0)
        self._fade_animation.setEndValue(0.0)
        self._fade_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self._fade_animation.finished.connect(self.close)
        self._fade_animation.start()

    # ---------- Opacity property for animation ----------

    def get_opacity(self) -> float:
        return self._opacity

    def set_opacity(self, value: float):
        self._opacity = value
        self.setWindowOpacity(value)

    opacity = Property(float, get_opacity, set_opacity)

    # ---------- Cleanup ----------

    def closeEvent(self, event):
        if self.movie:
            self.movie.stop()
        super().closeEvent(event)
