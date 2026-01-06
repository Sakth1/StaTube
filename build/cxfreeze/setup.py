from cx_Freeze import setup, Executable
import os
import sys
import re
from pathlib import Path

# --------------------------------------------------
# Resolve project root
# --------------------------------------------------
ROOT_DIR = Path.cwd()
sys.path.insert(0, str(ROOT_DIR))

# --------------------------------------------------
# Metadata from extract_metadata.py
# --------------------------------------------------
APP_NAME = os.environ.get("APP_NAME", "StaTube")
APP_VERSION = os.environ.get("APP_VERSION", "0.0.0")
APP_PUBLISHER = os.environ.get("APP_PUBLISHER", "Unknown")
APP_DESCRIPTION = os.environ.get("APP_DESCRIPTION", "Unknown")

# --------------------------------------------------
# Read UpgradeCode (stored WITHOUT braces)
# --------------------------------------------------
upgrade_file = ROOT_DIR / "build" / "installer" / "upgrade_code.txt"
raw = upgrade_file.read_text(encoding="utf-8")

UPGRADE_CODE_RAW = raw.strip().lower()

# Validate UUID (no braces)
if not re.fullmatch(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
    UPGRADE_CODE_RAW,
):
    raise RuntimeError(f"Invalid UpgradeCode in file: {repr(UPGRADE_CODE_RAW)}")

# cx_Freeze / msilib REQUIRES braces
UPGRADE_CODE = f"{{{UPGRADE_CODE_RAW}}}"

# --------------------------------------------------
# cx_Freeze configuration
# --------------------------------------------------
base = "Win32GUI" if sys.platform == "win32" else None

build_exe_options = {
    "packages": [
        "PySide6",
        "yt_dlp",
        "nltk",
        "wordcloud",
        "scrapetube",
    ],
    "excludes": ["tkinter", "tk", "tcl"],
    "include_files": [
        (ROOT_DIR / "utils", "utils"),
        (ROOT_DIR / "UI", "UI"),
        (ROOT_DIR / "assets", "assets"),
        (ROOT_DIR / "Data" / "schema.sql", "Data/schema.sql"),
        (ROOT_DIR / "LICENSE", "LICENSE"),
    ],
    "include_msvcr": True,
}

bdist_msi_options = {
    "upgrade_code": UPGRADE_CODE,
    "initial_target_dir": r"[ProgramFilesFolder]\StaTube",
    "summary_data": {
        "author": APP_PUBLISHER,
        "comments": APP_DESCRIPTION,
    },
}

executables = [
    Executable(
        script=str(ROOT_DIR / "main.py"),
        base=base,
        target_name="StaTube.exe",
        icon=str(ROOT_DIR / "assets" / "icon" / "StaTube.ico"),
        shortcut_name=APP_NAME,
        shortcut_dir="ProgramMenuFolder",
    )
]

setup(
    name=APP_NAME,
    version=APP_VERSION,
    description=APP_DESCRIPTION,
    author=APP_PUBLISHER,
    options={
        "build_exe": build_exe_options,
        "bdist_msi": bdist_msi_options,
    },
    executables=executables,
)
