# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller spec for SDGW 1914-1919.
# Run from repo root:
#     pyinstaller packaging/sdgw.spec --noconfirm
# Output: dist/SDGW/  (one-folder mode; SDGW.exe + _internal/)
#
# Note: the database file (data/sd_2011.db) is intentionally NOT
# bundled here. Inno Setup places it at install time so the updater
# can replace app-only or db-only deltas without re-downloading the
# other half.

from pathlib import Path
from PyInstaller.utils.hooks import collect_all

REPO_ROOT = Path(SPECPATH).parent

webview_datas, webview_binaries, webview_hidden = collect_all('webview')

a = Analysis(
    [str(REPO_ROOT / 'launcher.py')],
    pathex=[str(REPO_ROOT), str(REPO_ROOT / 'src')],
    binaries=webview_binaries,
    datas=[
        (str(REPO_ROOT / 'src' / 'templates'), 'templates'),
        (str(REPO_ROOT / 'src' / 'static'), 'static'),
    ] + webview_datas,
    hiddenimports=[
        'annotations',
        'clr',
        'clr_loader',
        'pythonnet',
        'webview.platforms.edgechromium',
        'webview.platforms.winforms',
    ] + webview_hidden,
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'pytest',
        'pandas',
        'numpy',
        'matplotlib',
        'IPython',
        'jupyter',
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SDGW',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon=str(REPO_ROOT / 'src' / 'static' / 'SDGW1419.ico'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='SDGW',
)
