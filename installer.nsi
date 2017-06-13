
SetCompressor /FINAL zlib

Name "ANAM Desktop Installer"
OutFile "ANAM Desktop Installer-{VERSION}.exe"
;InstallDir "$PROGRAMFILES64\ANAM Desktop"	
InstallDir "C:\ANAM Desktop"	
; Request application privileges for Windows Vista
RequestExecutionLevel user ; admin

;--------------------------------
Page directory
Page instfiles
UninstPage uninstConfirm
UninstPage instfiles
;--------------------------------

Function .onInit
  Var /GLOBAL exename
  StrCpy $exename "ANAM Desktop.exe"
FunctionEnd


Section "" ;No components page, name is not important
  SetOutPath "$INSTDIR"
  
  File /oname=$exename "dist\ANAM Desktop.exe"
  File "anam-desktop.settings"
  File "Aide ANAM Desktop.pdf"

  CreateDirectory "$INSTDIR\img"
  File /oname=img\anam-desktop.png img\anam-desktop.png
  File /oname=img\anam-desktop.ico img\anam-desktop.ico

  File /oname=vc_redist.x64-2015.exe extras\VCruntime\vc_redist.x64-2015.exe
  File /r "oraclient_win64"

  WriteUninstaller $INSTDIR\uninstaller.exe

  CreateDirectory "$SMPROGRAMS\ANAM Desktop"
  CreateShortcut "$SMPROGRAMS\ANAM Desktop\ANAM Desktop.lnk" "$INSTDIR\ANAM Desktop.exe" "" "$INSTDIR\img\anam-desktop.ico"
  CreateShortcut "$SMPROGRAMS\ANAM Desktop\Uninstall.lnk" "$INSTDIR\uninstaller.exe"

  ; install VisualC++ runtime 2015 (v14)
  ExecWait '"$INSTDIR\vc_redist.x64-2015.exe" /q:a /c:"VCREDI~2.EXE /q:a /c:""msiexec /i vcredist.msi /qb' $0
  
SectionEnd

Section "Uninstall"
  Delete $INSTDIR\uninstaller.exe
  Delete "$INSTDIR\ANAM Desktop.exe"
  Delete $INSTDIR\anam-desk.settings
  RMDir /r $INSTDIR\img
  Delete "$INSTDIR\vc_redist.x64-2015.exe"
  RMDir /r $INSTDIR\oraclient_win64
  Delete $INSTDIR\anam-desktop.log
  Delete $INSTDIR\erreurs-copie.log
  Delete "Aide ANAM Desktop.pdf"
  RMDir $INSTDIR

  Delete "$SMPROGRAMS\ANAM Desktop\ANAM Desktop.lnk"
  Delete "$SMPROGRAMS\ANAM Desktop\Uninstall.lnk"
  RMDir "$SMPROGRAMS\ANAM Desktop"
SectionEnd
