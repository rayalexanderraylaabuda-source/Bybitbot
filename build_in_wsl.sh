#!/bin/bash
# Bybit Trading Bot APK Builder Script
# Run this in WSL Ubuntu

echo "==============================================="
echo "  Bybit Trading Bot APK Builder for WSL"
echo "==============================================="
echo ""

# Update system
echo "Step 1: Updating system..."
sudo apt update
sudo apt upgrade -y

# Install dependencies
echo ""
echo "Step 2: Installing build dependencies..."
sudo apt install -y python3-pip git zip unzip openjdk-17-jdk \
    autoconf libtool pkg-config zlib1g-dev libncurses5-dev \
    libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev

# Install Python tools
echo ""
echo "Step 3: Installing Python build tools..."
pip3 install --upgrade pip
pip3 install buildozer cython==0.29.36

# Create build directory
echo ""
echo "Step 4: Preparing build directory..."
mkdir -p ~/bybit-bot-build
cd ~/bybit-bot-build

# Copy files from Windows
echo ""
echo "Step 5: Copying project files..."
cp -r /mnt/d/Documents/Autobot/android_app/* .
cp /mnt/d/Documents/Autobot/bybit_client_lite.py .
cp /mnt/d/Documents/Autobot/twin_range_filter_lite.py .

# Build APK
echo ""
echo "Step 6: Building APK (this takes 30-45 minutes)..."
echo "Please be patient and don't close the terminal!"
echo ""
buildozer -v android debug

# Copy APK back to Windows
echo ""
echo "Step 7: Copying APK to Windows..."
mkdir -p /mnt/d/Documents/Autobot/android_app/bin
cp bin/*.apk /mnt/d/Documents/Autobot/android_app/bin/

echo ""
echo "==============================================="
echo "  BUILD COMPLETE!"
echo "==============================================="
echo ""
echo "Your APK is at:"
echo "D:\\Documents\\Autobot\\android_app\\bin\\"
echo ""
ls -lh /mnt/d/Documents/Autobot/android_app/bin/*.apk
echo ""
echo "Transfer this APK to your Android phone and install it!"
