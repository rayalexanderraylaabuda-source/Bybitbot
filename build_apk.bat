@echo off
echo ===============================================
echo   Bybit Trading Bot APK Builder
echo ===============================================
echo.

REM Check if WSL is installed
wsl --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: WSL is not installed!
    echo.
    echo Installing WSL... This will require a restart.
    echo.
    wsl --install -d Ubuntu
    echo.
    echo WSL installation started!
    echo After your PC restarts:
    echo 1. Open Ubuntu from Start Menu
    echo 2. Set up username and password
    echo 3. Run this script again: build_apk.bat
    echo.
    pause
    exit /b
)

echo Step 1: Checking WSL installation...
wsl --list --verbose

echo.
echo Step 2: Updating WSL and installing dependencies...
wsl -e bash -c "sudo apt update && sudo apt upgrade -y"
wsl -e bash -c "sudo apt install -y python3-pip git zip unzip openjdk-17-jdk"
wsl -e bash -c "sudo apt install -y autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev"

echo.
echo Step 3: Installing Python build tools...
wsl -e bash -c "pip3 install --upgrade pip"
wsl -e bash -c "pip3 install buildozer cython==0.29.36"

echo.
echo Step 4: Copying files to WSL...
wsl -e bash -c "mkdir -p /home/%USERNAME%/bybit-bot"
wsl -e bash -c "cp -r /mnt/d/Documents/Autobot/android_app/* /home/%USERNAME%/bybit-bot/"

echo.
echo Step 5: Building APK (this will take 30-45 minutes)...
echo Please wait... Do not close this window!
wsl -e bash -c "cd /home/%USERNAME%/bybit-bot && buildozer -v android debug"

echo.
echo Step 6: Copying APK back to Windows...
if not exist "bin" mkdir bin
wsl -e bash -c "cp /home/%USERNAME%/bybit-bot/bin/*.apk /mnt/d/Documents/Autobot/android_app/bin/"

echo.
echo ===============================================
echo   BUILD COMPLETE!
echo ===============================================
echo.
echo Your APK is ready at:
echo D:\Documents\Autobot\android_app\bin\
echo.
dir bin\*.apk
echo.
pause
