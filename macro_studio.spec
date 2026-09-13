# -*- mode: python ; coding: utf-8 -*-
# Macro Studio — Windows one-folder build (customtkinter / pynput 안정성·시작속도·AV 오탐↓)
#
# 빌드: pyinstaller macro_studio.spec
# 결과: dist/MacroStudio/MacroStudio.exe  (+ _internal 등)
# macros/ 는 런타임에 exe 옆에 생성 (storage.get_project_root).

from PyInstaller.utils.hooks import collect_all

block_cipher = None

datas = []
binaries = []
hiddenimports = [
    "customtkinter",
    "darkdetect",
    "packaging",
    "packaging.version",
    "packaging.specifiers",
    "packaging.requirements",
    "pynput",
    "pynput.keyboard",
    "pynput.keyboard._win32",
    "pynput.mouse",
    "pynput.mouse._win32",
    "pynput._util",
    "pynput._util.win32",
    "screeninfo",
    "screeninfo.enumerators",
    "screeninfo.enumerators.windows",
    "macro_studio",
    "macro_studio.app",
    "macro_studio.app_hotkeys",
    "macro_studio.models",
    "macro_studio.storage",
    "macro_studio.recorder",
    "macro_studio.player",
    "macro_studio.monitors",
    "macro_studio.share",
    "macro_studio.ui_slots",
    "macro_studio.ui_slots_ops",
    "macro_studio.ui_share",
    "macro_studio.ui_events",
    "macro_studio.ui_events_edit",
    "macro_studio.ui_clipboard",
]

for pkg in ("customtkinter", "darkdetect"):
    try:
        d, b, h = collect_all(pkg)
        datas += d
        binaries += b
        hiddenimports += h
    except Exception:
        pass

a = Analysis(
    ["run_macro_studio.py"],
    pathex=["."],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="MacroStudio",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="MacroStudio",
)
