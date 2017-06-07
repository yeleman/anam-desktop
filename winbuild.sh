#!/bin/bash

if [ "a$1" = "a" ] ;
	then
	echo "you must specify path to virtualenv"
	exit 1	
else
	venv=$1
fi

${venv}/Scripts/pyinstaller -i img/anam-desktop.ico -n "ANAM Desktop.exe" -y --clean --onefile --windowed --paths /c//Users/reg/envs/anamdesk5/Lib/site-packages/PyQt5/Qt/bin --additional-hooks-dir=. launcher.py

'/c/Program Files (x86)/NSIS/Bin/makensis.exe' 'ANAM Desktop Installer.nsi'
