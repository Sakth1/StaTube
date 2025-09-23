import requests
import concurrent.futures
import threading
import random
import time
from Data.CacheManager import CacheManager

class ProxyPool():
    def __init__(self, url="https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt", limit=100):
        self.url = url
        self.limit = limit
        self.valid_proxies = []
        self.lock = threading.Lock()
        self.cache = CacheManager()
        self.cache_key = "valid_proxies"

        # load existing proxies from cache
        cached = self.cache.load(self.cache_key)
        if isinstance(cached, list):
            self.valid_proxies = cached

        self.request_counter = 0

        # start background thread
        self.stop_event = threading.Event()
        self.worker_thread = threading.Thread(target=self.background_worker, daemon=True)
        self.worker_thread.start()

    def fetch_proxies(self):
        """Fetch raw proxies from remote list"""
        response = requests.get(self.url, timeout=10)
        response.raise_for_status()
        return response.text.strip().split('\n')

    def check_proxy(self, proxy):
        """Validate proxy by making a test request"""
        test_url = "http://httpbin.org/ip"
        try:
            response = requests.get(
                test_url,
                proxies={"http": f"http://{proxy}", "https": f"http://{proxy}"},
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False

    def background_worker(self):
        """Continuously validate and add proxies until limit reached"""
        while not self.stop_event.is_set():
            try:
                proxies = self.fetch_proxies()
                with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
                    for proxy, valid in zip(proxies, executor.map(self.check_proxy, proxies)):
                        if valid:
                            with self.lock:
                                if proxy not in self.valid_proxies and len(self.valid_proxies) < self.limit:
                                    self.valid_proxies.append(proxy)
                                    print(f"[ProxyPool] Valid proxy added: {proxy} (total {len(self.valid_proxies)})")
                                    self.cache.save(self.cache_key, self.valid_proxies)

                # stop if limit reached
                if len(self.valid_proxies) >= self.limit:
                    print("[ProxyPool] Reached limit, sleeping for 10 minutes before re-checking...")
                    time.sleep(600)  # revalidate every 10 minutes
                else:
                    time.sleep(30)  # fetch new proxies every 30s until we fill the pool
            except Exception as e:
                print(f"[ProxyPool] Error in worker: {e}")
                time.sleep(60)

    def get_proxy(self):
        """Return a proxy, rotating every 10 requests"""
        with self.lock:
            if not self.valid_proxies:
                raise RuntimeError("No valid proxies available yet")
            self.request_counter += 1
            if self.request_counter % 10 == 0:
                return random.choice(self.valid_proxies)
            return self.valid_proxies[self.request_counter % len(self.valid_proxies)]
        
    def get_requests_proxy(self):
        """Return a proxy dict usable by requests"""
        proxy = self.get_proxy()
        return {"http": f"http://{proxy}", "https": f"http://{proxy}"}

    def stop(self):
        """Stop the background thread"""
        self.stop_event.set()
        self.worker_thread.join()


# Example usage
if __name__ == "__main__":
    pool = ProxyPool(limit=100)

    # Wait until at least 5 proxies available
    while len(pool.valid_proxies) < 5:
        print("Waiting for at least 5 proxies...")
        time.sleep(5)

    print("First 5 proxies ready, starting work...")

    for i in range(25):
        proxy = pool.get_proxy()
        print(f"Request {i+1}: using proxy {proxy}")
        time.sleep(1)

    pool.stop()
