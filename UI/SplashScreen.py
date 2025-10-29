from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QFrame, QWidget, QVBoxLayout, QHBoxLayout, QToolButton
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QSize, QThread, Signal
import sys, time

from utils.Proxy import Proxy


class ProxyThread():

    def __init__(self):
        super().__init__()
        self.proxy = Proxy()

    def start(self):
        """This runs in a background thread."""
        while True:
            print('waiting for proxy')
            if self.proxy.check_working_proxy():
                print('got proxy')
                return
            time.sleep(1)
