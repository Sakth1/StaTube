Implement the selection of channel from the listwidget, design and implement how to take things from there.

Change it so that the transcriptions is download for any language

fix this:
Exception in thread Thread-3 (search_thread):
Traceback (most recent call last):
  File "C:\Users\HP\AppData\Local\Programs\Python\Python312\Lib\threading.py", line 1075, in _bootstrap_inner
    self.run()
  File "C:\Users\HP\AppData\Local\Programs\Python\Python312\Lib\threading.py", line 1012, in run
    self._target(*self._args, **self._kwargs)
  File "d:\Personal\Personal_Projects\youtube_transcription_analysis\UI\MainWindow.py", line 118, in search_thread
    self.channels = search.search_channel(query)
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "d:\Personal\Personal_Projects\youtube_transcription_analysis\Backend\ScrapeChannel.py", line 50, in search_channel
    self.db.insert(
  File "d:\Personal\Personal_Projects\youtube_transcription_analysis\Data\DatabaseManager.py", line 100, in insert
    cursor.execute(query, values)
sqlite3.OperationalError: table CHANNEL has no column named channel_id

have a look at thi proxy system:
import asyncio
from proxybroker import Broker

async def show(proxies):
    while True:
        proxy = await proxies.get()
        if proxy is None: break
        print('Found proxy: %s' % proxy)

proxies = asyncio.Queue()
broker = Broker(proxies)
tasks = asyncio.gather(
    broker.find(types=['HTTP', 'HTTPS'], limit=10),
    show(proxies))

loop = asyncio.get_event_loop()
loop.run_until_complete(tasks)


from PySide6 import QtCore
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QFrame, QWidget, QVBoxLayout, QToolButton
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QSize

from .Homepage import Homepage

class MainWindow(QMainWindow):
    def __init__(self):
        self.stack = QStackedWidget()
        self.central_widget = QWidget()
        self.sidebar = QFrame()
        self.setupsidebar()
        self.setuptabs()

    def setupsidebar(self):
        self.sidebar_layout = QVBoxLayout(self.central_widget)
        side_layout = QVBoxLayout(self.sidebar)
        side_layout.setAlignment(Qt.AlignTop)
        side_layout.setContentsMargins(10, 20, 10, 20)
        side_layout.setSpacing(25)

        # Icon list (replace with your real icons)
        icons = [
            ("home", "Home"),
            ("calendar", "Reports"),
            ("user", "Patients"),
            ("mail", "Messages"),
            ("settings", "Settings")
        ]

        # Create buttons
        self.buttons = []
        for i, (text, tooltip) in enumerate(icons):
            btn = QToolButton()
            btn.setIcon(QIcon(text))
            btn.setIconSize(QSize(28, 28))
            btn.setToolTip(tooltip)
            btn.setCheckable(True)
            btn.setAutoExclusive(True)
            side_layout.addWidget(btn)
            self.buttons.append(btn)

        side_layout.addStretch()

        self.sidebar.setLayout(self.sidebar_layout)
        self.sidebar_layout.addWidget(self.stack)
        
    def setuptabs(self):
        self.homepage = Homepage(self)
        self.stack.addWidget(self.homepage)
        self.setCentralWidget(self.centralwidget)

if __name__ == "__main__":
    app = QApplication()
    window = MainWindow()
    window.show()
    app.exec()


from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QFrame, QWidget, QVBoxLayout, QHBoxLayout, QToolButton
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QSize, QThread, Signal
import sys, time

# Example Proxy class
class Proxy:
    def get_proxy(self):
        print("Fetching proxy...")
        time.sleep(3)
        print("Proxy ready!")

# Worker thread
class ProxyThread(QThread):
    proxy_ready = Signal(object)

    def __init__(self):
        super().__init__()
        self.proxy = Proxy()

    def run(self):
        """This runs in a background thread."""
        while True:
            self.proxy.get_proxy()
            self.proxy_ready.emit(self.proxy)
            self.sleep(600)