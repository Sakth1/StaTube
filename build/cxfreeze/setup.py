from cx_Freeze import setup, Executable
import os
import sys
from pathlib import Path

# ---- Ensure project root is importable ----
ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))

# ---- Metadata injected by CI ----
APP_NAME = os.environ["APP_NAME"]
APP_VERSION = os.environ["APP_VERSION"]
APP_PUBLISHER = os.environ["APP_PUBLISHER"]
APP_DESCRIPTION = os.environ["APP_DESCRIPTION"]

base = "Win32GUI" if sys.platform == "win32" else None

build_exe_options = {
    # ONLY real pip packages here
    "packages": [
        "PySide6",
        "yt_dlp",
        "nltk",
        "wordcloud",
        "scrapetube",
    ],
    # Local source + data
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
    # DO NOT change once released
    "upgrade_code": "{A6F3E7B2-5E0F-4B58-9D9C-STATUBE000001}",
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
