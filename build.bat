@echo off
chcp 65001 >nul
echo ============================================
echo    KSeF Panel - Budowanie EXE
echo ============================================
echo.

echo [1/4] Instalowanie zależności...
pip install -r requirements.txt
if errorlevel 1 (
    echo BLAD: Nie udalo sie zainstalowac zaleznosci!
    pause
    exit /b 1
)

echo.
echo [2/4] Budowanie pliku EXE...
pyinstaller main.py ^
    --onefile ^
    --noconsole ^
    --name KSeFPanel ^
    --add-data "app\templates;app\templates" ^
    --add-data "app\static;app\static" ^
    --hidden-import=win32api ^
    --hidden-import=win32print ^
    --clean ^
    -y

if errorlevel 1 (
    echo BLAD: Budowanie nie powiodlo sie!
    pause
    exit /b 1
)

echo.
echo [3/4] Tworzenie folderu dystrybucyjnego...
if not exist "KSeFPanel_Setup" mkdir KSeFPanel_Setup
copy /Y dist\KSeFPanel.exe KSeFPanel_Setup\KSeFPanel.exe
copy /Y INSTALUJ.bat KSeFPanel_Setup\INSTALUJ.bat
copy /Y README_INSTALACJA.txt KSeFPanel_Setup\README_INSTALACJA.txt

echo {"ksef_token": "", "nip": "", "environment": "prod", "default_printer": "", "auto_fetch_on_start": true} > KSeFPanel_Setup\config.json

echo.
echo [4/4] Gotowe!
echo ============================================
echo  Folder KSeFPanel_Setup jest gotowy.
echo  Skopiuj go na pendrive i uruchom
echo  INSTALUJ.bat na docelowym komputerze.
echo ============================================
echo.
pause
