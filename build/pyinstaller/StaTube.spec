# PyInstaller spec for StaTube (PySide6, single-file portable EXE)

from PyInstaller.utils.hooks import collect_all

block_cipher = None

# ---- PySide6 collection ----
pyside6_datas, pyside6_binaries, pyside6_hiddenimports = collect_all("PySide6")

# ---- Other dynamic / data-heavy libs ----
yt_dlp_datas, yt_dlp_binaries, yt_dlp_hiddenimports = collect_all("yt_dlp")
nltk_datas, _, nltk_hiddenimports = collect_all("nltk")
wordcloud_datas, _, wordcloud_hiddenimports = collect_all("wordcloud")

a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=pyside6_binaries + yt_dlp_binaries,
    datas=[
        ("assets", "assets"),
        ("UI", "UI"),
        ("Data/schema.sql", "Data/schema.sql"),
        ("LICENSE", "."),
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
    icon="assets/icon/StaTube.ico",
)
