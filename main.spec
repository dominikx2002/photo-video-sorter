# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec - shared across macOS, Windows and Linux.
# Build with: pyinstaller main.spec --noconfirm
import sys

APP_NAME = "PhotoVideoSorter"

ui_files = [
    ("ui/sidebar.ui", "ui"),
    ("ui/step0_welcome.ui", "ui"),
    ("ui/step1_source.ui", "ui"),
    ("ui/step2_destination.ui", "ui"),
    ("ui/step3_sorting.ui", "ui"),
    ("ui/step4_summary.ui", "ui"),
    ("packaging/icons/icon.png", "packaging/icons"),
    ("packaging/icons/check.svg", "packaging/icons"),
    ("packaging/icons/chevron-down.svg", "packaging/icons"),
    ("packaging/icons/compare.svg", "packaging/icons"),
    ("packaging/icons/duplicates.svg", "packaging/icons"),
]

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=ui_files,
    hiddenimports=["defusedxml", "defusedxml.ElementTree"],
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
    icon="packaging/icons/icon.ico" if sys.platform == "win32" else None,
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
        icon="packaging/icons/icon.icns",
        bundle_identifier="com.dominikserafin.photovideosorter",
        info_plist={
            "NSHighResolutionCapable": True,
            "CFBundleShortVersionString": "1.2.0",
            "CFBundleName": "Photo & Video Sorter",
        },
    )
