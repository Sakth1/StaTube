import requests
from swiftshadow.classes import ProxyInterface
import threading
from queue import Queue
from concurrent.futures import ThreadPoolExecutor, as_completed
import atexit

class Proxy:
    def __init__(self, protocol = "http", auto_rotate: bool = True, max_working_proxies: int = 50):
        self.proxy_manager = ProxyInterface(
            countries=["US"],
            protocol=protocol,
            autoRotate=auto_rotate
        )
        self.working_proxies = Queue()
        self.validation_lock = threading.Lock()
        self.max_working_proxies = max_working_proxies
        self.should_stop = threading.Event()
        
        # Start background validation thread
        self.validator_thread = threading.Thread(target=self._validate_proxies_worker, daemon=True)
        self.validator_thread.start()
        
        # Register cleanup on exit
        atexit.register(self.cleanup)

    def validate_proxy(self, proxy_str: str) -> bool:
        """Check if proxy works by pinging YouTube."""
        try:
            response = requests.get(
                "https://www.youtube.com/",
                proxies={'http': proxy_str, 'https': proxy_str},
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            return False

    def _validate_proxies_worker(self):
        """Background worker that validates proxies continuously."""
        while not self.should_stop.is_set():
            # Stop if we have enough working proxies
            if self.working_proxies.qsize() >= self.max_working_proxies:
                print(f"[INFO] Reached {self.max_working_proxies} working proxies. Stopping validation.")
                break
            
            try:
                with ThreadPoolExecutor(max_workers=10) as executor:
                    futures = []
                    
                    # Submit 10 proxies for validation
                    for _ in range(10):
                        if self.should_stop.is_set():
                            break
                            
                        if len(self.proxy_manager.proxies) == 0:
                            break
                        
                        # Check again before submitting new tasks
                        if self.working_proxies.qsize() >= self.max_working_proxies:
                            break
                        
                        self.proxy_manager.rotate()
                        proxy_obj = self.proxy_manager.get()
                        if proxy_obj:
                            proxy_str = proxy_obj.as_string()
                            futures.append(executor.submit(self._validate_and_store, proxy_str))
                    
                    # Wait for all validations to complete
                    for future in as_completed(futures):
                        if self.should_stop.is_set():
                            break
                        future.result()
                        # Check if we've reached limit during validation
                        if self.working_proxies.qsize() >= self.max_working_proxies:
                            break
            except Exception as e:
                if not self.should_stop.is_set():
                    print(f"[ERROR] Validation worker error: {e}")
            
            # Small delay before next batch
            if not self.should_stop.is_set():
                self.should_stop.wait(1)

    def _validate_and_store(self, proxy_str: str):
        """Validate a single proxy and store if working."""
        if self.should_stop.is_set():
            return False
            
        if self.validate_proxy(proxy_str):
            self.working_proxies.put(proxy_str)
            return True
        return False

    def get_working_proxy(self) -> str | None:
        """Get next working proxy from the queue."""
        try:
            if not self.working_proxies.empty():
                return self.working_proxies.get(timeout=1)
            else:
                print("[WARN] No working proxies available in queue.")
                return None
        except Exception as e:
            print(f"[ERROR] Failed to get working proxy: {e}")
            return None
        
    def get_proxy(self) -> str | None:
        """
        Returns a proxy string like "http://ip:port" if available.
        Returns None if no valid proxy could be fetched.
        """
        try:
            proxy_obj = self.proxy_manager.get()
            if proxy_obj:
                return proxy_obj.as_string()
            return None
        except Exception as e:
            print(f"[WARN] Could not fetch proxy: {e}")
            return None
        
    def check_working_proxy(self):
        if self.working_proxies.qsize() > 3:
            return True
        return False
    
    def cleanup(self):
        """Cleanup method to gracefully stop the validation thread."""
        print("[INFO] Shutting down proxy validation...")
        self.should_stop.set()
        if self.validator_thread.is_alive():
            self.validator_thread.join(timeout=2)


# Example usage
if __name__ == "__main__":
    proxy = Proxy(protocol="http")
    proxy_str = proxy.get_proxy()
    if proxy_str:
        print(f"[INFO] Using proxy: {proxy_str}")
    else:
        print("[WARN] No proxy available.")