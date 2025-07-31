# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['cli\\cli.py'],
    pathex=[],
    binaries=[('C:\\Users\\zachy\\AppData\\Local\\Programs\\Python\\Python311\\Lib\\site-packages\\keystone', 'keystone'), ('C:\\Users\\zachy\\Work\\Game Modding\\My Modding Tools\\Gameguardian All Updates Scipt Generator\\venv\\Lib\\site-packages\\capstone', 'capstone')],
    datas=[('resources/minified_script_template.lua', 'resources'), ('resources/script_template.lua', 'resources')],
    hiddenimports=[],
    hookspath=['../pyinstaller hooks'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='all_updates_generator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
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
    name='all_updates_generator',
)
