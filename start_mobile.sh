#!/data/data/com.termux/files/usr/bin/bash
# Termux startup script for trading bot

echo "================================"
echo "  Mobile Trading Bot Launcher"
echo "================================"
echo ""

# Navigate to bot directory
cd ~/trading-bot || { echo "Error: Bot directory not found"; exit 1; }

# Check if Python is installed
if ! command -v python &> /dev/null; then
    echo "Installing Python..."
    pkg install python -y
fi

# Check if required packages are installed
if ! python -c "import requests" &> /dev/null; then
    echo "Installing required packages..."
    pip install requests pandas numpy
fi

# Check if config exists
if [ ! -f "mobile_config.json" ]; then
    echo "Error: mobile_config.json not found!"
    echo "Please create config file first."
    exit 1
fi

# Acquire wakelock to prevent sleep
termux-wake-lock

echo "Starting bot..."
echo "Press Ctrl+C to stop"
echo ""

# Run the bot
python bot_mobile.py

# Release wakelock on exit
termux-wake-unlock
