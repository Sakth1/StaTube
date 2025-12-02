import logging
import os
import time
import platform
from pathlib import Path
import argparse

def get_documents_dir():
    system = platform.system()
    return Path(os.path.expanduser("~/Documents"))

def is_debug_mode():
    # Option A: --debug
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--debug", action="store_true")
    args, _ = parser.parse_known_args()

    # Option B: ENV variable
    env_flag = os.environ.get("STATUBE_DEBUG", "0") == "1"

    return args.debug or env_flag

def setup_logger():
    timestamp_ms = int(time.time() * 1000)
    documents_dir = get_documents_dir()

    log_dir = documents_dir / "StaTube"
    log_dir.mkdir(parents=True, exist_ok=True)

    file_path = log_dir / f"statube_log_{timestamp_ms}.log"

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

    # Console handler only if debug mode
    if is_debug_mode():
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    logger.propagate = False
    return logger, file_path

logger, log_file_path = setup_logger()
