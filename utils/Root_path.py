from pathlib import Path
import sys

def get_app_root() -> Path:
    """
    Returns the root directory of the application, regardless of:
    - script
    - cx_Freeze
    - PyInstaller (onefile / onedir)
    """
    if getattr(sys, "frozen", False):
        # cx_Freeze / PyInstaller
        return Path(sys.executable).parent
    else:
        # Normal Python execution
        return Path(__file__).resolve().parents[1]
