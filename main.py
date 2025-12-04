from PySide6.QtWidgets import QApplication
import sys

from utils.Logger import logger
from UI.MainWindow import MainWindow

APP_NAME = "StaTube"
APP_VERSION = "0.4.0"
APP_PUBLISHER = "StaTube"
APP_DESCRIPTION = "A Python PySide6 GUI app for analyzing YouTube video transcripts and comments."

def main():
    try:
        app = QApplication()
        window = MainWindow()
        window.showMaximized()
        app.exec()
    except KeyboardInterrupt:
        logger.warning("Interrupted by user, exiting...")
    except Exception as e:
        logger.exception("Unhandled exception in main:")
    finally:
        sys.exit(0)

if __name__ == "__main__":
    main()
