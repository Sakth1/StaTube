from PySide6.QtWidgets import (QWidget, QLabel, QGridLayout, QStyle, QPushButton,
                               QListView, QVBoxLayout, QAbstractItemView, QStyledItemDelegate,
                               QCheckBox, QHBoxLayout, QFrame, QComboBox, QLayout, QStyleOptionViewItem)
from PySide6.QtCore import (QThread, Qt, QSize, QRect, Property, QItemSelectionModel,
                            QItemSelection, QTimer, Signal, QModelIndex)
from PySide6.QtGui import (QStandardItemModel, QStandardItem, QPixmap, QPainter, QFont, QColor, QIcon,)
from typing import Optional, Dict, List, Any
import os

from Data.DatabaseManager import DatabaseManager
from Backend.ScrapeVideo import VideoWorker
from Backend.ScrapeTranscription import TranscriptWorker
from Backend.ScrapeComments import CommentWorker
from UI.SplashScreen import SplashScreen, BlurOverlay
from utils.AppState import app_state
from utils.Logger import logger

def clear_layout(layout: QLayout) -> None:
    """
    Recursively clears items from the given layout.

    Args:
        layout (QLayout): The layout to clear.
    """
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget:
            # Delete the widget
            widget.deleteLater()
        elif item.layout():
            # Recursively clear the layout
            clear_layout(item.layout())


def extend_unique(base_list, new_items):
    """
    Extends a list with new items while ensuring uniqueness.

    Args:
        base_list (list): The list to extend.
        new_items (list): The new items to add to the list.

    Returns:
        list: The extended list with unique items.
    """
    seen = set(base_list)
    for item in new_items:
        if item not in seen:
            base_list.append(item)
            seen.add(item)
    return base_list


class YouTubeVideoItem:
    """
    Represents a YouTube video or short item.

    Attributes:
        thumbnail (QPixmap): The video thumbnail.
        title (str): The video title.
        duration (str): The video duration in the format "HH:MM:SS".
        views (str): The number of views for the video.
        video_type (str): The type of video (video or short).
        time_since_published (str): The time since the video was published.
        video_id (str): The ID of the video.
    """

    def __init__(self, thumbnail: QPixmap, title: str, duration: str, views: str,
                 video_type: str, time_since_published: str = "", video_id: str = "") -> None:
        """
        Initializes the YouTube video item.

        Parameters:
            thumbnail (QPixmap): The video thumbnail.
            title (str): The video title.
            duration (str): The video duration in the format "HH:MM:SS".
            views (str): The number of views for the video.
            video_type (str): The type of video (video or short).
            time_since_published (str): The time since the video was published.
            video_id (str): The ID of the video.
        """
        self.thumbnail = thumbnail
        self.title = title
        self.duration = duration
        self.views = views
        self.video_type = video_type
        self.time_since_published = time_since_published
        self.video_id = video_id  # Added video_id for selection


class YouTubeVideoDelegate(QStyledItemDelegate):
    """
    Custom delegate for drawing YouTube videos and Shorts with grid and list layouts.

    This delegate is responsible for painting and providing size hints for the YouTube video items.
    """

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        """
        Paints the YouTube video item.

        Parameters:
            painter (QPainter): The painter to use.
            option (QStyleOptionViewItem): The style option.
            index (QModelIndex): The index of the item to paint.
        """
        data: YouTubeVideoItem = index.data(Qt.UserRole)
        if not data:
            return

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)

        # Highlight selected items
        painter.fillRect(option.rect, QColor("#263238") if option.state & QStyle.State_Selected else QColor("#0f0f0f"))

        view: QListView = option.widget
        is_list_mode: bool = view.viewMode() == QListView.ListMode

        thumbnail: QPixmap = data.thumbnail
        title: str = data.title
        duration: str = data.duration
        views: str = data.views
        time_since_published: str = data.time_since_published

        # === LIST MODE ===
        if is_list_mode:
            target_height: int = 100
            target_width: int = 178

            if isinstance(thumbnail, QPixmap) and not thumbnail.isNull():
                scaled: QPixmap = thumbnail.scaled(target_width, target_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                painter.drawPixmap(option.rect.x() + 12, option.rect.y() + 10, scaled)

            # Text
            text_x: int = option.rect.x() + target_width + 24
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
            target_height: int = 144
            target_width: int = 256
            thumb_x: int = option.rect.x() + (option.rect.width() - target_width) // 2
            thumb_y: int = option.rect.y() + 8
            thumb_rect: QRect = QRect(thumb_x, thumb_y, target_width, target_height)

            if isinstance(thumbnail, QPixmap) and not thumbnail.isNull():
                scaled: QPixmap = thumbnail.scaled(target_width, target_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
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

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        """
        Returns the size hint for the YouTube video item.

        Parameters:
            option (QStyleOptionViewItem): The style option.
            index (QModelIndex): The index of the item to get the size hint for.

        Returns:
            QSize: The size hint.
        """
        if option.widget.viewMode() == QListView.ListMode:
            return QSize(option.rect.width(), 120)
        return QSize(280, 240)


class SelectableListView(QListView):
    """
    Custom QListView with smooth scrolling and drag selection.
    
    This class extends QListView to provide smooth scrolling and drag selection.
    """
    
    def __init__(self, parent=None):
        """
        Initialize the SelectableListView object.
        
        :param parent: The parent widget.
        :type parent: Optional[QWidget]
        """
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
        """
        Handle mouse press event.
        
        :param event: The mouse press event.
        :type event: QMouseEvent
        """
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
        """
        Handle mouse move event.
        
        :param event: The mouse move event.
        :type event: QMouseEvent
        """
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
        """
        Handle mouse release event.
        
        :param event: The mouse release event.
        :type event: QMouseEvent
        """
        if event.button() == Qt.LeftButton:
            self.is_dragging = False
            self.drag_start_index = None
            self.auto_scroll_timer.stop()
            self.scroll_direction = 0
        super().mouseReleaseEvent(event)
    
    def _select_range(self, start_index, end_index):
        """
        Select all items between start and end index.
        
        :param start_index: The start index.
        :param end_index: The end index.
        :type start_index: QModelIndex
        :type end_index: QModelIndex
        """
        self.clearSelection()
        start_row = min(start_index.row(), end_index.row())
        end_row = max(start_index.row(), end_index.row())
        
        selection = QItemSelection()
        for row in range(start_row, end_row + 1):
            index = self.model().index(row, 0)
            selection.select(index, index)
        
        self.selectionModel().select(selection, QItemSelectionModel.Select)
    
    def _auto_scroll(self):
        """
        Smoothly scroll the view when dragging near edges.
        """
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
    video_page_scrape_video_signal = Signal(bool)
    video_page_scrape_transcript_signal = Signal()
    video_page_scrape_comments_signal = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initializes the Video widget.

        Parameters:
            parent (Optional[QWidget]): The parent widget.

        Notes:
            Connects the video_page_scrape_video_signal to the scrape_videos slot.
            Sets up the main layout, header controls, and video list.
            Connects the channel_info_changed signal to the update_channel_label slot.
        """
        super(Video, self).__init__(parent)
        self.mainwindow: Optional[QWidget] = parent
        self.db: DatabaseManager = app_state.db

        self.splash: Optional[SplashScreen] = None
        self.worker_thread: Optional[QThread] = None
        self.worker: Optional[VideoWorker] = None
        
        # Workers for transcript and comments
        self.transcript_thread: Optional[QThread] = None
        self.transcript_worker: Optional[TranscriptWorker] = None
        self.comment_thread: Optional[QThread] = None
        self.comment_worker: Optional[CommentWorker] = None

        self.video_page_scrape_video_signal.connect(self.scrape_videos)

        # === Main layout ===
        self.main_layout: QGridLayout = QGridLayout(self)
        self.setLayout(self.main_layout)

        # === Header controls ===
        self.channel_label_layout: QHBoxLayout = QHBoxLayout()

        bottom_layout: QHBoxLayout = QHBoxLayout()
        self.add_to_list_button: QPushButton = QPushButton("Add to list")
        self.add_to_list_button.clicked.connect(self.add_to_list)
        self.scrape_transcript_button: QPushButton = QPushButton("Scrape Transcript")
        self.scrape_transcript_button.clicked.connect(self.scrape_transcript)
        self.scrape_comments_button: QPushButton = QPushButton("Scrape Comments")
        self.scrape_comments_button.clicked.connect(self.scrape_comments)
        bottom_layout.addWidget(self.scrape_transcript_button)
        bottom_layout.addWidget(self.add_to_list_button, stretch=2)
        bottom_layout.addWidget(self.scrape_comments_button)

        self.filter_combo: QComboBox = QComboBox()
        self.filter_combo.addItems(["All", "Live", "Shorts", "Videos"])
        self.sort_combo: QComboBox = QComboBox()
        self.sort_combo.addItems(["Longest", "Shortest", "Newest", "Oldest", "Most Viewed", "Least Viewed"])
        self.filter_combo.currentIndexChanged.connect(lambda:self.on_combo_changed(self.sort_combo.currentText(), self.filter_combo.currentText()))
        self.sort_combo.currentIndexChanged.connect(lambda: self.on_combo_changed(self.sort_combo.currentText(), self.filter_combo.currentText()))

        self.scrape_shorts_checkbox: QCheckBox = QCheckBox("Scrape Shorts")
        self.scrape_shorts_checkbox.setChecked(False)

        filter_sort_layout: QHBoxLayout = QHBoxLayout()
        filter_sort_layout.addWidget(self.filter_combo)
        filter_sort_layout.addWidget(self.sort_combo)

        # === Segmented Control ===
        self._create_segmented_control()

        # === Video list - Use SelectableListView instead of QListView ===
        self.video_view: SelectableListView = SelectableListView()
        self.video_view.setViewMode(QListView.IconMode)
        self.video_view.setResizeMode(QListView.Adjust)
        self.video_view.setFlow(QListView.LeftToRight)
        self.video_view.setWrapping(True)
        self.video_view.setSpacing(20)
        self.video_view.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.video_view.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.model: QStandardItemModel = QStandardItemModel()
        self.video_view.setModel(self.model)
        self.video_delegate: YouTubeVideoDelegate = YouTubeVideoDelegate(self.video_view)
        self.video_view.setItemDelegate(self.video_delegate)

        # === Layout ===
        self.main_layout.addWidget(self.segment_container, 0, 0, 1, 1, alignment=Qt.AlignLeft)
        self.main_layout.addLayout(filter_sort_layout, 0, 1, 1, 1, alignment=Qt.AlignLeft)
        self.main_layout.addLayout(self.channel_label_layout, 0, 2, 1, 3, alignment=Qt.AlignCenter)
        self.main_layout.addWidget(self.scrape_shorts_checkbox, 0, 5, 1, 1, alignment=Qt.AlignRight)
        self.main_layout.addWidget(self.video_view, 1, 0, 1, 6)
        self.main_layout.addLayout(bottom_layout, 2, 1, 1, 4, alignment=Qt.AlignCenter)

        # === Signals ===
        app_state.channel_info_changed.connect(self.update_channel_label)
        self.update_channel_label(app_state.channel_info)

    # --- Segmented Control ---
    def _create_segmented_control(self) -> None:
        """
        Creates the segmented control with list and grid buttons.

        :return: None
        """
        self.segment_container = QFrame()
        layout = QHBoxLayout(self.segment_container)
        layout.setContentsMargins(0, 0, 0, 0)

        list_icon: QIcon = QIcon(os.path.join(self.mainwindow.base_dir, "assets", "icon", "light", "light_list.ico"))
        grid_icon: QIcon = QIcon(os.path.join(self.mainwindow.base_dir, "assets", "icon", "light", "light_grid.ico"))

        self.list_btn: QPushButton = QPushButton()
        self.list_btn.setIcon(list_icon)
        self.list_btn.setToolTip("List View")
        self.list_btn.setCheckable(True)
        self.list_btn.clicked.connect(self.on_list_clicked)

        self.grid_btn: QPushButton = QPushButton()
        self.grid_btn.setIcon(grid_icon)
        self.grid_btn.setToolTip("Grid View")
        self.grid_btn.setCheckable(True)
        self.grid_btn.setChecked(True)
        self.grid_btn.clicked.connect(self.on_grid_clicked)

        layout.addWidget(self.list_btn)
        layout.addWidget(self.grid_btn)

    # --- UI Actions ---
    def on_list_clicked(self, checked: bool) -> None:
        """
        Triggered when the list button is clicked.

        If the list button is checked, it unchecks the grid button and
        sets the view mode of the video view to ListMode, with a flow of
        TopToBottom, and a spacing of 6 pixels. If the list button is
        unchecked, it checks the list button.

        :param checked: Whether the list button is checked.
        :type checked: bool
        :return: None
        :rtype: None
        """
        if checked:
            self.grid_btn.setChecked(False)
            self.video_view.setViewMode(QListView.ListMode)
            self.video_view.setFlow(QListView.TopToBottom)
            self.video_view.setSpacing(6)
        else:
            self.list_btn.setChecked(True)

    def on_grid_clicked(self, checked: bool) -> None:
        """
        Triggered when the grid button is clicked.

        If the grid button is checked, it unchecks the list button and
        sets the view mode of the video view to IconMode, with a flow of
        LeftToRight, and a spacing of 20 pixels. If the grid button is
        unchecked, it checks the grid button.

        :param checked: Whether the grid button is checked.
        :type checked: bool
        :return: None
        :rtype: None
        """
        if checked:
            self.list_btn.setChecked(False)
            self.video_view.setViewMode(QListView.IconMode)
            self.video_view.setFlow(QListView.LeftToRight)
            self.video_view.setSpacing(20)
        else:
            self.grid_btn.setChecked(True)

    # --- Scraping ---
    def scrape_videos(self, scrape_shorts: bool) -> None:
        """
        Start scraping videos from the selected channel.

        This function will start a new thread to scrape videos from the selected channel.
        It will show a splash screen while the scraping is in progress.

        If no channel is selected, it will simply return without doing anything.

        :param scrape_shorts: Whether to scrape shorts or not.
        :type scrape_shorts: bool
        :return None
        :rtype: None
        """
        channel_info: dict[str, str] = app_state.channel_info

        if not channel_info:
            logger.warning("No channel selected for video scraping")
            return

        else:
            channel_name: str = channel_info.get("channel_name")
            channel_id: str = channel_info.get("channel_id")
            channel_url: str = channel_info.get("channel_url")
        self.show_splash_screen()

        self.worker_thread: QThread = QThread()
        self.worker = VideoWorker(channel_id, channel_url, scrape_shorts)
        self.worker.moveToThread(self.worker_thread)

        self.worker_thread.started.connect(self.worker.run)
        self.worker.progress_updated.connect(self.update_splash_progress)
        self.worker.progress_percentage.connect(self.update_splash_percentage)
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker_thread.start()

    def show_splash_screen(self, parent: Optional[QWidget] = None, gif_path: str = "", title: str = "Scraping Videos...") -> None:
        cwd = os.getcwd()
        gif_path = os.path.join(cwd, "assets", "gif", "loading.gif") if not gif_path else gif_path

        if self.splash:
            self.splash.close()
            self.splash = None

        # ✅ IMPORTANT FIX: parent MUST be None
        self.splash = SplashScreen(parent=None, gif_path=gif_path)

        self.splash.set_title(title)
        self.splash.update_status("Starting...")
        self.splash.set_progress(0)

        # ✅ Overlay still binds to mainwindow correctly
        self.splash.enable_runtime_mode(
            parent_window=self.mainwindow,
            cancel_callback=self.cancel_scraping
        )

        self.splash.show_with_animation()
        self.splash.raise_()
        self.splash.activateWindow()
        """QTimer.singleShot(5 * 60 * 1000, self._force_close_stuck_splash)

    def _force_close_stuck_splash(self):
        if self.splash:
            logger.error("FORCE closing stuck splash!")
            self.splash.fade_and_close(300)
            self.splash = None"""

    def cancel_scraping(self):
        """
        Called when user presses Cancel on splash screen.
        Safely stops active workers and closes splash + overlays.
        """
        logger.warning("User cancelled scraping operation.")

        # --- Stop video scraping ---
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.requestInterruption()
            self.worker_thread.quit()
            self.worker_thread.wait(500)

        # --- Stop transcript scraping ---
        if self.transcript_thread and self.transcript_thread.isRunning():
            self.transcript_thread.requestInterruption()
            self.transcript_thread.quit()
            self.transcript_thread.wait(500)

        # --- Stop comment scraping ---
        if self.comment_thread and self.comment_thread.isRunning():
            self.comment_thread.requestInterruption()
            self.comment_thread.quit()
            self.comment_thread.wait(500)

        # ✅ Force-remove overlays
        self._clear_overlays()

        # Fade & cleanup splash safely
        if self.splash:
            self.splash.fade_and_close(300)
            self.splash = None

    def _clear_overlays(self) -> None:
        """
        Force-close any BlurOverlay widgets still attached to the main window.
        This prevents the UI from staying dimmed if the splash fails to fully clean up.
        """
        if self.mainwindow is None:
            return

        # Close every BlurOverlay child of the main window
        for overlay in self.mainwindow.findChildren(BlurOverlay):
            overlay.close()

    def update_splash_progress(self, message: str) -> None:
        """
        Updates the status message of the SplashScreen dialog.

        Args:
            message (str): The status message to display.
        """
        if self.splash:
            self.splash.update_status(message)

    def update_splash_percentage(self, percentage: int) -> None:
        """
        Updates the progress bar of the SplashScreen dialog.

        Args:
            percentage (int): The progress percentage (0-100) to display.
        """
        if self.splash:
            self.splash.set_progress(percentage)

    def on_worker_finished(self) -> None:
        """
        Called when the VideoWorker thread has finished scraping videos.

        Closes the SplashScreen dialog if it exists and prints a completion message.
        Then, loads the videos from the database into the video list widget.

        :return None
        :rtype: None
        """
        self._clear_overlays()

        if self.splash:
            self.splash.fade_and_close(400)
            self.splash = None

        logger.info("Video scraping completed!")
        self.load_videos_from_db()

    def on_transcript_worker_finished(self) -> None:
        """
        Called when the TranscriptWorker thread has finished scraping transcripts.
        Closes the SplashScreen dialog.
        """
        self._clear_overlays()

        if self.splash is not None:
            self.splash.fade_and_close(400)
            self.splash = None
        self.video_page_scrape_transcript_signal.emit()
    
    def on_comment_worker_finished(self) -> None:
        """
        Called when the CommentWorker thread has finished scraping comments.
        Closes the SplashScreen dialog.
        """
        self._clear_overlays()

        if self.splash is not None:
            self.splash.fade_and_close(400)
            self.splash = None
        self.video_page_scrape_comments_signal.emit()

    # --- Loading videos ---
    def load_videos_from_db(
        self,
        where: Optional[str] = None,
        order_by: Optional[str] = None
    ) -> None:
        """
        Loads videos from the database into the video list widget.

        Args:
            where (Optional[str], optional): SQL WHERE clause to filter videos. Defaults to None.
            order_by (Optional[str], optional): SQL ORDER BY clause to sort videos. Defaults to None.

        Returns:
            None
        """
        channel_id: int = app_state.channel_info.get("channel_id", 0)
        videos: List[Dict[str, Any]] = self.db.fetch(
            table="VIDEO",
            where=f"channel_id=? AND {where}" if where else "channel_id=?",
            order_by=order_by,
            params=(channel_id,)
        )
        self.model.clear()

        for video in videos:
            thumb_path: str = os.path.join(self.db.thumbnail_dir, str(channel_id), f"{video['video_id']}.png")
            if not os.path.exists(thumb_path):
                logger.debug(f"Thumbnail missing for video_id={video['video_id']}")
                continue
            pixmap: QPixmap = QPixmap(thumb_path)
            if pixmap.isNull():
                continue

            duration: str = self._format_duration(video.get("duration", 0))
            views: str = self._format_views(video.get("view_count", 0))
            title: str = video.get("title", "Untitled")
            video_type: str = video.get("video_type", "video").lower()
            time_since_published: str = video.get("time_since_published", "")
            video_id: str = video.get("video_id", "")

            item_data: YouTubeVideoItem = YouTubeVideoItem(pixmap, title, duration, views, video_type, time_since_published, video_id)
            item: QStandardItem = QStandardItem()
            item.setData(item_data, Qt.UserRole)
            item.setEditable(False)
            self.model.appendRow(item)

        logger.info(f"Loaded {self.model.rowCount()} videos for channel {channel_id}")

    def _format_duration(self, duration: Optional[int]) -> str:
        """
        Formats a duration in seconds to a string in the format "HH:MM".
        
        Args:
            duration (Optional[int]): The duration in seconds. Defaults to None.
        
        Returns:
            str: The formatted duration string.
        """
        if duration is None:
            return "--:--"
        try:
            return str(duration) if ":" in str(duration) else f"{int(duration)//60}:{int(duration)%60:02}"
        except Exception:
            return "--:--"

    def _format_views(self, views: int) -> str:
        """
        Formats a view count to a string in the format "X.XM" or "X.XK" if the view count is above 1 million or 1 thousand, respectively.

        Args:
            views (int): The view count.

        Returns:
            str: The formatted view count string.
        """
        if views >= 1_000_000:
            return f"{views / 1_000_000:.1f}M"
        elif views >= 1_000:
            return f"{views / 1_000:.1f}K"
        return str(views)

    def on_combo_changed(self, sort: str, filter: str) -> None:
        """
        Triggered when the sort or filter combo boxes are changed.

        Retrieves videos from the database based on the selected filter and sort
        options, and loads them into the video list view.

        Parameters:
            sort (str): The selected sort option.
            filter (str): The selected filter option.

        Returns:
            None
        """
        where_clause: Optional[str] = None if filter == "All" else f"video_type = '{filter.lower()}'"
        order_by_clause: Optional[str] = None
        if sort == "Longest":
            order_by_clause = "duration_in_seconds DESC"
        elif sort == "Shortest":
            order_by_clause = "duration_in_seconds ASC"
        elif sort == "Newest":
            order_by_clause = "upload_timestamp DESC"
        elif sort == "Oldest":
            order_by_clause = "upload_timestamp ASC"
        elif sort == "Most Viewed":
            order_by_clause = "view_count DESC"
        elif sort == "Least Viewed":
            order_by_clause = "view_count ASC"

        self.load_videos_from_db(where_clause, order_by_clause)

    def select_videos(self) -> Dict[int, List[str]]:
        """
        Retrieves the selected video IDs from the video list view and returns a video list dictionary.

        Returns a dictionary containing the channel ID as the key and a list of video IDs as the value.

        Parameters:
            None

        Returns:
            Dict[int, List[str]]: A dictionary containing the channel ID and a list of video IDs.
        """
        selected_indexes: List[QModelIndex] = self.video_view.selectedIndexes()
        if not selected_indexes:
            logger.warning("No videos selected in video page")
            return {}
        
        channel_id: int = app_state.channel_info.get("channel_id", 0)
        video_ids: List[str] = []
        
        for index in selected_indexes:
            item_data: YouTubeVideoItem = index.data(Qt.UserRole)
            if item_data and item_data.video_id:
                video_ids.append(item_data.video_id)
        
        video_list: Dict[int, List[str]] = {channel_id: video_ids}
        return video_list

    def add_to_list(self) -> Dict[int, List[str]]:
        """
        Adds the selected videos to the video list stored in the application state.

        Retrieves the selected video IDs from the video list view, and extends the
        existing video list stored in the application state with the selected videos.

        If the video list for the channel already exists in the application state, it
        updates the list by adding the selected videos to it. If the video list does not
        exist, it creates a new list with the selected videos.

        Parameters:
            video_list (Dict[int, List[str]]): A dictionary containing the channel ID as the key and a list of video IDs as the value.

        Returns:
            Dict[int, List[str]]: The updated video list stored in the application state.
        """
        video_list: Dict[int, List[str]] = self.select_videos()
        existing_video_list: Dict[int, List[str]] = app_state.video_list
        if existing_video_list is not None:
            for key in list(existing_video_list.keys()):
                if key in list(video_list.keys()):
                    video_list[key] = extend_unique(existing_video_list[key], video_list[key])

        app_state.video_list = video_list
        return app_state.video_list

    def scrape_transcript(self) -> None:
        """
        Retrieves the selected video IDs from the video list view and emits a signal to scrape the video transcripts.

        Retrieves the selected video IDs from the video list view, and emits the video_page_scrape_transcript_signal
        to scrape the video transcripts.

        Parameters:
            None

        Returns:
            None
        """
        video_list: Dict[int, List[str]] = app_state.video_list
        if not video_list:
            logger.warning("No videos in list to scrape comments")
            return
        
        self.show_splash_screen(title="Scraping Transcripts...")
        
        self.transcript_thread = QThread()
        self.transcript_worker = TranscriptWorker(video_list)
        self.transcript_worker.moveToThread(self.transcript_thread)
        
        self.transcript_thread.started.connect(self.transcript_worker.run)
        self.transcript_worker.progress_updated.connect(self.update_splash_progress)
        self.transcript_worker.progress_percentage.connect(self.update_splash_percentage)
        self.transcript_worker.finished.connect(self.on_transcript_worker_finished)
        self.transcript_worker.finished.connect(self.transcript_thread.quit)
        self.transcript_worker.finished.connect(self.transcript_worker.deleteLater)
        self.transcript_thread.finished.connect(self.transcript_thread.deleteLater)
        
        self.transcript_thread.start()

    def scrape_comments(self) -> None:
        """
        Retrieves the selected video IDs from the video list view and emits a signal to scrape the video comments.

        Retrieves the selected video IDs from the video list view, and emits the video_page_scrape_comments_signal
        to scrape the video comments.

        Parameters:
            None

        Returns:
            None
        """
        video_list: Dict[int, List[str]] = app_state.video_list
        if not video_list:
            print("No videos in list to scrape comments.")
            return

        self.show_splash_screen(title="Scraping Comments...")

        self.comment_thread = QThread()
        self.comment_worker = CommentWorker(video_list)
        self.comment_worker.moveToThread(self.comment_thread)

        self.comment_thread.started.connect(self.comment_worker.run)
        self.comment_worker.progress_updated.connect(self.update_splash_progress)
        self.comment_worker.progress_percentage.connect(self.update_splash_percentage)
        self.comment_worker.finished.connect(self.on_comment_worker_finished)
        self.comment_worker.finished.connect(self.comment_thread.quit)
        self.comment_worker.finished.connect(self.comment_worker.deleteLater)
        self.comment_thread.finished.connect(self.comment_thread.deleteLater)

        self.comment_thread.start()

    def update_channel_label(self, channel_info: Optional[Dict[str, Any]] = None) -> None:
        """
        Updates the channel label with the selected channel information.

        If channel_info is not None, the channel name and profile picture are retrieved and
        displayed in the channel label layout.

        Parameters:
            channel_info (dict[str, Any]): A dictionary containing the selected channel information.
        Returns:
            None
        """
        name = "None"
        clear_layout(self.channel_label_layout)
        self.channel_label_layout.addWidget(QLabel("Selected Channel: "), alignment=Qt.AlignLeft | Qt.AlignVCenter)
        if channel_info is not None:
            name = f' {channel_info.get("channel_name", "")}'
            img_label = QLabel()
            pix = QPixmap(channel_info.get("profile_pic", "")).scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            img_label.setPixmap(pix)
            self.channel_label_layout.addWidget(img_label, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        self.channel_label_layout.addWidget(QLabel(name), alignment=Qt.AlignLeft | Qt.AlignVCenter)