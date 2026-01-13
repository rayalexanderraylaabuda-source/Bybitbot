#!/bin/bash

echo "=============================================="
echo "  Building Bybit Trading Bot APK"
echo "=============================================="
echo ""

# Update packages
echo "[1/6] Updating system..."
sudo apt update -qq

# Install dependencies
echo "[2/6] Installing dependencies..."
sudo apt install -y python3-pip openjdk-17-jdk git zip unzip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev

# Install buildozer
echo "[3/6] Installing Buildozer..."
pip3 install --upgrade pip
pip3 install buildozer cython==0.29.36

# Copy project files
echo "[4/6] Preparing project..."
rm -rf ~/bybit-apk-build
mkdir -p ~/bybit-apk-build
cp -r /mnt/d/Documents/Autobot/android_app/* ~/bybit-apk-build/
cd ~/bybit-apk-build

# Build APK
echo "[5/6] Building APK (30-45 minutes)..."
yes | buildozer android debug

# Copy back to Windows
echo "[6/6] Copying APK to Windows..."
mkdir -p /mnt/d/Documents/Autobot/android_app/bin
cp bin/*.apk /mnt/d/Documents/Autobot/android_app/bin/

echo ""
echo "=============================================="
echo "  BUILD COMPLETE!"
echo "=============================================="
echo ""
echo "APK Location: D:\\Documents\\Autobot\\android_app\\bin\\"
ls -lh /mnt/d/Documents/Autobot/android_app/bin/
