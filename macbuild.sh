#!/bin/sh

pyinstaller --clean -y --onefile --windowed -i img/anam-desktop.icns --osx-bundle-identifier com.yeleman.anam-desktop --name "ANAM Desktop" --additional-hooks-dir=. launcher.py
