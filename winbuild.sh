#!/bin/bash

# we must have the virtualenv path as parameter
if [ "a$1" = "a" ] ;
	then
	echo "you must specify path to virtualenv"
	exit 1	
else
	venv=$1
fi

# build output exe file
${venv}/Scripts/pyinstaller -i img/anam-desktop.ico -n "ANAM Desktop.exe" -y --clean --onefile --windowed --paths /c//Users/reg/envs/anamdesk5/Lib/site-packages/PyQt5/Qt/bin --additional-hooks-dir=. launcher.py

# guess version number (string)
version=`${venv}/Scripts/python -c 'from anamdesktop.utils import get_version; print(get_version())'`

# create a copy of installer script with version number inside (output installer file)
cat installer.nsi |sed "s/{VERSION}/${version}/g" > installer-version.nsi

# move out settings so installer gets a clean one
mv anam-desktop.settings anam-desktop.settings.old
echo "{}" > anam-desktop.settings

# build the installer
'/c/Program Files (x86)/NSIS/Bin/makensis.exe' installer-version.nsi

# restore settings file
mv anam-desktop.settings.old anam-desktop.settings

# remove temp installer script with version inside
rm installer-version.nsi
