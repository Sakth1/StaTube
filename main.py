from UI.MainWindow import MainWindow
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QTimer
import sys
import signal
from utils.CheckInternet import Internet

def main():
    internet = Internet()

    if not internet.check_internet():
        app = QApplication()
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText("No internet connection detected.\nPlease check your network and restart the app.")
        msg.setWindowTitle("Connection Error")
        msg.exec()
        sys.exit(1)

    app = QApplication()
    window = MainWindow()
    #window.showMaximized()
    window.show()

    try:
        app.exec()
    except KeyboardInterrupt:
        print("Interrupted by user, exiting...")
    finally:
        sys.exit(0)

if __name__ == "__main__":
    main()
