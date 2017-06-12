#!/bin/bash

if [ "a$1" = "a" ] ;
	then
	echo "you must specify path to virtualenv"
	exit 1	
else
	venv=$1
fi

${venv}/Scripts/pyinstaller -i img/anam-desktop.ico -n "ANAM Desktop.exe" -y --clean --onefile --windowed --paths /c//Users/reg/envs/anamdesk5/Lib/site-packages/PyQt5/Qt/bin --additional-hooks-dir=. launcher.py

version=`${venv}/Scripts/python -c 'from anamdesktop.utils import get_version; print(get_version())'`
cat installer.nsi |sed "s/{VERSION}/${version}/g" > installer-version.nsi

'/c/Program Files (x86)/NSIS/Bin/makensis.exe' installer-version.nsi
rm installer-version.nsi
