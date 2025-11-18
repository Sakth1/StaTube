# utils/CheckInternet.py
import requests

class Internet():
    def __init__(self):
        """
        Initialize the Internet class.

        This class provides a method to check if the device has internet access.
        """
        pass

    def check_internet(self, timeout: int = 5) -> bool:
        """
        Check if the device has internet access.

        Args:
            timeout (int): Timeout for the request in seconds.

        Returns:
            bool: True if internet is available, False otherwise.
        """
        test_url: str = "http://www.google.com"  # lightweight and reliable endpoint
        try:
            response: requests.Response = requests.get(test_url, timeout=timeout)
            return response.status_code == 200
        except requests.ConnectionError as e:
            print(f"[Internet Check] No internet connection: {e}")
            return False
        except requests.Timeout:
            print("[Internet Check] Connection timed out")
            return False
        except Exception as e:
            print(f"[Internet Check] Unexpected error: {e}")
            return False
