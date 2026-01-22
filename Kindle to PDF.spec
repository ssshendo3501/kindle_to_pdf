# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['kindle_to_pdf_gui.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['PIL._tkinter_finder'],
    hookspath=[],
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
    name='Kindle to PDF',
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
    name='Kindle to PDF',
)
app = BUNDLE(
    coll,
    name='Kindle to PDF.app',
    icon='icon.icns',
    bundle_identifier='com.kindletopdf.app',
    info_plist={
        'CFBundleName': 'Kindle to PDF',
        'CFBundleDisplayName': 'Kindle to PDF',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHighResolutionCapable': True,
        'NSScreenCaptureUsageDescription': '画面をキャプチャしてPDFを作成するために必要です',
        'NSAppleEventsUsageDescription': 'Kindleアプリを操作するために必要です',
    },
)
