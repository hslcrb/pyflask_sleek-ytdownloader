Unicode true
Target amd64-unicode
SetCompressor /SOLID lzma
Name "Sleek Downloader"
BrandingText "Sleek Downloader"
OutFile "${OUTPUT}"
InstallDir "$LOCALAPPDATA\Programs\SleekDownloader"
RequestExecutionLevel user
ShowInstDetails show

!include "x64.nsh"
!include "MUI2.nsh"
!define MUI_ABORTWARNING
!define MUI_FINISHPAGE_RUN "$INSTDIR\SleekDownloader.exe"
!define MUI_FINISHPAGE_RUN_NOTCHECKED
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "English"
!include "${MANIFEST}"

Function .onInit
    ${IfNot} ${RunningX64}
        MessageBox MB_OK|MB_ICONSTOP "Sleek Downloader requires 64-bit Windows."
        Abort
    ${EndIf}
FunctionEnd

Section "Sleek Downloader"
    SetShellVarContext current
    SetOutPath "$INSTDIR"
    File /r "${PAYLOAD}/*"
    WriteUninstaller "$INSTDIR\Uninstall.exe"
    CreateDirectory "$SMPROGRAMS\Sleek Downloader"
    CreateShortcut "$SMPROGRAMS\Sleek Downloader\Sleek Downloader.lnk" "$INSTDIR\SleekDownloader.exe"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\SleekDownloader" "DisplayName" "Sleek Downloader"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\SleekDownloader" "DisplayVersion" "${VERSION}"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\SleekDownloader" "UninstallString" '"$INSTDIR\Uninstall.exe"'
    WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\SleekDownloader" "NoModify" 1
    WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\SleekDownloader" "NoRepair" 1
SectionEnd

Section "Uninstall"
    SetShellVarContext current
    Delete "$SMPROGRAMS\Sleek Downloader\Sleek Downloader.lnk"
    RMDir "$SMPROGRAMS\Sleek Downloader"
    DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\SleekDownloader"
    !insertmacro RemovePayload
    Delete "$INSTDIR\Uninstall.exe"
    RMDir "$INSTDIR"
SectionEnd
