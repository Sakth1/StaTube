from PySide6.QtWidgets import QApplication
import sys

from utils.Logger import logger
from UI.AppStartup import AppStartup

APP_NAME = "StaTube"
APP_VERSION = "0.4.1"
APP_PUBLISHER = "StaTube"
APP_DESCRIPTION = "A Python PySide6 GUI app for analyzing YouTube video transcripts and comments."

def main():
    logger.info("=== StaTube Boot Process 1: Application starting ===")

    try:
        app = QApplication(sys.argv)

        logger.debug("Launching AppStartup (Splash First)...")
        startup = AppStartup()

        logger.info("Entering Qt event loop...")
        sys.exit(app.exec())

    except KeyboardInterrupt:
        logger.warning("Interrupted by user, exiting...")
    except Exception:
        logger.exception("Unhandled exception in main()")
    finally:
        logger.info("StaTube application shutting down.")


if __name__ == "__main__":
    main()
