from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QFrame, QWidget, QVBoxLayout, QHBoxLayout, QToolButton
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QSize, QThread, Signal
import sys, time

from utils.Proxy import Proxy


class ProxyThread(QThread):

    def __init__(self):
        super().__init__()
        self.proxy = Proxy()

    def run(self):
        """This runs in a background thread."""
        pass