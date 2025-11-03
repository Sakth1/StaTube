"""
Fast in-memory Proxy Pool with dual validation (YouTube + thumbnail)
and aggressive parallelization.

Behavior:
 - Fetches mixed proxies from GitHub (socks4/socks5/http).
 - Validates them concurrently (200+ threads if needed).
 - Keeps 30 valid proxies in queue; refills when below 20.
 - Dual validation: YouTube + YouTube thumbnail.
 - Prints debug status every 3 seconds.

Requirements:
    pip install requests[socks]
"""

import requests
import threading
from queue import Queue, Empty
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import random
from typing import List, Set, Tuple
import atexit

PROXY_SOURCES: List[Tuple[str, str]] = [
    ("https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks4.txt", "socks4"),
    ("https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks5.txt", "socks5"),
    #("https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt", "http"),
]

DEFAULT_TARGET_VALID = 30
DEFAULT_REFILL_THRESHOLD = 20


class Proxy:
    def __init__(
        self,
        target_valid: int = DEFAULT_TARGET_VALID,
        refill_threshold: int = DEFAULT_REFILL_THRESHOLD,
        initial_workers: int = 200,
        validator_workers: int = 200,
        validation_timeout: float = 3.0,
    ):
        self.target_valid = target_valid
        self.refill_threshold = refill_threshold
        self.initial_workers = initial_workers
        self.validator_workers = validator_workers
        self.validation_timeout = validation_timeout

        self.working_proxies: Queue = Queue()
        self._seen: Set[str] = set()
        self._seen_lock = threading.Lock()

        self._candidates: List[Tuple[str, str]] = []
        self._candidates_lock = threading.Lock()

        self.should_stop = threading.Event()
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)

        # Fetch proxies and fill initially
        self._download_and_mix_proxies()
        self._initial_fill()

        self._monitor_thread.start()
        atexit.register(self.cleanup)

    # -------------------------------------------------------------------------
    # PROXY FETCHING
    # -------------------------------------------------------------------------
    def _download_and_mix_proxies(self):
        candidates: List[Tuple[str, str]] = []
        for url, scheme in PROXY_SOURCES:
            try:
                print(f"[INFO] Fetching proxies from {url}")
                r = requests.get(url, timeout=10)
                if r.status_code == 200:
                    lines = [line.strip() for line in r.text.splitlines() if line.strip()]
                    for ln in lines:
                        if ":" in ln:
                            candidates.append((scheme, ln))
                    print(f"[INFO] Loaded {len(lines)} {scheme.upper()} proxies.")
            except Exception as e:
                print(f"[WARN] Failed to fetch {url}: {e}")
        random.shuffle(candidates)
        with self._candidates_lock:
            self._candidates = candidates
        print(f"[INFO] Total proxies mixed: {len(candidates)}")

    def _build_proxy_url(self, scheme: str, ipport: str) -> str:
        if scheme.lower().startswith("socks5"):
            return f"socks5h://{ipport}"
        elif scheme.lower().startswith("socks4"):
            return f"socks4://{ipport}"
        else:
            return f"http://{ipport}"

    # -------------------------------------------------------------------------
    # VALIDATION
    # -------------------------------------------------------------------------
    def validate_proxy(self, proxy_url: str) -> bool:
        """
        Dual validation:
         - YouTube homepage
         - YouTube thumbnail
        """
        proxies = {"http": proxy_url, "https": proxy_url}
        urls = [
            "https://www.youtube.com/",
            "https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg",
        ]
        for url in urls:
            try:
                resp = requests.get(url, proxies=proxies, timeout=self.validation_timeout, allow_redirects=False)
                if resp.status_code != 200:
                    return False
            except Exception:
                return False
        return True

    def _validate_batch(self, batch: List[Tuple[str, str]], max_add: int = 0):
        added = 0
        start = time.time()
        futures = {}

        with ThreadPoolExecutor(max_workers=self.validator_workers) as executor:
            for scheme, ipport in batch:
                if self.should_stop.is_set():
                    break
                proxy_url = self._build_proxy_url(scheme, ipport)
                fut = executor.submit(self.validate_proxy, proxy_url)
                futures[fut] = proxy_url  # map future → proxy_url

            for fut in as_completed(futures):
                if self.should_stop.is_set():
                    break
                proxy_url = futures[fut]
                try:
                    ok = fut.result(timeout=self.validation_timeout + 1)
                except Exception:
                    ok = False

                if ok:
                    with self._seen_lock:
                        if proxy_url in self._seen:
                            continue
                        self._seen.add(proxy_url)
                    try:
                        self.working_proxies.put_nowait(proxy_url)
                        added += 1
                        print(f"[VALID] {proxy_url}")
                    except Exception:
                        pass
                    if max_add and added >= max_add:
                        break

        elapsed = round(time.time() - start, 2)
        print(f"[DEBUG] Batch validation done: added={added}, total={self.working_proxies.qsize()}, took={elapsed}s")
        return added

    # -------------------------------------------------------------------------
    # INITIALIZATION & MONITOR
    # -------------------------------------------------------------------------
    def _initial_fill(self):
        print("[INFO] Performing initial validation...")
        while not self.should_stop.is_set() and self.working_proxies.qsize() < self.target_valid:
            with self._candidates_lock:
                if not self._candidates:
                    self._download_and_mix_proxies()
                batch = self._candidates[: self.initial_workers]
                self._candidates = self._candidates[self.initial_workers :]
            self._validate_batch(batch, max_add=self.target_valid - self.working_proxies.qsize())

    def _monitor_loop(self):
        last_debug = time.time()
        while not self.should_stop.is_set():
            size = self.working_proxies.qsize()
            if size < self.refill_threshold:
                with self._candidates_lock:
                    if len(self._candidates) < self.initial_workers:
                        self._download_and_mix_proxies()
                    batch = self._candidates[: self.initial_workers]
                    self._candidates = self._candidates[self.initial_workers :]
                needed = self.target_valid - size
                if needed > 0 and batch:
                    self._validate_batch(batch, max_add=needed)
            if time.time() - last_debug >= 3:
                print(f"[DEBUG] Working proxies: {self.working_proxies.qsize()}")
                last_debug = time.time()
            time.sleep(1)

    # -------------------------------------------------------------------------
    # PUBLIC INTERFACE
    # -------------------------------------------------------------------------
    def get_working_proxy(self, block: bool = False, timeout: float = 1.0) -> str | None:
        try:
            return self.working_proxies.get(block=block, timeout=timeout) if block else self.working_proxies.get_nowait()
        except Empty:
            return None

    def peek_count(self) -> int:
        return self.working_proxies.qsize()

    def ensure_sufficient_proxies(self, min_count: int = 1, poll_interval: float = 1.0) -> bool:
        while not self.should_stop.is_set():
            if self.working_proxies.qsize() >= min_count:
                return True
            time.sleep(poll_interval)
        return False

    def cleanup(self):
        print("[INFO] Cleaning up ProxyPool...")
        self.should_stop.set()
        if self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=2.0)


# -------------------------------------------------------------------------
# Standalone test
# -------------------------------------------------------------------------
if __name__ == "__main__":
    print("[START] Initializing ProxyPool (fast mode)...")
    pool = Proxy()
    try:
        pool.ensure_sufficient_proxies(30)
        print(f"[INFO] Validation complete. Total valid proxies: {pool.peek_count()}")
        while pool.peek_count() > 0:
            proxy = pool.get_working_proxy()
            if proxy:
                print(f"[VALID-PROXY] {proxy}")
    finally:
        pool.cleanup()
