import requests
from swiftshadow.classes import ProxyInterface
import threading
from queue import Queue
import time
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
        
        # Start multiple background validation threads for parallel processing
        self.validator_threads = []
        for _ in range(3):  # Run 3 parallel validation workers
            thread = threading.Thread(target=self._validate_proxies_worker, daemon=True)
            thread.start()
            self.validator_threads.append(thread)
        
        # Register cleanup on exit
        atexit.register(self.cleanup)

    def validate_proxy(self, proxy_str: str) -> bool:
        """Check if proxy works by pinging YouTube."""
        try:
            response = requests.get(
                "https://www.youtube.com/",
                proxies={'http': proxy_str, 'https': proxy_str},
                timeout=3,  # Reduced from 5 to 3 seconds
                allow_redirects=False  # Faster validation
            )
            return response.status_code == 200
        except Exception as e:
            return False

    def _validate_proxies_worker(self):
        """Background worker that validates proxies continuously."""
        while not self.should_stop.is_set():
            # Stop if we have enough working proxies
            if self.working_proxies.qsize() >= self.max_working_proxies:
                break
            
            try:
                with ThreadPoolExecutor(max_workers=20) as executor:  # Increased from 10 to 20
                    futures = []
                    
                    # Submit 30 proxies for validation (increased from 10)
                    for _ in range(30):
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
                    
                    # Process results as they complete (don't wait for all)
                    for future in as_completed(futures):
                        if self.should_stop.is_set():
                            break
                        try:
                            future.result(timeout=0.5)  # Don't wait too long for results
                        except Exception:
                            pass  # Ignore individual validation failures
                        # Check if we've reached limit during validation
                        if self.working_proxies.qsize() >= self.max_working_proxies:
                            break
            except Exception as e:
                if not self.should_stop.is_set():
                    print(f"[ERROR] Validation worker error: {e}")
            
            # Removed delay between batches for faster processing

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
                print(self.working_proxies)
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
        
    def ensure_sufficient_proxies(self):
        while True:
            print(f'Checking proxy, {self.working_proxies.qsize()} proxies available')
            if self.working_proxies.qsize() > 1:
                return True
            time.sleep(1)
    
    def cleanup(self):
        """Cleanup method to gracefully stop the validation threads."""
        print("[INFO] Shutting down proxy validation...")
        self.should_stop.set()
        for thread in self.validator_threads:
            if thread.is_alive():
                thread.join(timeout=2)
