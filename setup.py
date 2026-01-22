"""
py2app build script for Kindle to PDF
Usage: python setup.py py2app
"""

from setuptools import setup

APP = ['kindle_to_pdf_gui.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': False,
    'packages': ['PIL', 'Quartz', 'Foundation'],
    'includes': ['tkinter'],
    'plist': {
        'CFBundleName': 'Kindle to PDF',
        'CFBundleDisplayName': 'Kindle to PDF',
        'CFBundleIdentifier': 'com.kindletopdf.app',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSAppleEventsUsageDescription': 'Kindleアプリを操作するために必要です',
        'NSScreenCaptureUsageDescription': '画面をキャプチャするために必要です',
        'LSMinimumSystemVersion': '10.13',
        'NSHighResolutionCapable': True,
    }
}

setup(
    name='Kindle to PDF',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
