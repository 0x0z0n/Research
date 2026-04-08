# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['evtx_tool.py'],
    pathex=[],
    binaries=[],
    datas=[('evtx_tool/profiles/defaults/*.json', 'evtx_tool/profiles/defaults'), ('evtx_tool/data/mappings.json', 'evtx_tool/data'), ('evtx_tool/resources/images/eventhunt_logo.png', 'evtx_tool/resources/images')],
    hiddenimports=['sentinel'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PySide2', 'PySide6', 'PyQt6'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='eventhunt',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
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
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='eventhunt',
)
