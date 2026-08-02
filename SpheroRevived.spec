# -*- mode: python ; coding: utf-8 -*-
import sys
WINDOWS_ICON = "assets/icon.ico" if sys.platform == "win32" else None


from PyInstaller.utils.hooks import collect_submodules

hidden_imports = collect_submodules("bleak")

analysis = Analysis(
    ["run.py"],
    pathex=["."],
    binaries=[],
    datas=[
        (
            "firmware/bb8/working_donor_application.bin",
            "firmware/bb8",
        ),
    ],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(analysis.pure)

executable = EXE(
    pyz,
    analysis.scripts,
    analysis.binaries,
    analysis.datas,
    [],
    name="SpheroRevived",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    icon=WINDOWS_ICON,
)
