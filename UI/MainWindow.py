from PySide6 import QtCore, QtGui
from PySide6.QtWidgets import (QApplication, QMainWindow, QStackedWidget, QWidget, 
                               QLineEdit, QComboBox, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton)
import threading
import time
import traceback

from Backend.scrapeall import Search



class MainWindow(QMainWindow):
    results_ready = QtCore.Signal(list)
    def __init__(self):
        super(MainWindow, self).__init__()

        self.top_panel = QWidget()
        self.bottom_panel = QWidget()
        self.central_layout = QVBoxLayout()
        self.central_widget = QStackedWidget()
        self.searchbar = QComboBox()
        self.search_timer = QtCore.QTimer()
        self.stop_event = threading.Event()
        self.search_thread_instance = None

        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.search_keyword)

        self.central_widget.addWidget(self.top_panel)
        self.central_widget.addWidget(self.bottom_panel)
        
        self.searchbar.setEditable(True)
        self.searchbar.setPlaceholderText("Search")
        self.searchbar.currentTextChanged.connect(self.reset_search_timer)
        self.results_ready.connect(self.update_results)

        self.setupUi()

        self.setCentralWidget(self.central_widget)
    
    def setupUi(self):
        """
        Set up the user interface of the main window.
        """
        self.setGeometry(500, 200, 500, 300)
        self.setuptop()
        self.setupbottom()

    def setuptop(self):
        self.top_layout = QVBoxLayout()
        self.top_layout.addWidget(self.searchbar)
        self.top_panel.setLayout(self.top_layout)
        self.top_panel.show()
    
    def setupbottom(self):
        self.bottom_layout = QVBoxLayout()
        self.bottom_panel.setLayout(self.bottom_layout)
        self.bottom_panel.show()

    def reset_search_timer(self):
        self.search_timer.start(400)

    def search_thread(self, query):
        search = Search()
        channels = search.search_channel(query)
        self.results_ready.emit(channels) 

    def update_results(self, channels):
        self.searchbar.clear()
        self.searchbar.addItems(channels)
        self.searchbar.showPopup()

    def search_keyword(self):
        try:
            if self.search_thread_instance and self.search_thread_instance.is_alive():
                self.stop_event.set()
                self.search_thread_instance.join(timeout=0.1)

            self.stop_event.clear()

            query = self.searchbar.currentText()
            self.search_thread_instance = threading.Thread(target=self.search_thread, daemon=True, args=(query,))
            self.search_thread_instance.start()
        
        except Exception as e:
            traceback.print_exc()
            print(e)