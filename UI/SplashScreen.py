from PySide6.QtWidgets import (
    QDialog, QProgressBar, QLabel, QVBoxLayout,
    QWidget, QPushButton, QSizePolicy
)
from PySide6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve,
    Property, QEvent
)
from PySide6.QtGui import (
    QFont, QPainter, QMovie, QColor, QPixmap,
    QPen, QLinearGradient, QGuiApplication, QPalette
)
import time

from utils.Logger import logger


class BlurOverlay(QWidget):
    """
    Semi-transparent overlay that dims only the main window.
    It is a child of the main window, so it follows its position,
    stacking, and minimize/restore behavior.
    """
    def __init__(self, parent_window: QWidget):
        super().__init__(parent_window)

        # Child, no separate taskbar entry
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setWindowFlags(Qt.Widget | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)

        self.setWindowOpacity(0.35)

        if parent_window:
            self.setGeometry(parent_window.rect())

        self.show()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 160))


class SplashScreen(QDialog):
    """
    Runtime / startup splash dialog.

    - Stays above the main window
    - Goes behind other applications
    - Minimizes/restores with the main window
    - Optional overlay dim & cancel button
    """

    def __init__(self, parent: QWidget | None = None, gif_path: str | None = None, img_path: str | None = None):
        super().__init__(parent)

        self.overlay: BlurOverlay | None = None
        self.cancel_button: QPushButton | None = None
        self.eta_label: QLabel | None = None
        self.start_time: float | None = None

        # Install event filter on parent to track minimize/restore/move/resize
        if parent is not None:
            parent.installEventFilter(self)

        # IMPORTANT: No global always-on-top. Tool + Frameless keeps it tied to app.
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Dialog
        )

        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(False)

        # Size and state
        self.setFixedSize(550, 450)
        self._centered_once = False
        self.title = ""
        self.status = ""
        self._opacity = 0.0
        self.setWindowOpacity(0.0)

        # Theme
        self._is_dark_theme = self._detect_color_scheme()
        self._setup_theme_palette()

        # === Layout ===
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Title
        self.title_label = QLabel("")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.title_label.setStyleSheet(
            f"color: {self._title_color.name()}; padding: 10px;"
        )
        layout.addWidget(self.title_label)

        # GIF
        self.movie_label = QLabel(self)
        self.movie_label.setAlignment(Qt.AlignCenter)
        self.movie_label.setSizePolicy(
            QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        )

        self.movie = None

        if gif_path:
            self.movie = QMovie(gif_path)
            if self.movie.isValid():
                self.movie_label.setMovie(self.movie)
                self.movie.start()
                logger.debug(f"Loaded GIF: {gif_path}")
            else:
                self._set_fallback_loader()

        elif img_path:
            pixmap = QPixmap(img_path)
            if not pixmap.isNull():
                self._logo_pixmap = pixmap  # store original
                self._update_logo_pixmap()
                logger.debug(f"Loaded image: {img_path}")
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

        # Status text
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFont(QFont("Segoe UI", 11))
        self.status_label.setStyleSheet(
            f"color: {self._status_color.name()}; padding: 5px;"
        )
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        # ETA
        self.eta_label = QLabel("")
        self.eta_label.setAlignment(Qt.AlignCenter)
        self.eta_label.setFont(QFont("Segoe UI", 10))
        self.eta_label.setStyleSheet("color: #90caf9;")
        layout.addWidget(self.eta_label)

        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setFixedWidth(120)
        self.cancel_button.setVisible(False)
        layout.addWidget(self.cancel_button, alignment=Qt.AlignCenter)

        layout.addStretch()

        self._fade_animation: QPropertyAnimation | None = None
        self._fade_in_animation: QPropertyAnimation | None = None

    def _update_logo_pixmap(self):
        if not hasattr(self, "_logo_pixmap"):
            return

        # Logo takes ~65% of splash height
        target_height = int(self.height() * 0.65)

        scaled = self._logo_pixmap.scaled(
            target_height,
            target_height,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.movie_label.setPixmap(scaled)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_logo_pixmap()

# ---------- Event Filter (track parent window) ----------
    def eventFilter(self, obj, event):
        """
        Track the parent window so the splash:
        - Minimizes/restores together
        - Keeps overlay aligned on move/resize
        """
        parent = self.parent()
        if parent is not None and obj is parent:
            et = event.type()
            if et == QEvent.WindowStateChange:
                if parent.isMinimized():
                    self.showMinimized()
                    if self.overlay:
                        self.overlay.hide()
                else:
                    # Restored
                    if self.isMinimized():
                        self.showNormal()
                    self.raise_()
                    self.activateWindow()
                    if self.overlay:
                        self.overlay.show()
            elif et in (QEvent.Move, QEvent.Resize):
                # Keep overlay covering the parent
                if self.overlay and parent is not None:
                    self.overlay.setGeometry(parent.rect())

        return super().eventFilter(obj, event)

    # ---------- Theme detection & setup ----------

    def _detect_color_scheme(self) -> bool:
        app = QGuiApplication.instance()
        if not app:
            return True  # assume dark

        palette: QPalette = app.palette()
        window_color = palette.color(QPalette.Window)
        luminance = (
            0.299 * window_color.red() +
            0.587 * window_color.green() +
            0.114 * window_color.blue()
        )
        return luminance < 128

    def _setup_theme_palette(self):
        if self._is_dark_theme:
            self._gradient_top = QColor(26, 35, 39)
            self._gradient_mid = QColor(38, 50, 56)
            self._gradient_bottom = QColor(55, 71, 79)

            self._border_color = QColor(100, 181, 246, 100)
            self._title_color = QColor(255, 255, 255)
            self._status_color = QColor(176, 190, 197)

            self._progress_bg = "rgba(255, 255, 255, 0.12)"
            self._progress_chunk_start = "#1e88e5"
            self._progress_chunk_mid = "#42a5f5"
            self._progress_chunk_end = "#64b5f6"
        else:
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
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 {self._progress_chunk_start},
                    stop:0.5 {self._progress_chunk_mid},
                    stop:1 {self._progress_chunk_end}
                );
            }}
        """)

    def _set_fallback_loader(self):
        self.movie_label.setText("●●●")
        self.movie_label.setFont(QFont("Segoe UI", 48))
        accent = QColor(100, 181, 246) if self._is_dark_theme else QColor(25, 118, 210)
        self.movie_label.setStyleSheet(f"color: {accent.name()};")

    # ---------- Painting & positioning ----------

    def showEvent(self, event):
        super().showEvent(event)

        if not self._centered_once:
            self._centered_once = True

            parent = self.parent()
            if parent is not None and parent.isVisible():
                geo = parent.frameGeometry()
            else:
                screen = QGuiApplication.primaryScreen()
                geo = screen.availableGeometry() if screen else None

            if geo:
                self.move(
                    geo.center().x() - self.width() // 2,
                    geo.center().y() - self.height() // 2
                )

    def paintEvent(self, event):
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
        self.title = title
        self.title_label.setText(title)

    def update_status(self, message: str):
        self.status = message
        self.status_label.setText(message)

    def set_progress(self, value: int):
        value = max(0, min(100, int(value)))

        if not hasattr(self, "_progress_anim"):
            self._progress_anim = QPropertyAnimation(
                self.progress_bar, b"value", self
            )
            self._progress_anim.setEasingCurve(QEasingCurve.OutCubic)

        self._progress_anim.stop()
        self._progress_anim.setDuration(300)
        self._progress_anim.setStartValue(self.progress_bar.value())
        self._progress_anim.setEndValue(value)
        self._progress_anim.start()

    def update_eta(self, progress: int):
        if self.start_time is None or progress <= 0:
            return

        elapsed = time.time() - self.start_time
        total_estimated = elapsed * (100.0 / progress)
        remaining = max(0, int(total_estimated - elapsed))

        mins, secs = divmod(remaining, 60)
        self.eta_label.setText(
            f"Estimated time remaining: {mins:02d}:{secs:02d}"
        )

    def enable_runtime_mode(self, parent_window: QWidget, cancel_callback):
        """
        Call this for long-running tasks (search, scraping).
        """
        if parent_window is not None:
            self.overlay = BlurOverlay(parent_window)
        self.cancel_button.setVisible(True)
        self.cancel_button.clicked.connect(cancel_callback)

    # ---------- Animations ----------

    def show_with_animation(self, duration_ms: int = 500):
        self.start_time = time.time()
        self.setWindowOpacity(0.0)
        self._opacity = 0.0

        self.show()
        self.raise_()
        self.activateWindow()

        self.setWindowState((self.windowState() & ~Qt.WindowMinimized) | Qt.WindowActive)

        self._fade_in_animation = QPropertyAnimation(self, b"opacity", self)
        self._fade_in_animation.setDuration(duration_ms)
        self._fade_in_animation.setStartValue(0.0)
        self._fade_in_animation.setEndValue(1.0)
        self._fade_in_animation.setEasingCurve(QEasingCurve.OutCubic)
        self._fade_in_animation.start()

    def fade_and_close(self, duration_ms: int = 700):
        if self._fade_animation is not None:
            return

        self._fade_animation = QPropertyAnimation(self, b"opacity", self)
        self._fade_animation.setDuration(duration_ms)
        self._fade_animation.setStartValue(self.windowOpacity())
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

        if self.overlay:
            self.overlay.close()
            self.overlay = None

        super().closeEvent(event)
