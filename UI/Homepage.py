from PySide6 import QtCore
from PySide6.QtWidgets import (QApplication, QMainWindow, QStackedWidget, QWidget, 
                               QLineEdit, QListWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QListWidgetItem, QCompleter, QGridLayout)
from PySide6.QtCore import Qt, QStringListModel, QSize
from PySide6.QtGui import QPixmap, QIcon
import threading
import time
import traceback

from Backend.ScrapeChannel import Search
from Backend.ScrapeTranscription import Transcription
from utils.AppState import app_state

class Home(QWidget):
    results_ready = QtCore.Signal(list)
    videos = {}
    video_url = []
    live = {}
    shorts = {}
    content = {}

    def __init__(self, parent: QMainWindow = None):
        super(Home, self).__init__(parent)

        self.mainwindow = parent
        self.db = app_state.db
        self.search = Search()

        self.top_panel = QWidget()
        self.central_layout = QVBoxLayout()
        self.central_widget = QStackedWidget()
        
        # Replace ComboBox with LineEdit and ListWidget
        self.searchbar = QLineEdit()
        self.select_button = QPushButton("Select")
        self.channel_list = QListWidget()
        self.model = QStringListModel()
        self.completer = QCompleter(self.model, self.searchbar)
        self.select_button.clicked.connect(self.select_channel)
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
        self.scrape_transcription_button = QPushButton("screpe transcription")

        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(lambda: self.search_keyword(self.searchbar.text()))
        
        # Setup search components
        self.searchbar.setPlaceholderText("Search")
        self.searchbar.textChanged.connect(self.reset_search_timer)
        self.completer.activated.connect(self.on_completer_activated)
        
        self.search_channel_button.clicked.connect(self.search_channel)
        self.scrape_transcription_button.clicked.connect(self.scrape_transcription)
        self.results_ready.connect(self.update_results)

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
        self.top_layout.addWidget(self.select_button, 2, 0, 1, 2, alignment=Qt.AlignBottom)
        self.top_panel.show()

    def select_channel(self):
        item = self.channel_list.currentItem()
        if item:
            data = item.data(Qt.UserRole)
            app_state.channel_name = data['channel_name']
            app_state.channel_id = data['channel_id']
            print(f'{data["channel_url"]}')
            app_state.channel_url = data['channel_url']

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

    def search_thread(self, query, final=False):
        print("search channel thread triggered")
        
        # Check if thread should stop before starting work
        if self.stop_event.is_set():
            print("Search thread cancelled before execution")
            return
        
        if final:
            self.channels = self.search.search_channel(query, limit=20, stop_event=self.stop_event, final=final)
        else:
            self.channels = self.search.search_channel(query, limit=6, stop_event=self.stop_event, final=final)

        # Check again before processing results
        if self.stop_event.is_set():
            print("Search thread cancelled after search")
            return

        self.channel_name = [item.get('title') for key, item in self.channels.items()]

        if not final:
            self.results_ready.emit(self.channel_name)
            
    def update_results(self, channels):
        """Update dropdown list with search results"""        
        if channels:
            self.model.setStringList(channels)
            self.completer.complete()
    
    @QtCore.Slot()
    def update_channel_list(self):
        self.channel_list.clear()
        if not self.channels:
            return

        for channel_id, channel_info in self.channels.items():
            inf = self.db.fetch("CHANNEL", "channel_id=?", (channel_id,))
            if not inf:
                # No DB row found — use sensible defaults and warn
                print(f"[WARN] No DB entry for channel_id={channel_id}")
                sub_count = 0
                channel_name = channel_info.get("title", "Unknown")
                profile_pic = None
            else:
                row = inf[0]
                sub_count = row.get("sub_count") or 0
                channel_name = row.get("name") or channel_info.get("title", "Unknown")
                profile_pic = row.get("profile_pic")

            icon = QIcon(profile_pic) if profile_pic else QIcon()
            text_label = f'\n{channel_name}\n{sub_count}\n'
            item = QListWidgetItem(icon, text_label)
            item.setData(Qt.UserRole, {
                "channel_id": channel_id,
                "channel_name": channel_name,
                "channel_url": channel_info.get('url'),
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
                # Don't wait - just let daemon thread die
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
                self.channels = self.search.search_channel(query, limit=20, stop_event=self.stop_event)
            else:
                self.channels = self.search.search_channel(query, limit=6, stop_event=self.stop_event)
        except Exception as e:
            if self.stop_event.is_set():
                print("Search thread stopped during execution")
                return
            raise

        # Check again before processing results
        if self.stop_event.is_set():
            print("Search thread cancelled after search")
            return

        self.channel_name = [item.get('title') for key, item in self.channels.items()]

        if not final:
            self.results_ready.emit(self.channel_name)
        else:
            QtCore.QMetaObject.invokeMethod(
                self, 
                "update_channel_list", 
                Qt.QueuedConnection
            )

    def search_channel(self):
        query = self.searchbar.text()
        self.search_keyword(query=query, final=True)

    def scrape_transcription(self):
        """
        Scrape transcription for the first video in self.video_url
        and store it as JSON in Data/.
        """
        if not self.video_url:
            print("No video URL available. Please scrape videos first.")
            return

        try:
            video_url = self.video_url[:1]  # Take the first video for now
            print(f"Fetching transcript for: {video_url}")

            transcription = Transcription(self.db)  # Already uses DatabaseManager internally
            transcript_data = transcription.get_transcripts(video_url, self.channel_id, lang="en")

            if transcript_data:
                print(f"Transcript fetched and saved")
            else:
                print("Failed to fetch transcript.")

        except Exception as e:
            traceback.print_exc()
            print(f"Error while scraping transcription: {e}")

