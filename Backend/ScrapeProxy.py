import requests
import concurrent.futures
import threading

class ProxyFetcher:
    def __init__(self, url="https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt"):
        self.url = url
        self.valid_proxies = []
        self.lock = threading.Lock()

    def fetch_proxies(self):
        response = requests.get(self.url, timeout=10)
        response.raise_for_status()
        proxies = response.text.strip().split('\n')
        return proxies

    def check_proxy(self, proxy, limit=100):
        if len(self.valid_proxies) >= limit:
            return  # stop if we already have enough

        test_url = "http://httpbin.org/ip"
        try:
            print(f"Testing proxy: {proxy}")
            response = requests.get(
                test_url,
                proxies={"http": f"http://{proxy}", "https": f"http://{proxy}"},
                timeout=5
            )
            if response.status_code == 200:
                with self.lock:
                    print(f"Valid proxy: {proxy}")
                    print(f'Total proxies: {len(self.valid_proxies)}')
                    if len(self.valid_proxies) < limit:  # check again inside lock
                        self.valid_proxies.append(proxy)
        except Exception:
            pass

    def validate_proxies(self, proxies, workers=20, limit=100):
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(self.check_proxy, proxy, limit) for proxy in proxies]
            concurrent.futures.wait(futures, return_when=concurrent.futures.FIRST_COMPLETED)
        return self.valid_proxies[:limit]


if __name__ == "__main__":
    proxy_fetcher = ProxyFetcher()
    proxies = proxy_fetcher.fetch_proxies()
    print(f"Fetched {len(proxies)} proxies.")

    valid = proxy_fetcher.validate_proxies(proxies, limit=15)
    print(f"Usable proxies: {len(valid)}")
