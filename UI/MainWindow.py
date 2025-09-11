from PySide6 import QtCore, QtGui, QtWidgets


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.setupUi()
    
    def setupUi(self):
        """
        Set up the user interface of the main window.

        This function is called once in the constructor of MainWindow and
        should not be called again. It sets the size of the window to 800x600
        and should be overridden in subclasses if a different size is desired.
        """

        self.setGeometry(500, 200, 500, 300)