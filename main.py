from PySide6.QtWidgets import QApplication
import sys

from UI.MainWindow import MainWindow

APP_NAME = "StaTube"
APP_VERSION = "0.3.0"
APP_PUBLISHER = "StaTube"
APP_DESCRIPTION = "A Python PySide6 GUI app for analyzing YouTube video transcripts and comments."

def main():

    try:
        app = QApplication()
        window = MainWindow()
        window.showMaximized()
        app.exec()
    except KeyboardInterrupt:
        print("Interrupted by user, exiting...")
    finally:
        sys.exit(0)

if __name__ == "__main__":
    main()
