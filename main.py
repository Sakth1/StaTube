from UI.MainWindow import MainWindow
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QTimer
import sys
import signal
from utils.CheckInternet import Internet

def handle_interrupt(*args):
    """Handle Ctrl+C cleanly."""
    print("\nCtrl+C detected — closing application...")
    QApplication.quit()

def main():
    # Ensure Ctrl+C works cross-platform
    signal.signal(signal.SIGINT, handle_interrupt)

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

    # Timer allows event loop to check for SIGINT periodically
    timer = QTimer()
    timer.start(100)
    timer.timeout.connect(lambda: None)

    try:
        app.exec()
    except KeyboardInterrupt:
        print("Interrupted by user, exiting...")
    finally:
        sys.exit(0)

if __name__ == "__main__":
    main()
