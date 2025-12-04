# logger_config.py
import logging
import os
from datetime import datetime
import platform
from pathlib import Path


class EscapingFormatter(logging.Formatter):
    """Formatter that escapes newline characters in log messages."""
    def format(self, record):
        s = super().format(record)
        return s.replace('\n', r'\n')


def get_documents_dir():
    """Return the user's Documents directory in a cross-platform safe way."""
    return Path(os.path.expanduser("~/Documents"))


def setup_logger():
    logger = logging.getLogger("StaTube")
    logger.setLevel(logging.DEBUG)

    # Prevent duplicate handlers if logger is reloaded
    if logger.handlers:
        return logger, None

    # Timestamped file name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Directory: ~/Documents/StaTube/
    documents_dir = get_documents_dir()
    log_dir = documents_dir / "StaTube"
    log_dir.mkdir(parents=True, exist_ok=True)

    # Example: statube_log_20251204_162233.log
    log_file_path = log_dir / f"statube_log_{timestamp}.log"

    # Log format similar to your "driving_pattern" version
    fmt = (
        "%(asctime)s | %(levelname)-8s | "
        "%(filename)s:%(lineno)d | %(module)s.%(funcName)s | "
        "%(message)s"
    )
    formatter = EscapingFormatter(fmt)

    # File handler
    fh = logging.FileHandler(log_file_path, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # Optional: console output
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    logger.propagate = False

    logger.debug(f"StaTube logger initialized at: {log_file_path}")

    return logger, log_file_path


# Initialize logger when imported
logger, log_file_path = setup_logger()

