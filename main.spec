# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec - shared across macOS, Windows and Linux.
# Build with: pyinstaller main.spec --noconfirm
import sys

APP_NAME = "PhotoVideoSorter"

ui_files = [
    ("sidebar.ui", "."),
    ("step0_welcome.ui", "."),
    ("step1_source.ui", "."),
    ("step2_destination.ui", "."),
    ("step3_sorting.ui", "."),
    ("step4_summary.ui", "."),
]

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=ui_files,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    debug=False,
    strip=False,
    upx=False,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name=APP_NAME,
)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="Photo & Video Sorter.app",
        bundle_identifier="com.dominikserafin.photovideosorter",
        info_plist={
            "NSHighResolutionCapable": True,
            "CFBundleShortVersionString": "1.0.0",
            "CFBundleName": "Photo & Video Sorter",
        },
    )
