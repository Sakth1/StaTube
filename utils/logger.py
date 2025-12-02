import logging
import os
import time
from pathlib import Path
import platform

def get_documents_dir():
    """Return OS-specific documents directory."""
    system = platform.system()

    if system == "Windows":
        return Path(os.path.expanduser("~/Documents"))
    elif system == "Darwin":  # macOS
        return Path(os.path.expanduser("~/Documents"))
    else:  # Linux or others
        return Path(os.path.expanduser("~/Documents"))

def setup_logger():
    timestamp_ms = int(time.time() * 1000)
    documents_dir = get_documents_dir()

    # StaTube log directory
    log_dir = documents_dir / "StaTube"
    log_dir.mkdir(parents=True, exist_ok=True)

    file_path = log_dir / f"statube_log_{timestamp_ms}.log"

    logger = logging.getLogger("StaTube")
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - "
        "%(message)s [%(module)s:%(funcName)s:%(lineno)d]"
    )

    fh = logging.FileHandler(file_path, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)

    logger.addHandler(fh)
    logger.propagate = False

    return logger, file_path

logger, log_file_path = setup_logger()
