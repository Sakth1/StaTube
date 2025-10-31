# Proxy.py
import requests
import threading
from queue import Queue
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import atexit
from urllib.parse import urlparse

class Proxy:
    """
    Self-contained proxy manager.
    - Fetches proxies from multiple public sources
    - Validates them concurrently
    - Keeps a queue of working proxies for other modules to consume
    """

    DEFAULT_SOURCES = [
        # TheSpeedX raw lists
        ("https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks4.txt", "socks4"),
        ("https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks5.txt", "socks5"),
        ("https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt", "http"),
        # ProxyScrape API (good fallback)
        ("https://api.proxyscrape.com/?request=getproxies&proxytype=http&timeout=10000&country=all&ssl=all&anonymity=all", "http"),
        ("https://api.proxyscrape.com/?request=getproxies&proxytype=socks4&timeout=10000&country=all", "socks4"),
        ("https://api.proxyscrape.com/?request=getproxies&proxytype=socks5&timeout=10000&country=all", "socks5"),
        # Alternate sources (may be slow/unreliable but useful)
        ("https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt", "http"),
    ]

    def __init__(self, protocol: str = "http", auto_rotate: bool = True, max_working_proxies: int = 50):
        self.protocol = protocol  # default protocol hint for get_proxy
        self.auto_rotate = auto_rotate
        self.max_working_proxies = max_working_proxies

        # requests session for re-use
        self._session = requests.Session()
        # Add common headers to look a bit less like a bot
        self._session.headers.update({
            "User-Agent": "Mozilla/5.0 (compatible; ProxyValidator/1.0; +https://example.com/)"
        })

        # Candidate proxies awaiting validation: list of (proxy_string, proxy_type)
        self._candidates = []
        self._candidates_lock = threading.Lock()

        # Queue of validated working proxies (strings like "http://ip:port" or "socks5://ip:port")
        self.working_proxies = Queue()

        # control flags
        self.should_stop = threading.Event()

        # Threads
        self.fetcher_thread = threading.Thread(target=self._fetcher_loop, daemon=True)
        self.validator_threads = []
        self._start_background_workers(num_validator_threads=3)

        # Start fetching and validating
        self.fetcher_thread.start()

        atexit.register(self.cleanup)

    # ----------------------------
    # Public API
    # ----------------------------
    def get_working_proxy(self) -> str | None:
        """
        Return a validated working proxy string in the form:
          - "http://ip:port"
          - "socks5://ip:port"
        Returns None if queue is empty.
        """
        try:
            if self.working_proxies.empty():
                return None
            return self.working_proxies.get_nowait()
        except Exception as e:
            print(f"[ERROR] get_working_proxy: {e}")
            return None

    def get_proxy(self) -> str | None:
        """
        Return a raw (not necessarily validated) proxy from candidates in the preferred protocol.
        If none available, returns None.
        """
        with self._candidates_lock:
            # prefer the configured protocol first
            for idx, (pstr, ptype) in enumerate(self._candidates):
                if ptype == self.protocol:
                    return pstr
            # fallback to any
            if self._candidates:
                return self._candidates[0][0]
        return None

    def ensure_sufficient_proxies(self) -> bool:
        """
        Block until we have at least 2 working proxies (or until stopped).
        Returns True when satisfied, False if stopped before.
        """
        while not self.should_stop.is_set():
            if self.working_proxies.qsize() > 1:
                return True
            time.sleep(0.5)
        return False

    def cleanup(self):
        """
        Gracefully stop background workers.
        """
        print("[INFO] Proxy.cleanup: stopping background workers...")
        self.should_stop.set()

        # Join fetcher thread
        if self.fetcher_thread.is_alive():
            self.fetcher_thread.join(timeout=2)

        # Join validator threads
        for t in self.validator_threads:
            if t.is_alive():
                t.join(timeout=2)

        try:
            self._session.close()
        except Exception:
            pass

    # ----------------------------
    # Internal: fetching proxies
    # ----------------------------
    def _fetch_proxies_from_url(self, url: str, proxy_type: str) -> list:
        """
        Download a plain-text list of proxies from url.
        Gracefully handles rate limits (HTTP 429) and temporary errors.
        Implements automatic backoff for 10 minutes on rate-limited sources.
        """
        # static cache for backoff state (shared across instances)
        if not hasattr(self, "_rate_limited_sources"):
            self._rate_limited_sources = {}

        # Skip URL if still in backoff
        last_fail = self._rate_limited_sources.get(url, 0)
        if time.time() - last_fail < 600:  # 10 minutes
            print(f"[BACKOFF] Skipping {url} (still in cooldown after 429)")
            return []

        try:
            resp = self._session.get(url, timeout=10)
            code = resp.status_code

            if code == 429:
                print(f"[RATE LIMIT] {url} -> HTTP 429 (Too Many Requests). Backing off 10 min.")
                self._rate_limited_sources[url] = time.time()
                return []
            elif code >= 400:
                print(f"[WARN] Source {url} returned HTTP {code}")
                return []

            # Parse response lines into proxy list
            result = []
            for ln in resp.text.splitlines():
                ln = ln.strip()
                if not ln or ln.startswith("#"):
                    continue
                if "://" in ln:
                    try:
                        ln = urlparse(ln).netloc
                    except Exception:
                        ln = ln.split("://", 1)[-1]
                if ":" not in ln:
                    continue
                result.append((ln, proxy_type))

            return result

        except requests.exceptions.RequestException as e:
            # transient network errors, timeouts, etc.
            print(f"[WARN] Could not fetch from {url}: {e}")
            return []
        except Exception as e:
            # unexpected (still log safely)
            print(f"[ERROR] Unexpected error while fetching {url}: {e}")
            return []

    def _merge_new_candidates(self, new_list: list):
        """
        Add new candidates into self._candidates without duplicates.
        new_list: list of (proxy_str, proxy_type)
        """
        with self._candidates_lock:
            existing = set(self._candidates)
            for item in new_list:
                if item not in existing:
                    self._candidates.append(item)
                    existing.add(item)

    def _fetcher_loop(self):
        """
        Periodically fetch lists of proxies from configured sources and add them to candidates.
        This runs in its own thread.
        """
        print("[INFO] Proxy.fetcher: started")
        # initial immediate fetch
        fetch_interval = 60  # seconds between refreshes
        while not self.should_stop.is_set():
            all_new = []
            for url, ptype in self.DEFAULT_SOURCES:
                if self.should_stop.is_set():
                    break
                proxies = self._fetch_proxies_from_url(url, ptype)
                if proxies:
                    all_new.extend(proxies)
            if all_new:
                self._merge_new_candidates(all_new)
                print(f"[INFO] Proxy.fetcher: added {len(all_new)} new candidates (total candidates: {len(self._candidates)})")
            else:
                print("[INFO] Proxy.fetcher: no new candidates fetched this round")

            # If we've already reached capacity of working proxies, wait longer before fetching again
            if self.working_proxies.qsize() >= self.max_working_proxies:
                sleep_for = fetch_interval * 5
            else:
                sleep_for = fetch_interval

            for _ in range(int(sleep_for / 1)):
                if self.should_stop.is_set():
                    break
                time.sleep(1)
        print("[INFO] Proxy.fetcher: stopped")

    # ----------------------------
    # Internal: validation
    # ----------------------------
    def _start_background_workers(self, num_validator_threads=3):
        """
        Start a number of background validator threads that each run a validator loop.
        """
        for i in range(num_validator_threads):
            t = threading.Thread(target=self._validate_proxies_worker, daemon=True, name=f"ProxyValidator-{i}")
            t.start()
            self.validator_threads.append(t)

    def _validate_proxies_worker(self):
        """
        Background validator worker:
        - Grabs batches of candidates
        - Validates them concurrently using ThreadPoolExecutor
        - Stores working proxies into self.working_proxies (queue)
        - Stops when self.should_stop set or when working_proxies reaches capacity
        """
        print(f"[INFO] {threading.current_thread().name} started")
        while not self.should_stop.is_set():
            # stop if we already have enough working proxies
            if self.working_proxies.qsize() >= self.max_working_proxies:
                # sleep a bit and re-check later (allows fetcher to reduce load)
                time.sleep(1)
                continue

            # prepare a batch of candidates (up to 50 each worker will attempt)
            batch = []
            with self._candidates_lock:
                # pop up to N candidates to test, avoid removing them permanently
                # we'll rotate them: test then append back if not working
                pop_count = min(60, max(10, len(self._candidates)))
                for _ in range(pop_count):
                    if not self._candidates:
                        break
                    batch.append(self._candidates.pop(0))

            if not batch:
                # nothing to validate; wait a bit for fetcher
                time.sleep(1)
                continue

            # validate batch concurrently
            with ThreadPoolExecutor(max_workers=20) as executor:
                futures = {executor.submit(self._validate_single_proxy, proxy, ptype): (proxy, ptype) for proxy, ptype in batch}
                for future in as_completed(futures):
                    if self.should_stop.is_set():
                        break
                    result = None
                    try:
                        result = future.result(timeout=6)  # short timeout on result
                    except Exception:
                        # individual validation failures are normal
                        result = None

                    proxy_tuple = futures[future]
                    # if success, put into working queue
                    if result:
                        proxy_url = result  # normalized proxy URL like "http://ip:port"
                        # avoid duplicates in working queue
                        # Since Queue has no easy membership test, do a quick approximate check:
                        if self.working_proxies.qsize() < self.max_working_proxies:
                            self.working_proxies.put(proxy_url)
                            print(f"[✓] Working proxy added: {proxy_url} (total working: {self.working_proxies.qsize()})")
                            if self.working_proxies.qsize() >= self.max_working_proxies:
                                break
                    else:
                        # if not working, re-insert into candidates tail for future attempts (rotation)
                        with self._candidates_lock:
                            # re-use the original proxy_tuple forms "ip:port" with ptype
                            self._candidates.append(proxy_tuple)

            # lightweight sleep to avoid hot-looping
            time.sleep(0.2)

        print(f"[INFO] {threading.current_thread().name} stopped")

    def _validate_single_proxy(self, proxy_str: str, proxy_type: str) -> str | None:
        """
        Validate a single proxy by attempting to GET https://www.youtube.com.
        Returns a proxy URL string on success (e.g. 'http://1.2.3.4:8080' or 'socks5://1.2.3.4:1080'),
        or None if invalid/unresponsive.
        NOTE: Validation uses the requests library. For SOCKS proxies, ensure 'requests[socks]' is installed
              (PySocks) to allow requests to use 'socks5://'/'socks4://' schemes.
        """
        if self.should_stop.is_set():
            return None

        # build scheme + proxy url
        scheme = proxy_type if proxy_type in ("http", "https", "socks4", "socks5") else proxy_type
        proxy_url = f"{scheme}://{proxy_str}"

        # Use a short timeout to validate quickly
        timeout = 5.0

        # Build proxies dict for requests
        proxies = {
            'http': proxy_url,
            'https': proxy_url
        }

        try:
            # We set allow_redirects=False to avoid extra time in redirects
            resp = self._session.get("https://www.youtube.com/", proxies=proxies, timeout=timeout, allow_redirects=False)
            if resp.status_code == 200:
                # quick sanity: return standardized proxy_url
                return proxy_url
            # some proxies may return 301/302; treat 200 as success only (safer)
        except Exception:
            # likely connection timeout / proxy refused / unsupported scheme
            return None
        return None

# Example quick test if module run directly
if __name__ == "__main__":
    p = Proxy(max_working_proxies=10)
    try:
        print("Waiting for some working proxies (max 10)...")
        # wait until we have at least 1 or until 60 seconds elapsed
        waited = 0
        while p.working_proxies.qsize() < 1 and waited < 60:
            time.sleep(1)
            waited += 1
            print(f"Waiting... ({waited}s) working={p.working_proxies.qsize()}")
        print("Collected working proxies:")
        while not p.working_proxies.empty():
            print(" -", p.get_working_proxy())
    finally:
        p.cleanup()
