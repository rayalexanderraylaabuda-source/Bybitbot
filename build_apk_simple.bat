@echo off
echo ================================================
echo    Bybit Trading Bot APK Builder
echo    Building APK with full GUI controls
echo ================================================
echo.
echo This will build an APK with:
echo   - API Key/Secret input fields
echo   - Stop Loss ROI %% adjustment
echo   - Take Profit ROI %% adjustment  
echo   - Coin pair selection checkboxes
echo   - Start/Stop bot buttons
echo.
echo Estimated time: 30-45 minutes
echo.
pause

echo.
echo [1/5] Installing build tools in WSL...
wsl bash -c "sudo apt update -qq && sudo apt install -y python3-pip openjdk-17-jdk 2>&1 | grep -v 'already'"

echo.
echo [2/5] Installing Python packages...
wsl bash -c "pip3 install -q buildozer cython==0.29.36"

echo.
echo [3/5] Preparing project files...
wsl bash -c "rm -rf ~/bybit-apk-build && mkdir -p ~/bybit-apk-build"
wsl bash -c "cp -r '/mnt/d/Documents/Autobot/android_app'/* ~/bybit-apk-build/"

echo.
echo [4/5] Building APK (30-45 minutes - DO NOT CLOSE!)...
echo Started at: %TIME%
wsl bash -c "cd ~/bybit-apk-build && yes | buildozer android debug 2>&1 | tee build.log"

echo.
echo [5/5] Copying APK to Windows...
if not exist "android_app\bin" mkdir android_app\bin
wsl bash -c "cp ~/bybit-apk-build/bin/*.apk '/mnt/d/Documents/Autobot/android_app/bin/'"

echo.
echo ================================================
echo    BUILD COMPLETE!
echo ================================================
echo.
echo Completed at: %TIME%
echo.
echo Your APK is at:
echo D:\Documents\Autobot\android_app\bin\
echo.
dir android_app\bin\*.apk
echo.
echo Transfer this file to your Android phone and install it!
echo.
pause
