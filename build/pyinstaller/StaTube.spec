# PyInstaller spec for StaTube (PySide6, single-file portable EXE)
# FIXED: correct main.py path resolution

from PyInstaller.utils.hooks import collect_all
from pathlib import Path

block_cipher = None

# ---- Resolve project root ----
ROOT_DIR = Path(__file__).resolve().parents[2]

# ---- PySide6 ----
pyside6_datas, pyside6_binaries, pyside6_hiddenimports = collect_all("PySide6")

# ---- Other libs ----
yt_dlp_datas, yt_dlp_binaries, yt_dlp_hiddenimports = collect_all("yt_dlp")
nltk_datas, _, nltk_hiddenimports = collect_all("nltk")
wordcloud_datas, _, wordcloud_hiddenimports = collect_all("wordcloud")

a = Analysis(
    [str(ROOT_DIR / "main.py")],
    pathex=[str(ROOT_DIR)],
    binaries=pyside6_binaries + yt_dlp_binaries,
    datas=[
        (str(ROOT_DIR / "assets"), "assets"),
        (str(ROOT_DIR / "UI"), "UI"),
        (str(ROOT_DIR / "Data" / "schema.sql"), "Data/schema.sql"),
        (str(ROOT_DIR / "LICENSE"), "."),
        *pyside6_datas,
        *yt_dlp_datas,
        *nltk_datas,
        *wordcloud_datas,
    ],
    hiddenimports=[
        *pyside6_hiddenimports,
        *yt_dlp_hiddenimports,
        *nltk_hiddenimports,
        *wordcloud_hiddenimports,
        "scrapetube",
        "utils",
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="StaTube",
    debug=False,
    strip=False,
    upx=True,
    console=False,
    icon=str(ROOT_DIR / "assets" / "icon" / "StaTube.ico"),
)
