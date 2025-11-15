from PySide6.QtWidgets import (QWidget, QLabel, QGridLayout, QStyle, QPushButton,
                               QListView, QVBoxLayout, QAbstractItemView, QStyledItemDelegate,
                               QButtonGroup, QHBoxLayout, QFrame, QComboBox)
from PySide6.QtCore import (QThread, Qt, QSize, QRect, Property, QItemSelectionModel,
                            QItemSelection, QTimer, Signal)
from PySide6.QtGui import QStandardItemModel, QStandardItem, QPixmap, QPainter, QFont, QColor, QIcon
import os

from Data.DatabaseManager import DatabaseManager
from Backend.ScrapeVideo import VideoWorker
from UI.SplashScreen import SplashScreen
from utils.AppState import app_state
from utils.Config import const


def clear_layout(layout):
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget:
            widget.deleteLater()
        elif item.layout():
            clear_layout(item.layout())


class YouTubeVideoItem:
    def __init__(self, thumbnail: QPixmap, title: str, duration: str, views: str,
                 video_type: str, time_since_published: str = "", video_id: str = ""):
        self.thumbnail = thumbnail
        self.title = title
        self.duration = duration
        self.views = views
        self.video_type = video_type
        self.time_since_published = time_since_published
        self.video_id = video_id  # Added video_id for selection


class YouTubeVideoDelegate(QStyledItemDelegate):
    """Custom delegate for drawing YouTube videos and Shorts with grid and list layouts."""

    def paint(self, painter: QPainter, option, index):
        data = index.data(Qt.UserRole)
        if not data:
            return

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)

        # Highlight selected items
        painter.fillRect(option.rect, QColor("#263238") if option.state & QStyle.State_Selected else QColor("#0f0f0f"))

        view = option.widget
        is_list_mode = view.viewMode() == QListView.ListMode

        thumbnail = data.thumbnail
        title = data.title
        duration = data.duration
        views = data.views
        time_since_published = data.time_since_published

        # === LIST MODE ===
        if is_list_mode:
            target_height = 100
            target_width = 178

            if isinstance(thumbnail, QPixmap) and not thumbnail.isNull():
                scaled = thumbnail.scaled(target_width, target_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                painter.drawPixmap(option.rect.x() + 12, option.rect.y() + 10, scaled)

            # Text
            text_x = option.rect.x() + target_width + 24
            painter.setFont(QFont("Segoe UI", 11, QFont.Bold))
            painter.setPen(Qt.white)
            painter.drawText(QRect(text_x, option.rect.y() + 12, option.rect.width() - text_x, 40),
                             Qt.TextWordWrap, title)

            painter.setFont(QFont("Segoe UI", 9))
            painter.setPen(QColor("#AAAAAA"))
            painter.drawText(QRect(text_x, option.rect.y() + 60, option.rect.width() - text_x, 20),
                             Qt.AlignLeft, f"{views} views  ●  {time_since_published}")

        # === GRID MODE ===
        else:
            target_height = 144
            target_width = 256
            thumb_x = option.rect.x() + (option.rect.width() - target_width) // 2
            thumb_y = option.rect.y() + 8
            thumb_rect = QRect(thumb_x, thumb_y, target_width, target_height)

            if isinstance(thumbnail, QPixmap) and not thumbnail.isNull():
                scaled = thumbnail.scaled(target_width, target_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                painter.drawPixmap(thumb_x, thumb_y, scaled)

            # Duration overlay
            if duration:
                painter.setFont(QFont("Segoe UI", 9))
                painter.setPen(Qt.white)
                painter.fillRect(thumb_rect.right() - 50, thumb_rect.bottom() - 22, 45, 18, QColor(0, 0, 0, 180))
                painter.drawText(QRect(thumb_rect.right() - 50, thumb_rect.bottom() - 22, 45, 18),
                                 Qt.AlignCenter, duration)

            # Title and views
            painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
            painter.setPen(Qt.white)
            painter.drawText(QRect(thumb_x, thumb_rect.bottom() + 8, target_width, 40),
                             Qt.TextWordWrap, title)
            painter.setFont(QFont("Segoe UI", 9))
            painter.setPen(QColor("#AAAAAA"))
            painter.drawText(QRect(thumb_x, thumb_rect.bottom() + 48, target_width, 20),
                             Qt.AlignLeft, f"{views} views  ●  {time_since_published}")

        painter.restore()

    def sizeHint(self, option, index):
        if option.widget.viewMode() == QListView.ListMode:
            return QSize(option.rect.width(), 120)
        return QSize(280, 240)


class SelectableListView(QListView):
    """Custom QListView with smooth scrolling and drag selection."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.drag_start_index = None
        self.is_dragging = False
        self.auto_scroll_timer = QTimer(self)
        self.auto_scroll_timer.timeout.connect(self._auto_scroll)
        self.scroll_direction = 0
        self.last_mouse_pos = None
        
        # Enable smooth scrolling
        self.verticalScrollBar().setSingleStep(5)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            index = self.indexAt(event.pos())
            modifiers = event.modifiers()
            
            if index.isValid():
                if modifiers == Qt.ShiftModifier:
                    # Shift+Click: Select range
                    current_indexes = self.selectedIndexes()
                    if current_indexes:
                        # Get first selected index
                        first_index = min(current_indexes, key=lambda x: x.row())
                        self._select_range(first_index, index)
                    else:
                        super().mousePressEvent(event)
                elif modifiers == Qt.ControlModifier:
                    # Ctrl+Click: Toggle selection
                    super().mousePressEvent(event)
                else:
                    # Normal click: Start drag selection
                    self.drag_start_index = index
                    self.is_dragging = True
                    self.clearSelection()
                    self.selectionModel().select(index, QItemSelectionModel.Select)
            else:
                self.clearSelection()
                
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        self.last_mouse_pos = event.pos()
        
        if self.is_dragging and self.drag_start_index is not None:
            current_index = self.indexAt(event.pos())
            if current_index.isValid():
                self._select_range(self.drag_start_index, current_index)
            
            # Check if we need to auto-scroll
            viewport_rect = self.viewport().rect()
            margin = 50  # Pixels from edge to trigger scroll
            
            if event.pos().y() < margin:
                # Near top
                self.scroll_direction = -1
                if not self.auto_scroll_timer.isActive():
                    self.auto_scroll_timer.start(16)  # ~60 FPS
            elif event.pos().y() > viewport_rect.height() - margin:
                # Near bottom
                self.scroll_direction = 1
                if not self.auto_scroll_timer.isActive():
                    self.auto_scroll_timer.start(16)
            else:
                self.scroll_direction = 0
                self.auto_scroll_timer.stop()
        
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_dragging = False
            self.drag_start_index = None
            self.auto_scroll_timer.stop()
            self.scroll_direction = 0
        super().mouseReleaseEvent(event)
    
    def _select_range(self, start_index, end_index):
        """Select all items between start and end index."""
        self.clearSelection()
        start_row = min(start_index.row(), end_index.row())
        end_row = max(start_index.row(), end_index.row())
        
        selection = QItemSelection()
        for row in range(start_row, end_row + 1):
            index = self.model().index(row, 0)
            selection.select(index, index)
        
        self.selectionModel().select(selection, QItemSelectionModel.Select)
    
    def _auto_scroll(self):
        """Smoothly scroll the view when dragging near edges."""
        if self.scroll_direction == 0:
            return
        
        scroll_bar = self.verticalScrollBar()
        current_value = scroll_bar.value()
        
        # Smooth scrolling with variable speed
        if self.last_mouse_pos:
            viewport_rect = self.viewport().rect()
            if self.scroll_direction < 0:
                # Scrolling up
                distance = max(1, 50 - self.last_mouse_pos.y())
                speed = (distance / 2) + 1
                scroll_bar.setValue(int(current_value - speed))
            else:
                # Scrolling down
                distance = max(1, self.last_mouse_pos.y() - (viewport_rect.height() - 50))
                speed = (distance / 2) + 1
                scroll_bar.setValue(int(current_value + speed))
        
        # Continue drag selection while scrolling
        if self.is_dragging and self.drag_start_index is not None and self.last_mouse_pos:
            current_index = self.indexAt(self.last_mouse_pos)
            if current_index.isValid():
                self._select_range(self.drag_start_index, current_index)


class Video(QWidget):
    """YouTube video browser and scraper widget."""
    video_page_scrape_video_signal = Signal()
    video_page_scrape_transcript_signal = Signal()

    def __init__(self, parent=None):
        super(Video, self).__init__(parent)
        self.mainwindow = parent
        self.db: DatabaseManager = app_state.db

        self.splash = None
        self.worker_thread = None
        self.worker = None
        self.video_page_scrape_video_signal.connect(self.scrape_videos)

        # === Main layout ===
        self.main_layout = QGridLayout(self)
        self.setLayout(self.main_layout)

        # === Header controls ===
        self.channel_label_layout = QHBoxLayout()

        self.scrape_info_button = QPushButton("select and scrape info")
        self.scrape_info_button.clicked.connect(self.select_videos)

        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All", "Live", "Shorts", "Videos"])
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Longest", "Shortest", "Newest", "Oldest", "Most Viewed", "Least Viewed"])
        self.filter_combo.currentIndexChanged.connect(self.on_combo_changed)
        self.sort_combo.currentIndexChanged.connect(self.on_combo_changed)

        filter_sort_layout = QHBoxLayout()
        filter_sort_layout.addWidget(self.filter_combo)
        filter_sort_layout.addWidget(self.sort_combo)

        self.lang_combo = QComboBox()
        self.lang_combo.addItems([f'{name} ({code})' for code, name in const.YOUTUBE_LANGUAGE_CODES.items()])
        self.lang_combo.setCurrentText(f'English (en)')

        # === Segmented Control ===
        self._create_segmented_control()

        # === Video list - Use SelectableListView instead of QListView ===
        self.video_view = SelectableListView()
        self.video_view.setViewMode(QListView.IconMode)
        self.video_view.setResizeMode(QListView.Adjust)
        self.video_view.setFlow(QListView.LeftToRight)
        self.video_view.setWrapping(True)
        self.video_view.setSpacing(20)
        self.video_view.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.video_view.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.model = QStandardItemModel()
        self.video_view.setModel(self.model)
        self.video_delegate = YouTubeVideoDelegate(self.video_view)
        self.video_view.setItemDelegate(self.video_delegate)

        # === Layout ===
        self.main_layout.addWidget(self.segment_container, 0, 0, 1, 1, alignment=Qt.AlignLeft)
        self.main_layout.addLayout(filter_sort_layout, 0, 1, 1, 1, alignment=Qt.AlignLeft)
        self.main_layout.addLayout(self.channel_label_layout, 0, 2, 1, 2, alignment=Qt.AlignCenter)
        self.main_layout.addWidget(self.lang_combo, 0, 4, 1, 2, alignment=Qt.AlignRight)
        self.main_layout.addWidget(self.video_view, 1, 0, 1, 6)
        self.main_layout.addWidget(self.scrape_info_button, 2, 2, 1, 4, alignment=Qt.AlignCenter)

        # === Signals ===
        app_state.channel_info_changed.connect(self.update_channel_label)
        self.update_channel_label(app_state.channel_info)

    # --- Segmented Control ---
    def _create_segmented_control(self):
        self.segment_container = QFrame()
        layout = QHBoxLayout(self.segment_container)
        layout.setContentsMargins(0, 0, 0, 0)

        list_icon = QIcon(os.path.join(self.mainwindow.base_dir, "assets", "icon", "light", "light_list.ico"))
        grid_icon = QIcon(os.path.join(self.mainwindow.base_dir, "assets", "icon", "light", "light_grid.ico"))

        self.list_btn = QPushButton()
        self.list_btn.setIcon(list_icon)
        self.list_btn.setToolTip("List View")
        self.list_btn.setCheckable(True)
        self.list_btn.clicked.connect(self.on_list_clicked)

        self.grid_btn = QPushButton()
        self.grid_btn.setIcon(grid_icon)
        self.grid_btn.setToolTip("Grid View")
        self.grid_btn.setCheckable(True)
        self.grid_btn.setChecked(True)
        self.grid_btn.clicked.connect(self.on_grid_clicked)

        layout.addWidget(self.list_btn)
        layout.addWidget(self.grid_btn)

    # --- UI Actions ---
    def on_list_clicked(self):
        if self.list_btn.isChecked():
            self.grid_btn.setChecked(False)
            self.video_view.setViewMode(QListView.ListMode)
            self.video_view.setFlow(QListView.TopToBottom)
            self.video_view.setSpacing(6)
        else:
            self.list_btn.setChecked(True)
        print("List view selected")

    def on_grid_clicked(self):
        if self.grid_btn.isChecked():
            self.list_btn.setChecked(False)
            self.video_view.setViewMode(QListView.IconMode)
            self.video_view.setFlow(QListView.LeftToRight)
            self.video_view.setSpacing(20)
        else:
            self.grid_btn.setChecked(True)
        print("Grid view selected")

    # --- Scraping ---
    def scrape_videos(self):
        channel_info = app_state.channel_info

        if not channel_info:
            print("No channel selected")
            return

        else:
            channel_name = channel_info.get("channel_name")
            channel_id = channel_info.get("channel_id")
            channel_url = channel_info.get("channel_url")
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
        self.splash = SplashScreen(parent=self.mainwindow, gif_path=gif_path)
        self.splash.set_title("Scraping Videos (Videos, Shorts, Live)...")
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
        print("✅ Video scraping completed!")
        self.load_videos_from_db()

    # --- Loading videos ---
    def load_videos_from_db(self, where=None, order_by=None):
        channel_id = app_state.channel_info.get("channel_id")
        videos = self.db.fetch(
            table="VIDEO",
            where=f"channel_id=? AND {where}" if where else "channel_id=?",
            order_by=order_by,
            params=(channel_id,)
        )
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
            time_since_published = video.get("time_since_published")
            video_id = video.get("video_id")

            item_data = YouTubeVideoItem(pixmap, title, duration, views, video_type, time_since_published, video_id)
            item = QStandardItem()
            item.setData(item_data, Qt.UserRole)
            item.setEditable(False)
            self.model.appendRow(item)

        print(f"Loaded {self.model.rowCount()} videos for channel {channel_id}")

    # --- Helpers ---
    def _format_duration(self, duration):
        if not duration:
            return "--:--"
        try:
            return duration if ":" in str(duration) else f"{int(duration)//60}:{int(duration)%60:02}"
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

    def on_combo_changed(self):
        sort = self.sort_combo.currentText()
        filter = self.filter_combo.currentText()

        where = None if filter == "All" else f"video_type = '{filter.lower()}'"
        order_by = None
        if sort == "Longest":
            order_by = "duration_in_seconds DESC"
        elif sort == "Shortest":
            order_by = "duration_in_seconds ASC"
        elif sort == "Newest":
            order_by = "upload_timestamp DESC"
        elif sort == "Oldest":
            order_by = "upload_timestamp ASC"
        elif sort == "Most Viewed":
            order_by = "view_count DESC"
        elif sort == "Least Viewed":
            order_by = "view_count ASC"

        self.load_videos_from_db(where, order_by)

    def select_videos(self):
        selected_indexes = self.video_view.selectedIndexes()
        if not selected_indexes:
            print("No videos selected")
            return
        
        channel_id = app_state.channel_info.get("channel_id")
        video_ids = []
        
        for index in selected_indexes:
            item_data = index.data(Qt.UserRole)
            if item_data and item_data.video_id:
                video_ids.append(item_data.video_id)
        
        video_list = {channel_id: video_ids}
        app_state.video_list = video_list
        
        print(f"Selected {len(video_ids)} video(s) for channel {channel_id}")
        self.video_page_scrape_transcript_signal.emit()

    def update_channel_label(self, channel_info: dict = None):
        name = "None"
        clear_layout(self.channel_label_layout)
        self.channel_label_layout.addWidget(QLabel("Selected Channel: "), alignment=Qt.AlignLeft | Qt.AlignVCenter)
        if channel_info is not None:
            name = f' {channel_info.get("channel_name")}'
            img_label = QLabel()
            pix = QPixmap(channel_info.get("profile_pic")).scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            img_label.setPixmap(pix)
            self.channel_label_layout.addWidget(img_label, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        self.channel_label_layout.addWidget(QLabel(name), alignment=Qt.AlignLeft | Qt.AlignVCenter)
