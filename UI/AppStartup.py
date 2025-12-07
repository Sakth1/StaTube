from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QThread, Signal
import os
import time

from UI.SplashScreen import SplashScreen
from utils.Logger import logger
from utils.CheckInternet import Internet

class StartupWorker(QThread):
    """
    Background worker for startup tasks such as internet checks.
    Keeps UI responsive while doing blocking work.
    """
    status_updated = Signal(str)
    finished = Signal(bool)  # True = internet OK, False = still offline after retries

    def __init__(self, parent=None, max_retries: int = 3, retry_delay: float = 2.0):
        super().__init__(parent)
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def run(self) -> None:
        internet = Internet()
        connected = False

        for attempt in range(self.max_retries):
            # R2: general “soft” messages, not attempt counts
            if attempt == 0:
                self.status_updated.emit("Checking internet connection...")
            elif attempt == 1:
                self.status_updated.emit("Still checking your connection...")
            else:
                self.status_updated.emit("Almost there, verifying network...")

            logger.debug(f"StartupWorker: Checking internet (attempt {attempt + 1}/{self.max_retries})")
            connected = internet.check_internet()
            logger.debug(f"StartupWorker: Internet check result: {connected}")

            if connected:
                logger.info(f"StartupWorker finished. Internet connected: {connected}")
                break

            # Small delay before retrying (background thread, so safe)
            time.sleep(self.retry_delay)

        self.finished.emit(bool(connected))


class AppStartup:    
    def __init__(self):
        # Splash screen
        gif_path = os.path.join(self.base_dir, "assets", "splash", "loading.gif")
        self.splash = SplashScreen(parent=self, gif_path=gif_path)
        # self.splash = SplashScreen(parent=self)
        self.splash.set_title("StaTube - YouTube Data Analysis Tool")
        self.splash.update_status("Starting application...")
        logger.info("Displaying splash screen and starting asynchronous startup sequence.")
        self.splash.show()

        # Start asynchronous startup flow
        self.start_startup_sequence()

    # ---------- Startup Sequence ----------

    def start_startup_sequence(self):
        """
        Kick off background startup tasks (internet checks, etc.)
        while showing the splash screen.
        """
        logger.debug("StartupWorker thread created. Beginning internet check process...")
        self.startup_worker = StartupWorker(self, max_retries=3, retry_delay=2.0)
        self.startup_worker.status_updated.connect(self.splash.update_status)
        self.startup_worker.finished.connect(self.on_startup_finished)
        self.startup_worker.start()

    def on_startup_finished(self, connected: bool):
        """
        Called when the startup worker finishes internet checks.
        """
        logger.info(f"Startup network check completed. Connected = {connected}")
        if not connected:
            # Show dialog: Continue Offline / Quit
            self.splash.close()
            logger.warning("No internet detected. User will be prompted for offline mode or exit.")
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Connection Issue")
            msg.setText(
                "No internet connection detected.\n\n"
                "StaTube can continue in offline mode, but some features may not work.\n"
                "What would you like to do?"
            )
            continue_btn = msg.addButton("Continue Offline", QMessageBox.AcceptRole)
            quit_btn = msg.addButton("Quit", QMessageBox.RejectRole)
            msg.setDefaultButton(continue_btn)

            msg.exec()

            if msg.clickedButton() == quit_btn:
                # User chose to quit; close the app
                QApplication.instance().quit()
                return

            # If user chose to continue offline, just carry on to setup
            self.splash.update_status("Continuing in offline mode...")

        else:
            logger.info("Internet connection verified. Proceeding with initialization.")
            self.splash.update_status("Internet connection established. Preparing application...")

        # Now perform remaining init (DB, stylesheet, pages)
        self.finish_initialization()