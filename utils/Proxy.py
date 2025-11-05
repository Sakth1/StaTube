"""
Proxy.py
---------
In-memory proxy pool with background validation.

✅ Fetches SOCKS4 + SOCKS5 proxies from GitHub.
✅ Validates in parallel using requests (YouTube + thumbnail check).
✅ Maintains queue of valid proxies (target=30, refill_threshold=20).
✅ Prints debug info every 3 sec.
✅ Thread-safe and auto-cleanup on exit.
"""

import requests
import threading
from queue import Queue, Empty
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import json
import random
from typing import List, Tuple, Set
import atexit

PROXY_SOURCES: List[Tuple[str, str, str]] = [
    #("https://proxylist.geonode.com/api/proxy-list?anonymityLevel=elite&protocols=socks5&speed=fast&limit=500&page=1&sort_by=lastChecked&sort_type=desc", "socks5", "Free-proxy-list"),
    #("https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks5.txt", "socks5", "default"),
    #("https://raw.githubusercontent.com/officialputuid/KangProxy/KangProxy/socks5/socks5.txt", "socks5", "default"),
    #("https://raw.githubusercontent.com/officialputuid/KangProxy/KangProxy/socks4/socks4.txt", "socks4", "default"),
    ("https://raw.githubusercontent.com/officialputuid/KangProxy/KangProxy/https/https.txt", "https", "default"),
    #("https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks4.txt", "socks4", "default"),
]

DEFAULT_TARGET_VALID = 30
DEFAULT_REFILL_THRESHOLD = 20


class Proxy:
    def __init__(
        self,
        target_valid: int = DEFAULT_TARGET_VALID,
        refill_threshold: int = DEFAULT_REFILL_THRESHOLD,
        initial_workers: int = 200,
        validator_workers: int = 100,
        validation_timeout: float = 2.5,
        validation_url: str = "https://www.youtube.com/",
        thumbnail_url: str = "https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg",
        profile_pic_dir: str = "https://yt3.ggpht.com/o7cU9OJXZZauZuaVvqhZkKlxQ02kgR6JMlQkoLZE7rU7VL8phOtJt_qUsPWJCGyrY10N9Kg9gA=s88-c-k-c0x00ffffff-no-rj-mo",
        status_callback=None,
    ):
        self.target_valid = target_valid
        self.refill_threshold = refill_threshold
        self.initial_workers = initial_workers
        self.validator_workers = validator_workers
        self.validation_timeout = validation_timeout
        self.validation_url = validation_url
        self.thumbnail_url = thumbnail_url
        self.profile_pic_url = profile_pic_dir
        self.time_taken_from_last_fetching = None

        self.working_proxies: Queue = Queue()
        self._seen_lock = threading.Lock()
        self._seen: Set[str] = set()
        self._candidates_lock = threading.Lock()
        self._candidates: List[Tuple[str, str]] = []

        self.should_stop = threading.Event()
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._initial_fill_thread = threading.Thread(target=self._initial_fill, daemon=True)
        self.status_callback = status_callback

        self._download_and_mix_proxies()
        self._initial_fill_thread.start()
        self._monitor_thread.start()
        atexit.register(self.cleanup)

    # -------------------------- Downloading --------------------------
    def _download_and_mix_proxies(self):
        candidates: List[Tuple[str, str, str]] = []
        for url, scheme, proxy_source in PROXY_SOURCES:
            try:
                print(f"[INFO] Fetching proxies from {url}")
                r = requests.get(url, timeout=10)
                self.time_taken_from_last_fetching = time.time()
                if r.status_code == 200:
                    if proxy_source == "Free-proxy-list":
                        data = json.loads(r.text)
                        data = data.get('data')
                        for d in data:
                            ip = d.get('ip')
                            port = d.get('port')
                            ipport = f"{ip}:{port}"
                            candidates.append((scheme, ipport))
                    else:
                        lines = [l.strip() for l in r.text.splitlines() if ":" in l]
                        for ln in lines:
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
            return f"socks5://{ipport}"
        elif scheme.lower().startswith("socks4"):
            return f"socks4://{ipport}"
        elif scheme.lower().startswith("https"):
            return f"https://{ipport}"
        return f"http://{ipport}"

    # -------------------------- Validation --------------------------
    def validate_proxy(self, proxy_url: str) -> bool:
        try:
            proxies = {"http": proxy_url, "https": proxy_url}

            # Step 1: Validate YouTube homepage
            r1 = requests.get(self.validation_url, proxies=proxies, timeout=self.validation_timeout)
            if r1.status_code != 200:
                return False

            # Step 2: Validate thumbnail
            r2 = requests.get(self.thumbnail_url, proxies=proxies, timeout=self.validation_timeout)
            if r2.status_code != 200:
                return False

            # Step 3: Validate YouTube profile picture
            r3 = requests.get(self.profile_pic_url, proxies=proxies, timeout=self.validation_timeout)
            return r3.status_code == 200

        except Exception:
            return False


    def _validate_batch(self, batch: List[Tuple[str, str]], max_add: int = 0):
        added = 0
        start = time.time()
        futures = {}
        with ThreadPoolExecutor(max_workers=self.validator_workers) as ex:
            for scheme, ipport in batch:
                if self.should_stop.is_set():
                    break
                proxy_url = self._build_proxy_url(scheme, ipport)
                futures[ex.submit(self.validate_proxy, proxy_url)] = proxy_url

            for fut in as_completed(futures):
                proxy_url = futures[fut]
                if self.should_stop.is_set():
                    break
                ok = False
                try:
                    ok = fut.result(timeout=self.validation_timeout + 1)
                except Exception:
                    pass

                if ok:
                    with self._seen_lock:
                        if proxy_url in self._seen:
                            continue
                        self._seen.add(proxy_url)
                    self.working_proxies.put_nowait(proxy_url)
                    added += 1
                    print(f"[VALID] {proxy_url}")
                    if self.status_callback:
                        self.status_callback(f"Valid proxy found ({self.working_proxies.qsize()}/3). \nMay take a Minute or two...")

                    if max_add and added >= max_add:
                        break

        elapsed = round(time.time() - start, 2)
        print(f"[DEBUG] Batch done: +{added}, total={self.working_proxies.qsize()}, took={elapsed}s")
        return added

    # -------------------------- Initial Fill --------------------------
    def _initial_fill(self):
        wanted = self.target_valid
        print("[INFO] Performing initial validation...")
        while not self.should_stop.is_set() and self.working_proxies.qsize() < wanted:
            with self._candidates_lock:
                if not self._candidates and (self.time_taken_from_last_fetching is not None and time.time()
                                             - self.time_taken_from_last_fetching > 60 * 20):
                    self._download_and_mix_proxies()
                batch = self._candidates[: self.initial_workers]
                self._candidates = self._candidates[self.initial_workers :]
            if not batch:
                break
            self._validate_batch(batch, max_add=wanted - self.working_proxies.qsize())

    # -------------------------- Background Monitor --------------------------
    def _monitor_loop(self):
        last_log = time.time()
        while not self.should_stop.is_set():
            size = self.working_proxies.qsize()
            if size < self.refill_threshold:
                with self._candidates_lock:
                    if not self._candidates and (self.time_taken_from_last_fetching is not None and self.time_taken_from_last_fetching
                                             - time.time() > 60 * 20):
                        self._download_and_mix_proxies()
                    batch = self._candidates[: self.initial_workers]
                    self._candidates = self._candidates[self.initial_workers :]
                self._validate_batch(batch, max_add=self.target_valid - size)

            if time.time() - last_log >= 3:
                print(f"[DEBUG] Working proxies: {self.working_proxies.qsize()}")
                last_log = time.time()
            time.sleep(1)

    # -------------------------- Accessors --------------------------
    def get_working_proxy(self, block: bool = False, timeout: float = 1.0) -> str | None:
        try:
            return self.working_proxies.get(block=block, timeout=timeout)
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

    def cleanup(self, join_timeout: float = 2.0):
        print("[INFO] Cleaning up ProxyPool...")
        self.should_stop.set()
        if self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=join_timeout)


if __name__ == "__main__":
    pool = Proxy()
    try:
        pool.ensure_sufficient_proxies(3)
        print(f"[INFO] Got {pool.peek_count()} proxies ready.")
        while pool.peek_count():
            print("[VALID-PROXY]", pool.get_working_proxy())
    finally:
        pool.cleanup()
