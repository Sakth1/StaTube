from cx_Freeze import setup, Executable
import os
import sys
from pathlib import Path

ROOT_DIR = Path.cwd()
sys.path.insert(0, str(ROOT_DIR))

# ---- Metadata from extract_metadata.py ----
APP_NAME = os.environ["APP_NAME"]
APP_VERSION = os.environ["APP_VERSION"]
APP_PUBLISHER = os.environ["APP_PUBLISHER"]
APP_DESCRIPTION = os.environ["APP_DESCRIPTION"]

# ---- Read locked UpgradeCode ----
UPGRADE_CODE = (ROOT_DIR / "build" / "installer" / "upgrade_code.txt").read_text().strip()

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
