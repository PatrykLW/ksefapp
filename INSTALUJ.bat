@echo off
chcp 65001 >nul
echo ============================================
echo    KSeF Panel - Instalacja
echo ============================================
echo.

set "INSTALL_DIR=C:\KSeFPanel"
set "EXE_NAME=KSeFPanel.exe"
set "SHORTCUT_NAME=KSeF Panel"

echo Instalacja do: %INSTALL_DIR%
echo.

:: Tworzenie folderu instalacji
if not exist "%INSTALL_DIR%" (
    mkdir "%INSTALL_DIR%"
    echo [OK] Utworzono folder %INSTALL_DIR%
) else (
    echo [OK] Folder %INSTALL_DIR% juz istnieje
)

:: Kopiowanie EXE
if exist "%~dp0%EXE_NAME%" (
    copy /Y "%~dp0%EXE_NAME%" "%INSTALL_DIR%\%EXE_NAME%"
    echo [OK] Skopiowano %EXE_NAME%
) else (
    echo [BLAD] Nie znaleziono %EXE_NAME% w folderze instalatora!
    echo Upewnij sie, ze %EXE_NAME% jest obok tego pliku.
    pause
    exit /b 1
)

:: Kopiowanie config.json
if exist "%~dp0config.json" (
    if not exist "%INSTALL_DIR%\config.json" (
        copy /Y "%~dp0config.json" "%INSTALL_DIR%\config.json"
        echo [OK] Skopiowano config.json
    ) else (
        echo [INFO] config.json juz istnieje - nie nadpisano (Twoje ustawienia sa bezpieczne)
    )
)

:: Wykrywanie sciezki do pulpitu (obsluga OneDrive, polskich Windows itd.)
echo [..] Szukanie pulpitu...
set "DESKTOP="

:: Metoda 1: Registry (najdokladniejsza)
for /f "tokens=2*" %%a in ('reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders" /v Desktop 2^>nul') do set "DESKTOP=%%b"
:: Zamiana %USERPROFILE% na wartosc
if defined DESKTOP call set "DESKTOP=%DESKTOP%"

:: Metoda 2: Fallback - sprawdz popularne lokalizacje
if not exist "%DESKTOP%" (
    if exist "%USERPROFILE%\OneDrive\Pulpit" set "DESKTOP=%USERPROFILE%\OneDrive\Pulpit"
)
if not exist "%DESKTOP%" (
    if exist "%USERPROFILE%\OneDrive\Desktop" set "DESKTOP=%USERPROFILE%\OneDrive\Desktop"
)
if not exist "%DESKTOP%" (
    if exist "%USERPROFILE%\Pulpit" set "DESKTOP=%USERPROFILE%\Pulpit"
)
if not exist "%DESKTOP%" (
    set "DESKTOP=%USERPROFILE%\Desktop"
)

echo     Pulpit: %DESKTOP%

:: Tworzenie skrotu na pulpicie
set "SCRIPT=%TEMP%\create_shortcut.vbs"

echo Set oWS = WScript.CreateObject("WScript.Shell") > "%SCRIPT%"
echo sLinkFile = "%DESKTOP%\%SHORTCUT_NAME%.lnk" >> "%SCRIPT%"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%SCRIPT%"
echo oLink.TargetPath = "%INSTALL_DIR%\%EXE_NAME%" >> "%SCRIPT%"
echo oLink.WorkingDirectory = "%INSTALL_DIR%" >> "%SCRIPT%"
echo oLink.Description = "KSeF Panel - Zarzadzanie fakturami" >> "%SCRIPT%"
echo oLink.Save >> "%SCRIPT%"

cscript //nologo "%SCRIPT%"
if errorlevel 1 (
    echo [UWAGA] Nie udalo sie utworzyc skrotu automatycznie.
    echo         Utworz skrot recznie: prawy klik na %INSTALL_DIR%\%EXE_NAME% -^> Wyslij do -^> Pulpit
) else (
    del "%SCRIPT%" 2>nul
    echo [OK] Skrot "%SHORTCUT_NAME%" utworzony na pulpicie
)

echo.
echo ============================================
echo    INSTALACJA ZAKONCZONA!
echo ============================================
echo.
echo  Folder: %INSTALL_DIR%
echo  Skrot: %DESKTOP%\%SHORTCUT_NAME%.lnk
echo.
echo  Aby zmienic token KSeF:
echo  - Otworz aplikacje i przejdz do Ustawien
echo  - LUB edytuj %INSTALL_DIR%\config.json
echo.
echo ============================================
pause
