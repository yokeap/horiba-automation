# build.bat
# Script สำหรับ build exe ให้ใช้งานง่าย

@echo off
echo ========================================
echo Horiba Automation System - Build Script
echo ========================================
echo.

REM ตรวจสอบว่าติดตั้ง PyInstaller แล้วหรือยัง
python -m pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    python -m pip install pyinstaller
)

REM ล้าง build และ dist folders เก่า
echo Cleaning old build files...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo.
echo ========================================
echo Building EXE...
echo ========================================
echo.

REM วิธีที่ 1: ใช้ spec file (แนะนำ)
if exist horiba_automation.spec (
    echo Using spec file...
    python -m PyInstaller horiba_automation.spec
) else (
    echo Spec file not found, using command line...
    
    REM หา AutoItX3 DLL path
    for /f "delims=" %%i in ('python -c "import autoit, os; print(os.path.dirname(autoit.__file__))"') do set AUTOIT_PATH=%%i
    
    REM Build ด้วย PyInstaller command line
    python -m PyInstaller main.py ^
        --onefile ^
        --windowed ^
        --name=HoribaAutomation ^
        --add-data "%AUTOIT_PATH%\lib\AutoItX3_x64.dll;autoit\lib" ^
        --add-data ".\imgdata;.\imgdata" ^
        --hidden-import=PyQt6.QtCore ^
        --hidden-import=PyQt6.QtGui ^
        --hidden-import=PyQt6.QtWidgets ^
        --hidden-import=PyQt6.QtSerialPort ^
        --hidden-import=cv2 ^
        --hidden-import=numpy ^
        --hidden-import=PIL ^
        --hidden-import=pyautogui ^
        --hidden-import=autoit ^
        --hidden-import=serial ^
        --exclude-module=matplotlib ^
        --exclude-module=scipy ^
        --exclude-module=pandas ^
        --icon=icon.ico
)

echo.
if exist dist\HoribaAutomation.exe (
    echo ========================================
    echo Build completed successfully!
    echo ========================================
    echo.
    echo EXE location: dist\HoribaAutomation.exe
    echo File size:
    dir dist\HoribaAutomation.exe | find "HoribaAutomation.exe"
    echo.
    echo You can now:
    echo 1. Test the EXE: dist\HoribaAutomation.exe
    echo 2. Create installer with Inno Setup
    echo.
) else (
    echo ========================================
    echo Build FAILED!
    echo ========================================
    echo Please check the errors above.
    echo.
)

pause
