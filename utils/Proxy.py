import requests
from swiftshadow.classes import ProxyInterface

class Proxy:
    def __init__(self, protocol = "http", auto_rotate: bool = True):
        self.proxy_manager = ProxyInterface(
            countries=["US"],
            protocol=protocol,
            autoRotate=auto_rotate
        )

    def validate_proxy(self, proxy_str: str) -> bool:
        """Check if proxy works by pinging YouTube."""
        try:
            response = requests.get(
                "https://www.youtube.com/",
                proxies={'http': proxy_str},
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            print(f"[ERROR] Proxy validation failed: {e}")
            return False

    def get_working_proxy(self) -> str | None:
        """Fetch proxy and validate it."""
        try:
            i = 0
            print(len(self.proxy_manager.proxies))
            while i < len(self.proxy_manager.proxies):
                self.proxy_manager.rotate()
                proxy_obj = self.proxy_manager.get()
                if not proxy_obj:
                    continue
                proxy_str = proxy_obj.as_string()
                print(f"[INFO] Testing proxy: {proxy_str}")
                if self.validate_proxy(proxy_str):
                    return proxy_str
                i += 1
            print("[ERROR] No working HTTPS proxy found.")
            return None
        except Exception as e:
            print(f"[ERROR] Proxy validation failed: {e}")
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


# Example usage
if __name__ == "__main__":
    proxy = Proxy(protocol="http")
    proxy_str = proxy.get_proxy()
    if proxy_str:
        print(f"[INFO] Using proxy: {proxy_str}")
    else:
        print("[WARN] No proxy available.")
