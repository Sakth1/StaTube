from UI.MainWindow import MainWindow
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QTimer
import sys
import signal
from utils.CheckInternet import Internet

APP_NAME = "StaTube"
APP_VERSION = "0.3.0"
APP_PUBLISHER = "Sakthi Murugan C"
APP_DESCRIPTION = "A Python PySide6 GUI app for analyzing YouTube video transcripts and comments."

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
    window.showMaximized()

    try:
        app.exec()
    except KeyboardInterrupt:
        print("Interrupted by user, exiting...")
    finally:
        sys.exit(0)

if __name__ == "__main__":
    main()
