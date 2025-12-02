from PySide6 import QtCore
from PySide6.QtWidgets import (QApplication, QMainWindow, QStackedWidget, QWidget, 
                               QLineEdit, QListWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QListWidgetItem, QCompleter, QGridLayout)
from PySide6.QtCore import Qt, QStringListModel, QSize, Signal
from PySide6.QtGui import QPixmap, QIcon, QPalette, QColor
import threading
import traceback
from typing import Optional, Dict, List, Any, Callable

from Data.DatabaseManager import DatabaseManager
from Backend.ScrapeChannel import Search
from utils.AppState import app_state
from utils.logger import logger
from UI.SplashScreen import SplashScreen
import os

class Home(QWidget):
    """
    Main home widget for channel search and selection functionality.
    
    This widget provides a search interface for YouTube channels, allowing users to:
    - Search for channels by keyword with auto-completion
    - View search results with channel information
    - Select channels for detailed scraping
    
    Attributes:
        results_ready (Signal): Emitted when search results are ready with list of channel names
        search_complete (Signal): Emitted when final search operation completes
        progress_update (Signal): Emitted to update progress bar with (progress: int, status: str)
        show_splash_signal (Signal): Signal to display splash screen
        close_splash_signal (Signal): Signal to close splash screen
        home_page_scrape_video_signal (Signal): Signal to initiate video scraping from home page
        videos (dict): Storage for video information
        video_url (list): List of video URLs
        live (dict): Storage for live stream information
        shorts (dict): Storage for YouTube shorts information
        content (dict): General content storage
    """
    results_ready = Signal(list)
    search_complete = Signal()  # Changed to simple signal
    progress_update = Signal(int, str)  # New signal for progress updates
    show_splash_signal = Signal()  # Signal to show splash
    close_splash_signal = Signal()  # Signal to close splash
    home_page_scrape_video_signal = Signal()
    
    videos = {}
    video_url = []
    live = {}
    shorts = {}
    content = {}

    def __init__(self, parent: Optional[QMainWindow] = None) -> None:
        """
        Initialize the Home widget.
        
        Sets up the UI components, database connection, search functionality,
        and signal-slot connections for asynchronous operations.
        
        Args:
            parent: Parent QMainWindow widget, defaults to None
        """
        super(Home, self).__init__(parent)

        self.mainwindow = parent
        self.db: DatabaseManager = app_state.db
        self.search = Search()
        self.splash = None

        self.top_panel = QWidget()
        self.central_layout = QVBoxLayout()
        self.central_widget = QStackedWidget()
        
        # Replace ComboBox with LineEdit and ListWidget
        self.searchbar = QLineEdit()
        self.select_scrape_button = QPushButton("Select and scrape info")
        self.channel_list = QListWidget()
        self.model = QStringListModel()
        self.completer = QCompleter(self.model, self.searchbar)
        self.select_scrape_button.clicked.connect(self.select_channel)
        self.completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)
        self.searchbar.setCompleter(self.completer)
        self.searchbar.mousePressEvent = lambda event, e=self.searchbar.mousePressEvent: (e(event), self.completer.complete())
        self.searchbar.focusInEvent = lambda event, e=self.searchbar.focusInEvent: (e(event), self.completer.complete())

        self.completer_active = False

        self.search_timer = QtCore.QTimer()
        self.stop_event = threading.Event()
        self.search_thread_instance = None
        self.channels = None
        self.search_channel_button = QPushButton("Search")

        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(lambda: self.search_keyword(self.searchbar.text()))
        
        # Setup search components
        self.searchbar.setPlaceholderText("Search")
        self.searchbar.textChanged.connect(self.reset_search_timer)
        self.completer.activated.connect(self.on_completer_activated)
        
        self.search_channel_button.clicked.connect(self.search_channel)
        
        # Connect signals to slots
        self.results_ready.connect(self.update_results)
        self.search_complete.connect(self.on_search_complete)
        self.progress_update.connect(self.on_progress_update)
        self.show_splash_signal.connect(self.show_search_splash)
        self.close_splash_signal.connect(self.close_splash)

        self.setupUi()
        self.setLayout(self.central_layout)
        self.central_layout.addWidget(self.top_panel)

    def on_completer_activated(self, text: str) -> None:
        """
        Handle completer selection event.
        
        When user selects an item from the auto-complete dropdown, this method
        stops any pending search operations and temporarily sets the completer_active flag.
        
        Args:
            text: The text that was selected from the completer
        """
        self.completer_active = True
        self.search_timer.stop()  # Stop any pending search
        # Reset flag after a short delay
        QtCore.QTimer.singleShot(50, lambda: setattr(self, 'completer_active', False))
    
    def setupUi(self) -> None:
        """
        Set up the user interface of the main window.
        
        Initializes and arranges all UI components in their proper layout.
        """
        self.setuptop()

    def setuptop(self) -> None:
        """
        Set up the top panel of the home widget.
        
        Creates a grid layout containing:
        - Search bar (row 0, col 0)
        - Search button (row 0, col 1)
        - Select and scrape button (row 2, cols 0-1)
        """
        self.top_layout = QGridLayout()
        self.top_panel.setLayout(self.top_layout)
        self.top_layout.addWidget(self.searchbar, 0, 0, alignment=Qt.AlignTop)
        self.top_layout.addWidget(self.search_channel_button, 0, 1)
        self.top_layout.addWidget(self.select_scrape_button, 2, 0, 1, 2, alignment=Qt.AlignBottom)
        self.top_panel.show()

    def select_channel(self) -> None:
        """
        Handle channel selection from the channel list.
        
        Extracts channel information from the currently selected list item,
        stores it in the application state, and emits a signal to initiate
        video scraping for the selected channel.
        
        The channel information includes:
        - channel_name: Display name of the channel
        - channel_id: Unique identifier for the channel
        - channel_url: URL to the channel page
        - profile_pic: Path to the channel's profile picture
        """
        item = self.channel_list.currentItem()
        channel_info = {}
        if item:
            data = item.data(Qt.UserRole)
            channel_info['channel_name'] = data['channel_name']
            channel_info['channel_id'] = data['channel_id']
            channel_info['channel_url'] = data['channel_url']
            channel_info['profile_pic'] = data['profile_pic']
            app_state.channel_info = channel_info
        
        self.home_page_scrape_video_signal.emit()

    def reset_search_timer(self) -> None:
        """
        Reset the search timer for debounced search functionality.
        
        Starts a 5ms timer before triggering a search. This provides a debounce
        effect to avoid excessive search operations while the user is typing.
        Only resets the timer if the completer is not currently active.
        """
        if not self.completer_active:
            self.search_timer.start(5)

    def on_item_selected(self, item: QListWidgetItem) -> None:
        """
        Handle item selection from dropdown.
        
        Updates the search bar text with the selected item and returns focus
        to the search bar for continued interaction.
        
        Args:
            item: The QListWidgetItem that was selected
        """
        if item:
            self.searchbar.blockSignals(True)
            selected_text = item.text()
            self.searchbar.setText(selected_text)
            # Return focus to input after selection
            QtCore.QTimer.singleShot(10, lambda: self.searchbar.setFocus())
            self.searchbar.blockSignals(False)

    @QtCore.Slot()
    def show_search_splash(self) -> None:
        """
        Show splash screen for search operation.
        
        Creates and displays a splash screen with an animated loading GIF
        to provide visual feedback during channel search operations.
        """
        cwd = os.getcwd()
        gif_path = os.path.join(cwd, "assets", "gif", "loading.gif")
        self.splash = SplashScreen(parent=self.mainwindow, gif_path=gif_path)
        self.splash.set_title("Searching Channels...")
        self.splash.update_status("Fetching channel information...")
        self.splash.show()

    @QtCore.Slot(int, str)
    def on_progress_update(self, progress: int, status: str) -> None:
        """
        Update splash screen progress.
        
        Updates the progress bar and status message on the splash screen
        during long-running search operations.
        
        Args:
            progress: Progress percentage (0-100), or -1 to skip progress bar update
            status: Status message to display on the splash screen
        """
        if self.splash:
            if progress >= 0:  # Only update progress bar for numeric values
                self.splash.set_progress(progress)
            if status:
                self.splash.update_status(status)

    @QtCore.Slot()
    def close_splash(self) -> None:
        """
        Close splash screen.
        
        Closes and cleans up the splash screen instance if it exists.
        """
        if self.splash:
            self.splash.close()
            self.splash = None

    def update_results(self, channels: List[str]) -> None:
        """
        Update dropdown list with search results.
        
        Populates the auto-complete dropdown with channel names from
        the search results and triggers the completer to display them.
        
        Args:
            channels: List of channel names to display in the dropdown
        """
        if channels:
            self.model.setStringList(channels)
            self.completer.complete()
    
    @QtCore.Slot()
    def on_search_complete(self) -> None:
        """
        Handle completion of final search with downloads.
        
        Called when the final comprehensive search operation completes.
        Updates the UI with the full channel list and closes the splash screen.
        """
        logger.info("Final search complete, updating UI...")
        self.update_channel_list()
        self.close_splash()

    @QtCore.Slot()
    def update_channel_list(self) -> None:
        """
        Update the channel list widget with search results.
        
        Populates the channel list widget with detailed information about each
        channel including profile picture, name, and subscriber count. Retrieves
        additional information from the database if available.
        
        Each list item stores channel data including:
        - channel_id: Unique channel identifier
        - channel_name: Display name
        - channel_url: Channel URL
        - profile_pic: Path to profile picture
        - sub_count: Subscriber count
        """
        self.channel_list.clear()
        if not self.channels:
            return

        # Create a copy of channels to avoid iteration issues
        channels_copy = self.channels.copy()
        
        for channel_id, info in channels_copy.items():
            inf = self.db.fetch(table="CHANNEL", where="channel_id=?", params=(channel_id,))
            if not inf:
                # No DB row found — use sensible defaults and warn
                channel_name = info.get("title", "Unknown")
                logger.warning(f"No DB entry for channel_id={channel_id}")
                sub_count = 0
                profile_pic = None
            else:
                row = inf[0]
                sub_count = row.get("sub_count") or 0
                channel_name = row.get("name") or info.get("title", "Unknown")
                profile_pic = row.get("profile_pic")

            icon = QIcon(profile_pic) if profile_pic else QIcon()
            text_label = f'{channel_name}\n{sub_count}'
            item = QListWidgetItem(icon, text_label)
            item.setData(Qt.UserRole, {
                "channel_id": channel_id,
                "channel_name": channel_name,
                "channel_url": info.get('url'),
                "profile_pic": profile_pic,
                "sub_count": sub_count
            })
            self.channel_list.addItem(item)

        self.channel_list.setIconSize(QSize(32, 32))
        # add widget to layout only if not already present
        if self.top_layout.itemAtPosition(1, 0) is None:
            self.top_layout.addWidget(self.channel_list, 1, 0, 1, 2)

    def search_keyword(self, query: str, final: bool = False) -> None:
        """
        Initiate a channel search operation.
        
        Starts a background thread to search for channels matching the given query.
        Handles cancellation of existing search threads before starting a new one.
        
        Args:
            query: Search keyword or channel name
            final: If True, performs a comprehensive search with progress tracking
                  and downloads. If False, performs a quick limited search for
                  auto-complete suggestions. Defaults to False.
        """
        try:
            # Signal any existing thread to stop
            if self.search_thread_instance and self.search_thread_instance.is_alive():
                self.stop_event.set()
                logger.debug("Signaling previous search thread to stop")

            self.stop_event.clear()

            if query:
                self.search_thread_instance = threading.Thread(
                    target=self._run_search, 
                    daemon=True, 
                    args=(query, final)
                )
                self.search_thread_instance.start()
        
        except Exception as e:
            logger.exception("Search keyword error:")

    def _run_search(self, query: str, final: bool) -> None:
        """
        Run search in background thread.
        
        Performs the actual channel search operation in a separate thread to avoid
        blocking the UI. Handles progress updates, splash screen display, and
        thread cancellation.
        
        For quick searches (final=False), limits results to 6 channels without
        downloading additional data. For final searches (final=True), retrieves
        up to 20 channels with full details including profile pictures.
        
        Args:
            query: Search keyword or channel name
            final: If True, performs comprehensive search with progress tracking.
                  If False, performs quick limited search.
        """
        logger.debug("Search channel thread triggered")
        
        # Check if thread should stop before starting work
        if self.stop_event.is_set():
            logger.debug("Search thread cancelled before execution")
            return
        
        try:
            if final:
                # Show splash screen for final search
                self.show_splash_signal.emit()
                
                # Define progress callback for the search
                def progress_callback(progress: Any, status: Optional[str] = None) -> None:
                    """
                    Callback function for reporting search progress.
                    
                    Args:
                        progress: Progress value (int/float for percentage, str for status message)
                        status: Optional status message, defaults to None
                    """
                    if isinstance(progress, (int, float)):
                        self.progress_update.emit(int(progress), status or "")
                    elif isinstance(progress, str):
                        self.progress_update.emit(-1, progress)  # -1 means don't update progress bar
                
                # Perform search with progress tracking
                self.channels = self.search.search_channel(
                    query, 
                    limit=20, 
                    stop_event=self.stop_event,
                    final=final,
                    progress_callback=progress_callback
                )
            else:
                # Quick search without splash
                self.channels = self.search.search_channel(
                    query, 
                    limit=6, 
                    stop_event=self.stop_event,
                    final=final
                )
            
        except Exception as e:
            if self.stop_event.is_set():
                logger.debug("Search thread stopped during execution")
                return
            # Close splash on error
            self.close_splash_signal.emit()
            logger.exception("Search error occurred:")
            return

        # Check again before processing results
        if self.stop_event.is_set():
            logger.debug("Search thread cancelled after search")
            self.close_splash_signal.emit()
            return

        self.channel_name = [item.get('title') for key, item in self.channels.items()]

        if not final:
            self.results_ready.emit(self.channel_name)
        else:
            # Signal that search is complete
            self.search_complete.emit()

    def search_channel(self) -> None:
        """
        Handle search button click event.
        
        Initiates a final comprehensive search for the query entered in the search bar.
        Cancels any ongoing auto-search operations before starting the new search.
        Clears previous incomplete results to ensure fresh data is retrieved.
        """
        query = self.searchbar.text().strip()
        if not query:
            return

        # --- Cancel any ongoing auto-search ---
        if self.search_thread_instance and self.search_thread_instance.is_alive():
            self.stop_event.set()
            self.search_thread_instance.join(timeout=1.0)  # Ensure it fully stops before continuing

        # Clear old incomplete results
        self.channels = None
        self.search.search_channel(name=None)  # reset internal state if needed

        # --- Now run the final search with fresh data ---
        self.search_keyword(query=query, final=True)