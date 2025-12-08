from PySide6.QtWidgets import QDialog, QProgressBar, QLabel, QVBoxLayout
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Property, QEvent
from PySide6.QtGui import QPixmap, QFont, QPainter, QMovie, QColor, QPen, QLinearGradient, QGuiApplication, QPalette


class SplashScreen(QDialog):
    """
    A frameless dialog that shows a GIF/Animation and status messages during startup.
    Supports:
      - Auto dark/light theme based on system palette
      - Fade-in / fade-out animations
    """
    def __init__(self, parent=None, gif_path=None):
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

        # Theme: computed once at construction
        self._is_dark_theme = self._detect_color_scheme()

        # Precompute colours for theme
        self._setup_theme_palette()

        # === Layout ===
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Title label
        self.title_label = QLabel("")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.title_label.setStyleSheet(f"color: {self._title_color.name()}; padding: 10px;")
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
                self._set_fallback_loader()
        else:
            self._set_fallback_loader()

        layout.addWidget(self.movie_label, alignment=Qt.AlignCenter)

        # Progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(6)
        self._apply_progressbar_style()
        layout.addWidget(self.progress_bar)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFont(QFont("Segoe UI", 11))
        self.status_label.setStyleSheet(f"color: {self._status_color.name()}; padding: 5px;")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        layout.addStretch()

        # Keep reference to animations so they are not garbage collected
        self._fade_animation = None
        self._fade_in_animation = None

        # Start transparent; we’ll animate to 1.0
        self.setWindowOpacity(0.0)
        self._opacity = 0.0

    # ---------- Theme detection & setup ----------

    def _detect_color_scheme(self) -> bool:
        """
        Heuristic to detect if the system/app is using a dark theme.
        Returns True if dark, False if light.
        """
        app = QGuiApplication.instance()
        if not app:
            return True  # default to dark if unsure

        palette: QPalette = app.palette()
        window_color = palette.color(QPalette.Window)
        # Simple luminance heuristic
        luminance = (
            0.299 * window_color.red() +
            0.587 * window_color.green() +
            0.114 * window_color.blue()
        )
        # Lower luminance -> dark theme
        return luminance < 128

    def _setup_theme_palette(self):
        """
        Set up colours depending on dark/light mode.
        """
        if self._is_dark_theme:
            # Dark theme palette
            self._gradient_top = QColor(26, 35, 39)
            self._gradient_mid = QColor(38, 50, 56)
            self._gradient_bottom = QColor(55, 71, 79)

            self._border_color = QColor(100, 181, 246, 100)
            self._title_color = QColor(255, 255, 255)
            self._status_color = QColor(176, 190, 197)

            # Progress bar colours
            self._progress_bg = "rgba(255, 255, 255, 0.12)"
            self._progress_chunk_start = "#1e88e5"
            self._progress_chunk_mid = "#42a5f5"
            self._progress_chunk_end = "#64b5f6"
        else:
            # Light theme palette
            self._gradient_top = QColor(245, 245, 245)
            self._gradient_mid = QColor(232, 234, 246)
            self._gradient_bottom = QColor(225, 245, 254)

            self._border_color = QColor(120, 144, 156, 160)
            self._title_color = QColor(33, 33, 33)
            self._status_color = QColor(97, 97, 97)

            self._progress_bg = "rgba(0, 0, 0, 0.06)"
            self._progress_chunk_start = "#1e88e5"
            self._progress_chunk_mid = "#1976d2"
            self._progress_chunk_end = "#0d47a1"

    def _apply_progressbar_style(self):
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                border-radius: 3px;
                background-color: {self._progress_bg};
            }}
            QProgressBar::chunk {{
                border-radius: 3px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {self._progress_chunk_start},
                    stop:0.5 {self._progress_chunk_mid},
                    stop:1 {self._progress_chunk_end});
            }}
        """)

    def _set_fallback_loader(self):
        self.movie_label.setText("●●●")
        self.movie_label.setFont(QFont("Segoe UI", 48))
        accent = QColor(100, 181, 246) if self._is_dark_theme else QColor(25, 118, 210)
        self.movie_label.setStyleSheet(f"color: {accent.name()};")

    # ---------- Positioning / Painting ----------

    def showEvent(self, event: QEvent) -> None:
        """
        Ensure the splash is centered on the correct screen when shown.
        """
        super().showEvent(event)

        if not self._centered_once:
            self._centered_once = True

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
        gradient.setColorAt(0, self._gradient_top)
        gradient.setColorAt(0.5, self._gradient_mid)
        gradient.setColorAt(1, self._gradient_bottom)

        painter.setBrush(gradient)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 12, 12)

        # Border
        painter.setPen(QPen(self._border_color, 2))
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

    # ---------- Boot animations ----------

    def show_with_animation(self, duration_ms: int = 500):
        """
        Show the splash with a smooth fade-in animation.
        """
        # Start fully transparent
        self.setWindowOpacity(0.0)
        self._opacity = 0.0

        self.show()

        self._fade_in_animation = QPropertyAnimation(self, b"opacity", self)
        self._fade_in_animation.setDuration(duration_ms)
        self._fade_in_animation.setStartValue(0.0)
        self._fade_in_animation.setEndValue(1.0)
        self._fade_in_animation.setEasingCurve(QEasingCurve.OutCubic)
        self._fade_in_animation.start()

    def fade_and_close(self, duration_ms: int = 700):
        """
        Fade out smoothly and close the splash.
        """
        if self._fade_animation is not None:
            # Already fading
            return

        self._fade_animation = QPropertyAnimation(self, b"opacity", self)
        self._fade_animation.setDuration(duration_ms)
        self._fade_animation.setStartValue(self._opacity)
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
