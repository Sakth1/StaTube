from PySide6 import QtCore
from PySide6.QtWidgets import (QWidget, QLabel, QGridLayout, QStyle, QPushButton,
                               QListView, QVBoxLayout, QAbstractItemView, QStyledItemDelegate,
                               QButtonGroup, QHBoxLayout, QFrame)
from PySide6.QtCore import QThread, Qt, QSize, QRect, Property
from PySide6.QtGui import QStandardItemModel, QStandardItem, QPixmap, QPainter, QFont, QColor, QIcon
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
    """Custom delegate for drawing YouTube videos and Shorts with grid and list layouts."""

    def __init__(self, parent=None):
        super().__init__(parent)

    def paint(self, painter, option, index):
        data = index.data(Qt.UserRole)
        if not data:
            return

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(option.rect, QColor("#0f0f0f"))  # YouTube's dark background

        view = option.widget
        is_list_mode = view.viewMode() == QListView.ListMode

        thumbnail = data.thumbnail
        title = getattr(data, "title", "")
        duration = getattr(data, "duration", "")
        views = getattr(data, "views", "")
        video_type = getattr(data, "video_type", "video").lower()

        if is_list_mode:
            # === LIST MODE (Bigger text) ===
            # Use same height for all video types, calculate width proportionally
            target_height = 100
            if isinstance(thumbnail, QPixmap) and not thumbnail.isNull():
                original_width = thumbnail.width()
                original_height = thumbnail.height()
                if original_height > 0:
                    target_width = int((original_width / original_height) * target_height)
                else:
                    target_width = 178  # YouTube list thumbnail width
            else:
                target_width = 178
                target_height = 100
            
            margin = 12  # Increased margin for better spacing

            # Thumbnail rectangle
            thumb_x = option.rect.x() + margin
            thumb_y = option.rect.y() + (option.rect.height() - target_height) // 2
            thumb_rect = QRect(thumb_x, thumb_y, target_width, target_height)

            # Draw proportionally scaled thumbnail
            if isinstance(thumbnail, QPixmap) and not thumbnail.isNull():
                scaled = thumbnail.scaled(target_width, target_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                x_offset = thumb_rect.x() + (thumb_rect.width() - scaled.width()) // 2
                y_offset = thumb_rect.y() + (thumb_rect.height() - scaled.height()) // 2
                painter.drawPixmap(x_offset, y_offset, scaled)

            # Text positions with proper spacing
            text_x = thumb_rect.right() + 16  # Increased spacing from thumbnail
            text_y = option.rect.y() + 14     # Increased top margin
            text_w = option.rect.width() - text_x - 20  # Right margin
            text_h = option.rect.height() - 24

            # === Title (Bigger font for list mode) ===
            painter.setFont(QFont("Segoe UI", 11, QFont.Bold))  # Increased from 9 to 11
            painter.setPen(Qt.white)
            title_rect = QRect(text_x, text_y, text_w, 44)  # Increased height for bigger text
            # Draw text with proper spacing - clip to prevent overflow
            painter.drawText(title_rect, Qt.TextWordWrap | Qt.AlignLeft | Qt.AlignTop, title)

            # === Views + Duration inline ===
            painter.setFont(QFont("Segoe UI", 9))  # Increased from 8 to 9
            painter.setPen(QColor("#AAAAAA"))

            # Views text
            try:
                views_num = int(float(views))
                views_text = f"{views_num:,} views"
            except (ValueError, TypeError):
                views_text = f"{views} views"

            # Compose single line: "views_text • duration"
            combined_text = f"{views_text}"
            if duration and duration != "--:--":
                combined_text += f" • {duration}"

            views_rect = QRect(text_x, title_rect.bottom() + 4, text_w, 20)  # Added spacing
            painter.drawText(views_rect, Qt.AlignLeft, combined_text)

        else:
            # === GRID MODE (Slightly bigger text) ===
            # Use same height for all video types, calculate width proportionally
            target_height = 144  # Normal video height
            if isinstance(thumbnail, QPixmap) and not thumbnail.isNull():
                original_width = thumbnail.width()
                original_height = thumbnail.height()
                if original_height > 0:
                    target_width = int((original_width / original_height) * target_height)
                else:
                    target_width = 256
            else:
                target_width = 256
                target_height = 144
            
            # Ensure minimum and maximum reasonable widths
            target_width = max(200, min(target_width, 360))  # Constrained for better grid layout

            # Thumbnail with horizontal centering and top spacing
            thumb_x = option.rect.x() + (option.rect.width() - target_width) // 2
            thumb_y = option.rect.y() + 10  # Increased top spacing
            thumb_rect = QRect(thumb_x, thumb_y, target_width, target_height)

            if isinstance(thumbnail, QPixmap) and not thumbnail.isNull():
                scaled = thumbnail.scaled(target_width, target_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                x_offset = thumb_rect.x() + (thumb_rect.width() - scaled.width()) // 2
                y_offset = thumb_rect.y() + (thumb_rect.height() - scaled.height()) // 2
                painter.drawPixmap(x_offset, y_offset, scaled)

            # Duration overlay
            if duration:
                painter.setFont(QFont("Segoe UI", 9))  # Slightly bigger
                painter.setPen(Qt.white)
                metrics = painter.fontMetrics()
                text_w = metrics.horizontalAdvance(duration)
                text_h = metrics.height()
                duration_rect = QRect(
                    thumb_rect.right() - text_w - 8,  # Adjusted positioning
                    thumb_rect.bottom() - text_h - 6,
                    text_w + 8,  # Slightly bigger background
                    text_h + 2,
                )
                painter.fillRect(duration_rect, QColor(0, 0, 0, 200))  # Darker background
                painter.drawText(duration_rect, Qt.AlignCenter, duration)

            # Title with side spacing
            painter.setFont(QFont("Segoe UI", 11, QFont.Bold))  # Increased from 10 to 11
            painter.setPen(Qt.white)
            # Title rect with left and right margins
            title_left_margin = 8
            title_right_margin = 8
            title_rect = QRect(
                thumb_rect.left() + title_left_margin, 
                thumb_rect.bottom() + 12,  # Increased spacing from thumbnail
                thumb_rect.width() - title_left_margin - title_right_margin, 
                42  # Increased height for bigger text
            )
            painter.drawText(title_rect, Qt.TextWordWrap | Qt.AlignLeft | Qt.AlignTop, title)

            # Views with side spacing
            painter.setFont(QFont("Segoe UI", 10))  # Increased from 9 to 10
            painter.setPen(QColor("#AAAAAA"))
            try:
                views_num = int(float(views))
                views_text = f"{views_num:,} views"
            except (ValueError, TypeError):
                views_text = f"{views} views"
            
            views_left_margin = 8
            views_right_margin = 8
            views_rect = QRect(
                thumb_rect.left() + views_left_margin, 
                title_rect.bottom() + 4,  # Increased spacing from title
                thumb_rect.width() - views_left_margin - views_right_margin, 
                20
            )
            painter.drawText(views_rect, Qt.AlignLeft, views_text)

        painter.restore()

    def sizeHint(self, option, index):
        """Adjusted sizes for better spacing."""
        view = option.widget
        if view.viewMode() == QListView.ListMode:
            return QSize(option.rect.width(), 120)  # Increased height for bigger text
        else:
            data = index.data(Qt.UserRole)
            if not data:
                return QSize(280, 240)  # Slightly bigger default
            
            # For grid mode, calculate width based on thumbnail aspect ratio
            thumbnail = getattr(data, "thumbnail", None)
            if isinstance(thumbnail, QPixmap) and not thumbnail.isNull():
                original_width = thumbnail.width()
                original_height = thumbnail.height()
                if original_height > 0:
                    target_width = int((original_width / original_height) * 144)
                    target_width = max(200, min(target_width, 360))  # Adjusted constraints
                else:
                    target_width = 280
            else:
                target_width = 280
            
            return QSize(target_width, 240)  # Increased height for bigger text and spacing


class Video(QWidget):
    videos: dict = None

    def __init__(self, parent=None):
        super(Video, self).__init__(parent)
        self.mainwindow = parent
        self.db = app_state.db

        self.splash = None
        self.worker_thread = None
        self.worker = None

        # === Main layout ===
        self.main_layout = QGridLayout(self)
        self.setLayout(self.main_layout)

        # === Channel Info ===
        self.channel_label = QLabel()
        self.scrap_video_button = QPushButton("Scrape Videos")
        self.scrap_video_button.clicked.connect(self.scrape_videos)

        # === Segmented Control (List / Grid) ===
        self._create_segmented_control()

        # === Video list ===
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

        # === Header layout ===
        self.main_layout.addWidget(self.segment_container, 0, 0, 1, 1, alignment=Qt.AlignLeft)
        self.main_layout.addWidget(self.channel_label, 0, 1, 1, 2, alignment=Qt.AlignCenter)
        self.main_layout.addWidget(self.scrap_video_button, 0, 3, 1, 1)
        self.main_layout.addWidget(self.video_view, 1, 0, 1, 4)

        app_state.channel_name_changed.connect(self.update_channel_label)
        self.update_channel_label(app_state.channel_name)

    # === Segmented Control Creation ===
    def _create_segmented_control(self):
        self.segment_container = QFrame()
        layout = QHBoxLayout(self.segment_container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        list_icon = QIcon(os.path.join(self.mainwindow.base_dir, "assets", "icon", "light", "light_list.ico"))
        grid_icon = QIcon(os.path.join(self.mainwindow.base_dir, "assets", "icon", "light", "light_grid.ico"))

        self.list_btn = QPushButton()
        self.list_btn.setIcon(list_icon)
        self.list_btn.setToolTip("List View")
        self.list_btn.setCheckable(True)
        self.list_btn.setChecked(True)
        self.list_btn.setProperty("segment", "left")
        self.list_btn.clicked.connect(self.on_list_clicked)

        self.grid_btn = QPushButton()
        self.grid_btn.setIcon(grid_icon)
        self.grid_btn.setToolTip("Grid View")
        self.grid_btn.setCheckable(True)
        self.grid_btn.setProperty("segment", "right")
        self.grid_btn.clicked.connect(self.on_grid_clicked)
        
        self.grid_btn.setChecked(True)
        self.list_btn.setChecked(False)

        layout.addWidget(self.list_btn)
        layout.addWidget(self.grid_btn)
        self.segment_container.setFixedHeight(32)

    # === Segmented control handlers ===
    def on_list_clicked(self):
        if self.list_btn.isChecked():
            self.grid_btn.setChecked(False)
            self.video_view.setViewMode(QListView.ListMode)
            self.video_view.setFlow(QListView.TopToBottom)
            self.video_view.setSpacing(4)  # compact spacing
        else:
            self.list_btn.setChecked(True)
        print("List view selected")


    def on_grid_clicked(self):
        if self.grid_btn.isChecked():
            self.list_btn.setChecked(False)
            self.video_view.setViewMode(QListView.IconMode)
            self.video_view.setFlow(QListView.LeftToRight)
        else:
            self.grid_btn.setChecked(True)
        print("Grid view selected")

    # === Channel label ===
    def update_channel_label(self, name=None):
        self.channel_label.setText(f"Selected channel: {name or 'None'}")

    # === Video scraping ===
    def scrape_videos(self):
        channel_name = app_state.channel_name
        channel_id = app_state.channel_id
        channel_url = app_state.channel_url

        if not channel_name or not channel_id or not channel_url:
            print("No channel selected")
            return

        self.show_splash_screen()

        self.worker_thread = QtCore.QThread()
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

    # === Load videos ===
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

    def _format_duration(self, seconds):
        try:
            if seconds is None or seconds == "":
                return "--:--"
            seconds = int(float(seconds))
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
                return f"{views / 1_000_000:.1f}M"
            elif views >= 1_000:
                return f"{views / 1_000:.1f}K"
            return str(views)
        except Exception:
            return "0"