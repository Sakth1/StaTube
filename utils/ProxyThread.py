from PySide6.QtCore import QThread, Signal
import time
from .Proxy import Proxy

class ProxyThread(QThread):
    """
    Runs in the background to keep proxy updated 
    with a fresh working proxy every 100 seconds.
    """
    proxy_updated = Signal(str)
    proxy_ready = Signal()
    proxy_status = Signal(str)

    def __init__(self):
        super().__init__()
        self.proxy = Proxy()
        self.running = True
        self.proxy_updated.connect(self._on_proxy_updated)

    def run(self):
        """
        Background loop that updates proxy every 100 seconds.
        """
        # Initial proxy fetch with status updates
        self.proxy_status.emit("Initializing proxy system...")
        QThread.msleep(500)  # Small delay for UI to update
        
        self.proxy_status.emit("Validating proxies...")
        if self.proxy.ensure_sufficient_proxies():
            self.proxy_status.emit("Fetching working proxy...")
            new_proxy = self.proxy.get_working_proxy()
            if new_proxy:
                self.proxy_status.emit("Proxy ready! Starting application...")
                QThread.msleep(500)  # Small delay before emitting ready signal
                self.proxy_ready.emit()  # Signal that initial proxy is ready
                print(f"[INFO] Initial proxy ready: {new_proxy}")
            else:
                self.proxy_status.emit("Failed to get proxy. Retrying...")
                # Retry logic
                retry_count = 0
                while retry_count < 3 and not new_proxy:
                    retry_count += 1
                    self.proxy_status.emit(f"Retry {retry_count}/3...")
                    time.sleep(2)
                    if self.proxy.ensure_sufficient_proxies():
                        new_proxy = self.proxy.get_working_proxy()
                        if new_proxy:
                            self.proxy_status.emit("Proxy ready! Starting application...")
                            QThread.msleep(500)
                            self.proxy_ready.emit()
                            print(f"[INFO] Initial proxy ready: {new_proxy}")
                            break
        else:
            self.proxy_status.emit("Waiting for working proxies...")
        
        # Continue with regular update loop
        while self.running:
            if self.proxy.ensure_sufficient_proxies():
                new_proxy = self.proxy.get_working_proxy()
                if new_proxy:
                    #self.proxy_updated.emit(new_proxy)
                    # TODO: Emit proxy_updated signal
                    print(f"[INFO] Proxy updated: {new_proxy}")
                else:
                    print("[WARN] No working proxy found to update.")
            else:
                print("[WARN] Waiting for working proxies...")
                time.sleep(1)

            # Wait 100 seconds before fetching the next proxy
            for _ in range(100):
                if not self.running:
                    break
                time.sleep(1)

    def _on_proxy_updated(self, proxy_str):
        """Callback after proxy update."""
        print(f"[SIGNAL] proxy updated to: {proxy_str}")

    def stop(self):
        """Gracefully stop the thread and clean up."""
        print("[INFO] Stopping ProxyThread...")
        self.running = False
        self.proxy.cleanup()
        self.quit()
        self.wait()