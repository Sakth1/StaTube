from PySide6.QtCore import QThread, Signal, QCoreApplication, QTimer
import time
from .Proxy import Proxy
from .AppState import app_state


class ProxyThread(QThread):
    """
    Runs Proxy in background and shares it through app_state.
    - Waits until 3 proxies are ready (shows progress in splash)
    - Emits proxy_ready once
    - Keeps background updates running
    """
    proxy_ready = Signal()
    proxy_status = Signal(str)

    def __init__(self):
        super().__init__()
        self._running = True
        self.pool = None
        self._last_proxy = None
        self._reuse_count = 2  # ensures rotation after two uses
        self._ready_emitted = False  # emit once only

    def run(self):
        def ui_status(msg: str):
            print(f"[UI-STATUS] {msg}")
            self.proxy_status.emit(msg)

        ui_status("Initializing proxy pool...")
        print("[DEBUG] Creating Proxy instance...")
        self.pool = Proxy(
            target_valid=30,
            refill_threshold=20,
            status_callback=ui_status
        )
        app_state.proxy = self.pool
        print("[DEBUG] Proxy instance created and stored in app_state")

        ui_status("Validating proxies...")
        start_time = time.time()

        while self._running:
            count = self.pool.peek_count()
            # ADD DEBUGGING:
            #print(f"[DEBUG] peek_count() returned: {count}")
            #print(f"[DEBUG] Pool type: {type(self.pool)}")
            #print(f"[DEBUG] Pool attributes: {[attr for attr in dir(self.pool) if not attr.startswith('_')]}")
            
            #ui_status(f"Valid proxies: {count}/3")
            
            if count >= 3:
                print(f"[DEBUG] Threshold reached — emitting proxy_ready signal")
                ui_status(f"Proxy initialization complete ({count} valid)")
                self.proxy_ready.emit()
                self._ready_emitted = True
                elapsed = round(time.time() - start_time, 1)
                print(f"[INFO] Proxy ready emitted after {elapsed}s, total {count}")
                break

            time.sleep(5)

        # Continue running in background to maintain proxy pool, but with less frequent updates
        while self._running:
            count = self.pool.peek_count()
            # Only update status occasionally to avoid spam
            if int(time.time()) % 10 == 0:  # Update every 10 seconds
                ui_status(f"Background: {count} valid proxies")
            time.sleep(3)

        print("[DEBUG] ProxyThread exiting run() loop")

    def get_proxy(self) -> str | None:
        """Returns same proxy twice before rotating."""
        if not self.pool:
            print("[WARN] Proxy pool not initialized yet")
            return None
        if self._reuse_count < 2:
            self._reuse_count += 1
            print(f"[DEBUG] Reusing proxy ({self._reuse_count}/2): {self._last_proxy}")
            return self._last_proxy
        proxy = self.pool.get_working_proxy()
        if proxy:
            print(f"[DEBUG] New proxy fetched: {proxy}")
            self._last_proxy = proxy
            self._reuse_count = 1
        return proxy

    def stop(self):
        print("[DEBUG] Stopping ProxyThread...")
        self._running = False
        if self.pool:
            self.pool.cleanup()
        self.quit()
        self.wait()
        print("[DEBUG] ProxyThread stopped and cleaned up")