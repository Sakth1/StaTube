from PySide6.QtCore import QThread, Signal
import time
from .Proxy import Proxy
from .AppState import app_state


class ProxyThread(QThread):
    """
    Runs Proxy in background and shares it through app_state.
    - Waits until 3 proxies are ready (shows progress in splash)
    - Then emits proxy_ready signal to continue app
    - Keeps background updates running
    """
    proxy_ready = Signal()
    proxy_status = Signal(str)

    def __init__(self):
        super().__init__()
        self._running = True
        self.pool = None
        self._last_proxy = None
        self._reuse_count = 2  # initialized as used up

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
        while self._running and self.pool.peek_count() < 3:
            ui_status(f"Valid proxies: {self.pool.peek_count()}/3")
            time.sleep(1)

        elapsed = round(time.time() - start, 1)
        ui_status(f"Proxy initialization complete ({self.pool.peek_count()} valid, {elapsed}s)")
        print(f"[INFO] Proxy ready with {self.pool.peek_count()} proxies.")
        self.proxy_ready.emit()

        # Keep updating splash/debug info
        while self._running:
            ui_status(f"Active proxies: {self.pool.peek_count()}")
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
