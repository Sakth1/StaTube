from swiftshadow.classes import ProxyInterface


class Proxy:
    def __init__(self, protocol: str = "http", auto_rotate: bool = True):
        """
        Wrapper for ProxyInterface to provide proxy rotation support.
        
        :param protocol: Proxy protocol ("http", "https", "socks4", "socks5").
        :param auto_rotate: Whether to enable automatic proxy rotation.
        """
        self.proxy_manager = ProxyInterface(
            protocol=protocol,
            autoRotate=auto_rotate
        )

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
