from PySide6 import QtCore
from PySide6.QtWidgets import (QWidget, QLabel, QGridLayout, QStyle, QPushButton,
                               QListView, QVBoxLayout, QAbstractItemView, QStyledItemDelegate,
                               QButtonGroup, QHBoxLayout)
from PySide6.QtCore import QThread, Qt, QSize, QRect
from PySide6.QtGui import QStandardItemModel, QStandardItem, QPixmap, QPainter, QFont, QColor
import os

from Backend.ScrapeVideo import VideoWorker
from UI.SplashScreen import SplashScreen
from utils.AppState import app_state


class YouTubeVideoItem:
    def __init__(self, thumbnail: QPixmap, title: str, duration: str, views: str, video_type: str):
        self.thumbnail = thumbnail
        self.title = title
        self.duration = duration
        self.views = views
        self.video_type = video_type


class YouTubeVideoDelegate(QStyledItemDelegate):
    """Custom delegate for drawing YouTube video and Shorts with distinct layouts."""

    def __init__(self, parent=None):
        super().__init__(parent)

    def paint(self, painter, option, index):
        data = index.data(Qt.UserRole)
        if not data:
            return

        thumbnail = data.thumbnail
        title = getattr(data, "title", "")
        duration = getattr(data, "duration", "")
        views = getattr(data, "views", "")
        video_type = getattr(data, "video_type", "video").lower()

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(option.rect, QColor("#121212"))

        # Thumbnail layout
        if video_type == "shorts":
            thumb_w, thumb_h = 256, 456  # proportional to 405x720 but smaller
        else:
            thumb_w, thumb_h = 256, 144  # 16:9

        # Center horizontally
        thumb_x = option.rect.x() + (option.rect.width() - thumb_w) // 2
        thumb_y = option.rect.y() + 8
        thumb_rect = QRect(thumb_x, thumb_y, thumb_w, thumb_h)

        # Draw thumbnail
        if isinstance(thumbnail, QPixmap):
            scaled = thumbnail.scaled(thumb_w, thumb_h, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            painter.drawPixmap(thumb_rect, scaled)

        # Duration overlay
        if duration:
            duration_text = str(duration)
            painter.setFont(QFont("Segoe UI", 8))
            painter.setPen(Qt.white)
            metrics = painter.fontMetrics()
            text_w = metrics.horizontalAdvance(duration_text)
            text_h = metrics.height()
            duration_rect = QRect(
                thumb_rect.right() - text_w - 10,
                thumb_rect.bottom() - text_h - 6,
                text_w + 6,
                text_h + 2,
            )
            painter.fillRect(duration_rect, QColor(0, 0, 0, 180))
            painter.drawText(duration_rect, Qt.AlignCenter, duration_text)

        # Title text
        painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
        painter.setPen(Qt.white)
        title_rect = QRect(thumb_rect.left(), thumb_rect.bottom() + 8, thumb_rect.width(), 40)
        painter.drawText(title_rect, Qt.TextWordWrap | Qt.AlignLeft, title)

        # Views text
        try:
            views_num = int(float(views))
            views_text = f"{views_num:,} views"
        except (ValueError, TypeError):
            views_text = f"{views} views"

        painter.setFont(QFont("Segoe UI", 9))
        painter.setPen(QColor("#AAAAAA"))
        views_rect = QRect(thumb_rect.left(), title_rect.bottom() + 2, thumb_rect.width(), 20)
        painter.drawText(views_rect, Qt.AlignLeft, views_text)

        painter.restore()

    def sizeHint(self, option, index):
        data = index.data(Qt.UserRole)
        if not data:
            return QSize(256, 200)

        video_type = getattr(data, "video_type", "video").lower()
        if video_type == "shorts":
            # Taller vertical layout
            return QSize(256, 520)
        else:
            return QSize(256, 210)


class Video(QWidget):
    videos: dict = None

    def __init__(self, parent=None):
        super(Video, self).__init__(parent)
        self.mainwindow = parent
        self.db = app_state.db

        self.splash = None
        self.worker_thread = None
        self.worker = None
        self.video_page = QWidget()
        self.main_layout = QGridLayout()

        # Create buttons
        self.grid_button = QPushButton("Grid")
        self.grid_button.setCheckable(True)
        self.list_button = QPushButton("List")
        self.list_button.setCheckable(True)

        # Create a button group and make it exclusive
        self.segmented_button = QButtonGroup(self)
        self.segmented_button.addButton(self.grid_button)
        self.segmented_button.addButton(self.list_button)
        self.segmented_button.setExclusive(True)  # ensures only one stays checked

        # Set default checked button
        self.grid_button.setChecked(True)
        
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.addWidget(self.grid_button)
        button_layout.addWidget(self.list_button)
        button_layout.setSpacing(0)
        button_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(button_container, 0, 0, 1, 1)

        self.channel_label = QLabel()
        self.scrap_video_button = QPushButton("Scrape Videos")
        self.scrap_video_button.clicked.connect(self.scrape_videos)
        self.main_layout.addWidget(self.channel_label, 0, 1, 1, 2)
        self.main_layout.addWidget(self.scrap_video_button, 0, 3, 1, 1)
        self.select_button = QPushButton("Select")
        self.main_layout.addWidget(self.select_button, 10, 0, 1, 4)

        self.setup_grid_video_view()
        
        self.setLayout(self.main_layout)

        app_state.channel_name_changed.connect(self.update_channel_label)
        self.update_channel_label(app_state.channel_name)

    def setup_grid_video_view(self):
        self.video_view = QListView()
        self.video_view.setViewMode(QListView.IconMode)
        self.video_view.setResizeMode(QListView.Adjust)
        self.video_view.setFlow(QListView.LeftToRight)
        self.video_view.setWrapping(True)
        self.video_view.setSpacing(20)
        self.video_view.setSelectionMode(QAbstractItemView.NoSelection)

        self.model = QStandardItemModel()
        self.video_view.setModel(self.model)
        self.video_delegate = YouTubeVideoDelegate(self.video_view)
        self.video_view.setItemDelegate(self.video_delegate)

        self.main_layout.addWidget(self.video_view, 1, 0, 1, 4)

    def update_channel_label(self, name=None):
        self.channel_label.setText(f"Selected channel: {name or 'None'}")

    def scrape_videos(self):
        channel_name = app_state.channel_name
        channel_id = app_state.channel_id
        channel_url = app_state.channel_url

        if not channel_name or not channel_id or not channel_url:
            print("No channel selected")
            return

        self.show_splash_screen()

        self.worker_thread = QThread()
        self.worker = VideoWorker(channel_id, channel_url)
        self.worker.moveToThread(self.worker_thread)

        self.worker_thread.started.connect(self.worker.fetch_video_urls)
        self.worker.progress_updated.connect(self.update_splash_progress)
        self.worker.progress_percentage.connect(self.update_splash_percentage)
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)

        self.worker_thread.start()

    def show_splash_screen(self):
        cwd = os.getcwd()
        gif_path = os.path.join(cwd, "assets", "gif", "loading.gif")
        self.splash = SplashScreen(gif_path=gif_path)
        self.splash.set_title("Scraping Videos...")
        self.splash.update_status("Starting...")
        self.splash.show()

    def update_splash_progress(self, message):
        if self.splash:
            self.splash.update_status(message)

    def update_splash_percentage(self, percentage):
        if self.splash:
            self.splash.set_progress(percentage)

    def on_worker_finished(self):
        if self.splash:
            self.splash.close()
            self.splash = None

        print("Video scraping completed!")
        self.load_videos_from_db()

    def load_videos_from_db(self):
        channel_id = app_state.channel_id
        videos = self.db.fetch("VIDEO", "channel_id = ?", (channel_id,))

        self.model.clear()

        for video in videos:
            thumb_path = os.path.join(self.db.thumbnail_dir, str(channel_id), f"{video['video_id']}.png")
            if not os.path.exists(thumb_path):
                continue

            pixmap = QPixmap(thumb_path)
            if pixmap.isNull():
                continue

            duration = self._format_duration(video.get("duration"))
            views = self._format_views(video.get("view_count"))
            title = video.get("title", "Untitled")
            video_type = video.get("video_type", "video").lower()

            item_data = YouTubeVideoItem(pixmap, title, duration, views, video_type)
            item = QStandardItem()
            item.setData(item_data, Qt.UserRole)
            item.setEditable(False)
            self.model.appendRow(item)

        print(f"Loaded {self.model.rowCount()} videos for channel {channel_id}")

    # --- Helper for formatting duration ---
    def _format_duration(self, seconds):
        try:
            if seconds is None or seconds == "":
                return "--:--"
            seconds = int(float(seconds))  # handles "1027.0" or float values
            minutes, sec = divmod(seconds, 60)
            hours, minutes = divmod(minutes, 60)
            if hours:
                return f"{hours}:{minutes:02}:{sec:02}"
            return f"{minutes}:{sec:02}"
        except Exception:
            return "--:--"

    def _format_views(self, views):
        try:
            views = int(views)
            if views >= 1_000_000:
                return f"{views/1_000_000:.1f}M"
            elif views >= 1_000:
                return f"{views/1_000:.1f}K"
            return str(views)
        except Exception:
            return "0"
