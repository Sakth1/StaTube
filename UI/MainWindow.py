from PySide6 import QtCore
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget

from .Homepage import Homepage

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.stack = QStackedWidget()
        self.setuptabs()

    def setuptabs(self):
        self.homepage = Homepage(self)
        self.stack.addWidget(self.homepage)
        self.setCentralWidget(self.stack)


if __name__ == "__main__":
    app = QApplication()
    window = MainWindow()
    window.show()
    app.exec()