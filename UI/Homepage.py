from PySide6 import QtCore
from PySide6.QtWidgets import (QApplication, QMainWindow, QStackedWidget, QWidget, 
                               QLineEdit, QListWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QListWidgetItem, QCompleter, QGridLayout)
from PySide6.QtCore import Qt, QStringListModel, QSize, Signal
from PySide6.QtGui import QPixmap, QIcon, QPalette, QColor
import threading
import traceback

from Data.DatabaseManager import DatabaseManager
from Backend.ScrapeChannel import Search
from utils.AppState import app_state
from UI.SplashScreen import SplashScreen
import os

class Home(QWidget):
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

    def __init__(self, parent: QMainWindow = None):
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

    def on_completer_activated(self, text):
        """Handle completer selection"""
        self.completer_active = True
        self.search_timer.stop()  # Stop any pending search
        # Reset flag after a short delay
        QtCore.QTimer.singleShot(50, lambda: setattr(self, 'completer_active', False))
    
    def setupUi(self):
        """
        Set up the user interface of the main window.
        """
        self.setuptop()

    def setuptop(self):
        self.top_layout = QGridLayout()
        self.top_panel.setLayout(self.top_layout)
        self.top_layout.addWidget(self.searchbar, 0, 0, alignment=Qt.AlignTop)
        self.top_layout.addWidget(self.search_channel_button, 0, 1)
        self.top_layout.addWidget(self.select_scrape_button, 2, 0, 1, 2, alignment=Qt.AlignBottom)
        self.top_panel.show()

    def select_channel(self):
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

    def reset_search_timer(self):
        if not self.completer_active:
            self.search_timer.start(5)

    def on_item_selected(self, item):
        """Handle item selection from dropdown"""
        if item:
            self.searchbar.blockSignals(True)
            selected_text = item.text()
            self.searchbar.setText(selected_text)
            # Return focus to input after selection
            QtCore.QTimer.singleShot(10, lambda: self.searchbar.setFocus())
            self.searchbar.blockSignals(False)

    @QtCore.Slot()
    def show_search_splash(self):
        """Show splash screen for search operation"""
        cwd = os.getcwd()
        gif_path = os.path.join(cwd, "assets", "gif", "loading.gif")
        self.splash = SplashScreen(parent=self.mainwindow, gif_path=gif_path)
        self.splash.set_title("Searching Channels...")
        self.splash.update_status("Fetching channel information...")
        self.splash.show()

    @QtCore.Slot(int, str)
    def on_progress_update(self, progress, status):
        """Update splash screen progress"""
        if self.splash:
            if progress >= 0:  # Only update progress bar for numeric values
                self.splash.set_progress(progress)
            if status:
                self.splash.update_status(status)

    @QtCore.Slot()
    def close_splash(self):
        """Close splash screen"""
        if self.splash:
            self.splash.close()
            self.splash = None

    def update_results(self, channels):
        """Update dropdown list with search results"""        
        if channels:
            self.model.setStringList(channels)
            self.completer.complete()
    
    @QtCore.Slot()
    def on_search_complete(self):
        """Handle completion of final search with downloads"""
        print("Final search complete, updating UI...")
        self.update_channel_list()
        self.close_splash()

    @QtCore.Slot()
    def update_channel_list(self):
        self.channel_list.clear()
        if not self.channels:
            return

        # Create a copy of channels to avoid iteration issues
        channels_copy = self.channels.copy()
        
        for channel_id, info in channels_copy.items():
            inf = self.db.fetch(table="CHANNEL", where="channel_id=?", params=(channel_id,))
            if not inf:
                # No DB row found — use sensible defaults and warn
                print(f"[WARN] No DB entry for channel {channel_name}")
                sub_count = 0
                channel_name = info.get("title", "Unknown")
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

    def search_keyword(self, query, final=False):
        try:
            # Signal any existing thread to stop
            if self.search_thread_instance and self.search_thread_instance.is_alive():
                self.stop_event.set()
                print("Signaling previous search thread to stop")

            self.stop_event.clear()

            if query:
                self.search_thread_instance = threading.Thread(
                    target=self._run_search, 
                    daemon=True, 
                    args=(query, final)
                )
                self.search_thread_instance.start()
        
        except Exception as e:
            traceback.print_exc()
            print(e)

    def _run_search(self, query, final):
        """Run search in background thread"""
        print("search channel thread triggered")
        
        # Check if thread should stop before starting work
        if self.stop_event.is_set():
            print("Search thread cancelled before execution")
            return
        
        try:
            if final:
                # Show splash screen for final search
                self.show_splash_signal.emit()
                
                # Define progress callback for the search
                def progress_callback(progress, status=None):
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
                print("Search thread stopped during execution")
                return
            # Close splash on error
            self.close_splash_signal.emit()
            print(f"Search error: {e}")
            traceback.print_exc()
            return

        # Check again before processing results
        if self.stop_event.is_set():
            print("Search thread cancelled after search")
            self.close_splash_signal.emit()
            return

        self.channel_name = [item.get('title') for key, item in self.channels.items()]

        if not final:
            self.results_ready.emit(self.channel_name)
        else:
            # Signal that search is complete
            self.search_complete.emit()

    def search_channel(self):
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