import logging
import os
from datetime import datetime
import platform
from pathlib import Path

def get_documents_dir():
    system = platform.system()
    return Path(os.path.expanduser("~/Documents"))

def setup_logger():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    documents_dir = get_documents_dir()

    log_dir = documents_dir / "StaTube"
    log_dir.mkdir(parents=True, exist_ok=True)

    file_path = log_dir / f"statube_log_{timestamp}.log"

    logger = logging.getLogger("StaTube")
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - "
        "%(message)s [%(module)s:%(funcName)s:%(lineno)d]"
    )

    # File handler
    fh = logging.FileHandler(file_path, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    logger.propagate = False
    return logger, file_path

logger, log_file_path = setup_logger()
