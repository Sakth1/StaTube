from PySide6.QtCore import QThread, Signal
import time
import threading
from .Proxy import Proxy
from .AppState import app_state


class ProxyThread(QThread):
    """
    Runs Proxy in background and shares it through app_state.
    - Waits until 3 proxies are ready (shows progress in splash)
    - Then emits proxy_ready signal to continue app
    - Keeps background updates running in a helper thread
    """
    proxy_ready = Signal()
    proxy_status = Signal(str)

    def __init__(self):
        super().__init__()
        self._running = True
        self.pool = None
        self._last_proxy = None
        self._reuse_count = 2  # initialized as used up
        self._bg_monitor_thread = None

    def run(self):
        def ui_status(msg: str):
            self.proxy_status.emit(msg)

        ui_status("Initializing proxy pool...")
        self.pool = Proxy(
            target_valid=30,
            refill_threshold=20,
            status_callback=ui_status
        )
        app_state.proxy = self.pool

        ui_status("Validating proxies...")
        start = time.time()
        # Wait until at least 3 valid proxies are found
        while self._running and self.pool.peek_count() < 3:
            ui_status(f"Valid proxies: {self.pool.peek_count()}/3")
            time.sleep(1)

        elapsed = round(time.time() - start, 1)
        ui_status(f"Proxy initialization complete ({self.pool.peek_count()} valid, {elapsed}s)")
        print(f"[INFO] Proxy ready with {self.pool.peek_count()} proxies.")

        # ✅ Notify MainWindow and continue app setup
        self.proxy_ready.emit()

        # ✅ Start a background monitor for ongoing proxy validation
        self._bg_monitor_thread = threading.Thread(target=self._background_monitor, daemon=True)
        self._bg_monitor_thread.start()

    def _background_monitor(self):
        """Runs separately to send proxy status updates every 3 seconds."""
        while self._running:
            count = self.pool.peek_count() if self.pool else 0
            self.proxy_status.emit(f"Active proxies: {count}")
            time.sleep(3)

    def get_proxy(self) -> str | None:
        """
        Returns same proxy twice before rotating to next one.
        """
        if not self.pool:
            return None
        if self._reuse_count < 2:
            self._reuse_count += 1
            return self._last_proxy
        proxy = self.pool.get_working_proxy()
        if proxy:
            self._last_proxy = proxy
            self._reuse_count = 1
        return proxy

    def stop(self):
        self._running = False
        if self.pool:
            self.pool.cleanup()
        self.quit()
        self.wait()
