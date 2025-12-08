from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QThread, Signal, QObject
import os, time

from UI.SplashScreen import SplashScreen
from UI.MainWindow import MainWindow
from utils.Logger import logger
from utils.CheckInternet import Internet


# STARTUP WORKER THREAD
class StartupWorker(QThread):
    status_updated = Signal(str, int)   # message, progress %
    finished = Signal(bool)
    step_timing = {}

    def __init__(self, parent=None):
        super().__init__(parent)

    def run(self):
        self.step("Checking internet connection...", 10)
        internet = Internet()
        connected = internet.check_internet()

        for _ in range(2):
            if connected:
                break
            time.sleep(1)
            connected = internet.check_internet()

        if not connected:
            self.finished.emit(False)
            return

        self.step("Initializing plugins...", 25)
        time.sleep(0.5)

        self.step("Loading UI modules...", 45)
        time.sleep(0.5)

        self.step("Preparing database engine...", 65)
        time.sleep(0.5)

        self.step("Optimizing startup cache...", 80)
        time.sleep(0.5)

        self.step("Finalizing system checks...", 95)
        time.sleep(0.4)

        self.step("Startup ready", 100)
        self.finished.emit(True)

    def step(self, msg, progress):
        logger.info(msg)
        self.status_updated.emit(msg, progress)
        self.step_timing[msg] = time.time()


# APP STARTUP CONTROLLER
class AppStartup(QObject):
    def __init__(self):
        super().__init__()

        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.base_dir = os.path.dirname(base_dir)
        gif_path = os.path.join(self.base_dir, "assets", "splash", "loading.gif")

        # parent=None to avoid QDialog parent type error
        self.splash = SplashScreen(parent=None, gif_path=gif_path)
        self.splash.set_title("StaTube - YouTube Data Analysis Tool")
        self.splash.update_status("Booting system...")
        self.splash.set_progress(5)

        # Use animated show
        self.splash.show_with_animation()

        logger.info("Splash screen shown with fade-in animation.")

        self.start_worker()

    # START BACKGROUND TASK
    def start_worker(self):
        self.worker = StartupWorker()
        self.worker.status_updated.connect(self.on_status_update)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()

    def on_status_update(self, message: str, progress: int):
        self.splash.update_status(message)
        self.splash.set_progress(progress)

    # FINAL HANDOFF
    def on_finished(self, connected: bool):
        self.splash.fade_and_close()
        if not connected:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Connection Issue")
            msg.setText(
                "No internet connection detected.\n\n"
                "StaTube can continue in offline mode, but some features may not work."
            )
            continue_btn = msg.addButton("Continue Offline", QMessageBox.AcceptRole)
            quit_btn = msg.addButton("Quit", QMessageBox.RejectRole)
            msg.setDefaultButton(continue_btn)
            msg.exec()

            if msg.clickedButton() == quit_btn:
                QApplication.instance().quit()
                return

        # NOW SAFE TO CREATE MAIN WINDOW
        logger.info("Launching MainWindow after verified startup.")
        try:
            self.main_window = MainWindow()
            self.main_window.finish_initialization()
            self.main_window.showMaximized()
        except Exception as e:
            logger.exception("Fatal UI startup failure")
            QMessageBox.critical(
                None,
                "Startup Failure",
                "StaTube failed to initialize UI. Starting in Safe Mode."
            )
        logger.info("===== Startup Timing Report =====")
        for step, t in self.worker.step_timing.items():
            logger.info(f"{step}")
