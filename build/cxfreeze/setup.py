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
APP_DESCRIPTION = os.environ.get("APP_DESCRIPTION", "YouTube utility and analysis tool")

# --------------------------------------------------
# UpgradeCode (stable, validated)
# --------------------------------------------------
upgrade_file = ROOT_DIR / "build" / "installer" / "upgrade_code.txt"
raw = upgrade_file.read_text(encoding="utf-8").strip()

UUID_REGEX = r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
if not re.fullmatch(UUID_REGEX, raw.strip("{}")):
    raise RuntimeError(f"Invalid UpgradeCode: {repr(raw)}")

UPGRADE_CODE = "{" + raw.strip("{}").upper() + "}"

# --------------------------------------------------
# Executable config
# --------------------------------------------------
base = "Win32GUI" if sys.platform == "win32" else None

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

# --------------------------------------------------
# Build options
# --------------------------------------------------
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

# --------------------------------------------------
# MSI UI / installer behavior
# --------------------------------------------------
bdist_msi_options = {
    # Identity
    "upgrade_code": UPGRADE_CODE,

    # UI flow
    "initial_target_dir": rf"[ProgramFilesFolder]\{APP_NAME}",
    "license_file": str(ROOT_DIR / "LICENSE"),

    # Shortcuts
    "add_to_path": False,
    "install_icon": str(ROOT_DIR / "assets" / "icon" / "StaTube.ico"),

    # Installer metadata
    "summary_data": {
        "author": APP_PUBLISHER,
        "comments": APP_DESCRIPTION,
    },

    # All-users install (shows per-user vs all-users choice)
    "all_users": False,
}

# --------------------------------------------------
# Setup
# --------------------------------------------------
setup(
    name=APP_NAME,
    version=APP_VERSION,
    description=APP_DESCRIPTION,
    author=APP_PUBLISHER,
    executables=executables,
    options={
        "build_exe": build_exe_options,
        "bdist_msi": bdist_msi_options,
    },
)
