from pathlib import Path

from PyInstaller.building.build_main import Analysis, COLLECT, EXE, PYZ
from PyInstaller.utils.hooks import collect_all, collect_submodules


ROOT = Path(SPECPATH).parent
webview_datas, webview_binaries, webview_hiddenimports = collect_all("webview")
hiddenimports = webview_hiddenimports + collect_submodules("pystray") + ["cross_read.main"]

analysis = Analysis(
    [str(ROOT / "src" / "cross_read" / "desktop.py")],
    pathex=[str(ROOT / "src")],
    binaries=webview_binaries,
    datas=webview_datas
    + [
        (str(ROOT / "config.example.yaml"), "."),
        (str(ROOT / "src" / "cross_read" / "static"), "cross_read/static"),
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter"],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(analysis.pure)
exe = EXE(
    pyz,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="CrossRead",
    icon=str(ROOT / "assets" / "cross-read.ico"),
    version=str(ROOT / "packaging" / "version_info.txt"),
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)

collect = COLLECT(
    exe,
    analysis.binaries,
    analysis.datas,
    strip=False,
    upx=True,
    name="CrossRead",
)
