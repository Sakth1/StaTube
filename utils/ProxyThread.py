# utils/ProxyThread.py
from PySide6.QtCore import QThread, Signal
import time
from typing import Optional
from .Proxy import Proxy  # adjust import if your module filename differs
from .AppState import app_state


class _ProxyWrapper:
    """
    Wrapper placed into app_state.proxy so other modules can call:
        app_state.proxy.get_working_proxy()
    This wrapper returns the same proxy twice before rotating to the next one.
    It delegates other useful methods to the underlying ProxyPool.
    """
    def __init__(self, pool: Proxy):
        self._pool = pool
        self._current_proxy: Optional[str] = None
        self._current_count = 0  # how many times we've served current_proxy (max 2)
        self._lock = False  # simple guard to avoid concurrent rotates (QThread usage is single-threaded but other threads may call)

    def _rotate_if_needed(self):
        """If current proxy exhausted, fetch a new one from the pool."""
        if self._current_proxy is None or self._current_count >= 2:
            # Try to get a new proxy from the pool (non-blocking)
            try:
                p = self._pool.get_working_proxy(block=False)
            except Exception:
                p = None

            # If none available, attempt a blocking short wait (1s) once
            if not p:
                p = self._pool.get_working_proxy(block=True, timeout=1.0)

            if p:
                self._current_proxy = p
                self._current_count = 0
            else:
                # no proxy available; keep current as-is (could be None)
                pass

    def get_working_proxy(self, block: bool = False, timeout: float = 1.0) -> Optional[str]:
        """
        Return the current proxy. Each proxy will be returned twice before moving to the next.
        If block=True and no proxy available, wait up to timeout seconds for one.
        """
        # If someone requested blocking, prefer to wait via underlying pool
        if block:
            # If we already have a current proxy and it hasn't been used twice, return it immediately
            if self._current_proxy and self._current_count < 2:
                self._current_count += 1
                return self._current_proxy

            # otherwise attempt to fetch (blocking) a new proxy from the pool
            p = self._pool.get_working_proxy(block=True, timeout=timeout)
            if p:
                self._current_proxy = p
                self._current_count = 1  # consumed once
                return self._current_proxy
            return None

        # Non-blocking behavior
        self._rotate_if_needed()
        if self._current_proxy:
            self._current_count += 1
            return self._current_proxy
        return None

    # convenience delegations
    def peek_count(self) -> int:
        return self._pool.peek_count()

    def ensure_sufficient_proxies(self, *args, **kwargs):
        return self._pool.ensure_sufficient_proxies(*args, **kwargs)

    def cleanup(self, *args, **kwargs):
        return self._pool.cleanup(*args, **kwargs)


class ProxyThread(QThread):
    """
    Background thread that manages a shared ProxyPool instance and emits signals:
      - proxy_updated(str): emitted when a new proxy becomes current (after rotation)
      - proxy_ready(): emitted when initial minimum proxies are available (3)
      - proxy_status(str): status text for splash screen updates
    """
    proxy_updated = Signal(str)
    proxy_ready = Signal()
    proxy_status = Signal(str)

    def __init__(self, rotation_interval: int = 100, min_initial_proxies: int = 3):
        """
        rotation_interval: seconds between automatic rotations (kept for compatibility, but
                           rotation also happens when get_working_proxy uses up the proxy twice).
        min_initial_proxies: how many validated proxies we wait for before emitting proxy_ready.
        """
        super().__init__()
        self.rotation_interval = rotation_interval
        self.min_initial_proxies = min_initial_proxies
        self._stop_requested = False
        self._wrapper: Optional[_ProxyWrapper] = None

    def run(self):
        """
        Thread entrypoint. This will:
          1. Create a ProxyPool and assign a wrapper into app_state.proxy.
          2. Wait until at least min_initial_proxies are validated, emitting status updates.
          3. Emit proxy_ready and then continue running, emitting periodic status logs and rotating proxies.
        """
        try:
            self.proxy_status.emit("Initializing proxy pool...")
            # Create the pool (this will start its own background monitor)
            pool = Proxy()  # uses defaults (30 target, 20 refill threshold) — can be parameterized
            self._wrapper = _ProxyWrapper(pool)

            # store the wrapper in global state (AppState). This allows other modules to call app_state.proxy.get_working_proxy()
            app_state.proxy = self._wrapper

            # Wait for at least min_initial_proxies to be available
            self.proxy_status.emit(f"Validating proxies (need {self.min_initial_proxies})...")
            # We'll poll and emit status every 3 seconds as requested
            last_emit = 0
            while not self._stop_requested:
                count = self._wrapper.peek_count()
                now = time.time()
                if now - last_emit >= 3:
                    self.proxy_status.emit(f"Validated proxies: {count}")
                    last_emit = now
                if count >= self.min_initial_proxies:
                    break
                time.sleep(0.5)

            # Initial ready
            self.proxy_status.emit(f"Proxy pool ready ({self._wrapper.peek_count()} proxies).")
            self.proxy_ready.emit()

            # Optionally emit the current proxy immediately (so UI can display the first proxy)
            # Ensure there is a current proxy available in the wrapper; fetch non-blocking
            first = self._wrapper.get_working_proxy(block=False)
            if first:
                # Because wrapper returns same proxy twice, calling get_working_proxy again will return same value.
                # Emit proxy_updated to notify UI
                self.proxy_updated.emit(first)

            # Main loop: periodically emit status and handle rotation interval (100s)
            # Note: rotation truly happens when callers request proxies; we emit proxy_status regularly and rotate proactively here.
            last_rotation = time.time()
            while not self._stop_requested:
                # regular status update every ~3 seconds
                self.proxy_status.emit(f"Validated proxies: {self._wrapper.peek_count()}")
                # Rotate proactively if rotation_interval elapsed: consume remaining uses of current proxy so next call returns new one
                if time.time() - last_rotation >= self.rotation_interval:
                    # Force a rotation by marking current proxy as used twice (so next get_working_proxy rotates)
                    # We'll fetch current to see what it is, then artificially bump count so next fetch changes.
                    # Since wrapper internal state is private, we call get_working_proxy twice to consume it (if available).
                    cur = self._wrapper.get_working_proxy(block=False)
                    if cur:
                        # consume the second time to force rotation
                        _ = self._wrapper.get_working_proxy(block=False)
                        # Now fetch the next (non-blocking) to get the new current proxy
                        newp = self._wrapper.get_working_proxy(block=False)
                        if newp and newp != cur:
                            self.proxy_updated.emit(newp)
                    last_rotation = time.time()

                # Sleep a bit but wake frequently to keep UI responsive for stop requests
                for _ in range(3):
                    if self._stop_requested:
                        break
                    time.sleep(1)

        except Exception as e:
            # If an unexpected error happens, emit a status so the UI can show it.
            import traceback
            traceback.print_exc()
            self.proxy_status.emit(f"[ERROR] ProxyThread failed: {e}")
        finally:
            # cleanup handled in stop() as well, but ensure pool is cleaned if present
            try:
                if self._wrapper:
                    self._wrapper.cleanup()
            except Exception:
                pass

    def stop(self):
        """Request thread stop and cleanup resources."""
        self._stop_requested = True
        # instruct underlying pool to cleanup if present
        try:
            if self._wrapper:
                self._wrapper.cleanup()
        except Exception:
            pass
        # politely stop the thread and allow run() to exit
        self.quit()
        self.wait(2000)
