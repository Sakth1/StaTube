# utils/CheckInternet.py
import requests
from utils.logger import logger

class Internet():
    def __init__(self):
        """Initialize Internet checker."""
        logger.debug("Internet checker initialized.")

    def check_internet(self, timeout: int = 5) -> bool:
        """
        Check if internet is accessible.
        """
        test_url: str = "http://www.youtube.com"

        try:
            logger.debug(f"Checking internet connectivity using URL: {test_url}")
            response: requests.Response = requests.get(test_url, timeout=timeout)
            ok = response.status_code == 200
            logger.debug(f"Internet check status_code={response.status_code}, ok={ok}")
            return ok

        except requests.ConnectionError as e:
            logger.warning(f"No internet connection: {e}")
            logger.debug("ConnectionError details:", exc_info=True)
            return False

        except requests.Timeout:
            logger.warning("Internet check timed out.")
            return False

        except Exception as e:
            logger.exception("Unexpected error during internet check:")
            return False
