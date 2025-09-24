from UI.MainWindow import MainWindow
from PySide6.QtWidgets import QApplication
import sys
from PySide6.QtWidgets import QApplication, QMessageBox
from UI.MainWindow import MainWindow
from utils.CheckInternet import Internet

try:
    if not Internet().check_internet():
        app = QApplication()
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText("No internet connection detected.\nPlease check your network and restart the app.")
        msg.setWindowTitle("Connection Error")
        msg.exec()
        sys.exit(1)

    app = QApplication()
    window = MainWindow()
    window.show()
    app.exec()

except Exception as e:
    import traceback
    traceback.print_exc()
    print(e)