# 📱 Run Trading Bot on Android Phone (No Computer Needed!)

## Quick Start Guide

### Step 1: Install Termux

1. Download **Termux** from F-Droid (NOT Google Play Store)
   - Go to: https://f-droid.org/en/packages/com.termux/
   - Or search "Termux" on F-Droid app
   - Install it

### Step 2: Setup Termux (First Time Only)

Open Termux and run these commands one by one:

```bash
# Update packages
pkg update && pkg upgrade -y

# Install Python and required tools
pkg install python git wget -y

# Install Python packages
pip install requests pandas numpy

# Give storage permission (will ask for permission)
termux-setup-storage
```

### Step 3: Download Bot Files

```bash
# Create directory
mkdir -p ~/trading-bot
cd ~/trading-bot

# Download files from your computer
# Option A: If you have the files on Termux storage
cp /sdcard/Download/*.py ~/trading-bot/

# Option B: Or manually copy the 3 required files:
# - bot_mobile.py
# - bybit_client.py  
# - twin_range_filter.py
```

### Step 4: Create Config File

```bash
# Create config file
cat > mobile_config.json << 'EOF'
{
    "api_key": "f5CoXcOfrUeh8BhJXC",
    "api_secret": "G42bTbSBK9kqZ9phRtvLT5pstU11vkIn2tVk",
    "testnet": false,
    "trading_pairs": ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT"],
    "leverage": {
        "BTCUSDT": 100,
        "ETHUSDT": 100,
        "SOLUSDT": 100,
        "XRPUSDT": 50,
        "DOGEUSDT": 50
    },
    "position_size_percent": 35,
    "timeframe": "5",
    "fast_period": 27,
    "fast_range": 1.6,
    "slow_period": 55,
    "slow_range": 2.0,
    "stop_loss_percent": 50,
    "enable_stop_loss": true,
    "check_interval": 60
}
EOF

# Edit with your API keys
nano mobile_config.json
```

In nano editor:
- Use arrow keys to navigate
- Replace `YOUR_API_KEY_HERE` with your actual keys
- Press `Ctrl+X`, then `Y`, then `Enter` to save

### Step 5: Run the Bot

```bash
cd ~/trading-bot
python bot_mobile.py
```

## 🔄 Keeping Bot Running

### Option 1: Use Termux Wakelock (Recommended)

```bash
# Acquire wakelock (prevents phone from sleeping)
termux-wake-lock

# Run bot
python bot_mobile.py

# When done, release wakelock
termux-wake-unlock
```

### Option 2: Use Screen (Advanced)

```bash
# Install screen
pkg install screen -y

# Start a screen session
screen -S trading-bot

# Run bot
python bot_mobile.py

# Detach from screen: Press Ctrl+A then D
# Bot keeps running in background!

# Reattach to check on it
screen -r trading-bot
```

### Option 3: Run as Service (Most Reliable)

```bash
# Install termux-services
pkg install termux-services -y

# Restart Termux app, then:
mkdir -p ~/.termux/boot
nano ~/.termux/boot/start-trading-bot

# Add this content:
#!/data/data/com.termux/files/usr/bin/bash
termux-wake-lock
cd ~/trading-bot
python bot_mobile.py
```

## 📋 Quick Commands

```bash
# Start bot
cd ~/trading-bot && python bot_mobile.py

# View logs
tail -f bot_mobile.log

# Check if running
ps aux | grep bot_mobile

# Stop bot
# Press Ctrl+C in Termux

# View config
cat mobile_config.json

# Edit config
nano mobile_config.json
```

## 🔋 Battery Optimization

### Disable Battery Optimization for Termux

1. Go to Android Settings
2. Apps → Termux
3. Battery → Unrestricted

### Keep Screen On (Optional)

```bash
# In Termux
termux-wake-lock
```

## 📱 Convenient Widgets

### Create Termux Shortcut

1. Open Termux
2. Run: `mkdir -p ~/.shortcuts`
3. Create script:

```bash
cat > ~/.shortcuts/Start-Bot.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
cd ~/trading-bot
termux-wake-lock
python bot_mobile.py
EOF

chmod +x ~/.shortcuts/Start-Bot.sh
```

4. Long-press home screen → Widgets → Termux → Shortcut
5. Select "Start-Bot"

Now you have a home screen button to start the bot!

## 🔒 Security Tips

1. **Never share your API keys**
2. **Use API key restrictions** on Bybit:
   - IP whitelist (if you have static IP)
   - Enable only "Trade" permission
   - No withdrawals permission
3. **Start with testnet** to test first
4. **Use small position sizes** initially

## 📊 Monitoring

### Check Status While Bot Runs

```bash
# View live logs
tail -f bot_mobile.log

# Search for signals
grep "LONG\|SHORT" bot_mobile.log

# Check errors
grep "ERROR" bot_mobile.log
```

## ⚠️ Troubleshooting

### Bot Stops When Screen Off

```bash
# Use wakelock
termux-wake-lock

# Or use screen/tmux
pkg install screen -y
screen -S bot
python bot_mobile.py
# Press Ctrl+A then D to detach
```

### Connection Issues

```bash
# Check internet
ping -c 3 google.com

# Test DNS
nslookup api.bybit.com

# Reinstall packages
pip install --upgrade requests
```

### Python Errors

```bash
# Reinstall dependencies
pip uninstall pandas numpy requests -y
pip install pandas numpy requests
```

## 📁 File Transfer Methods

### Method 1: USB Cable

1. Connect phone to computer via USB
2. Copy files to phone's Download folder
3. In Termux: `cp /sdcard/Download/*.py ~/trading-bot/`

### Method 2: Termux SSH (Wireless)

```bash
# On phone (Termux)
pkg install openssh -y
passwd  # Set password
whoami  # Note username
ifconfig | grep inet  # Note IP address
sshd  # Start SSH server

# On computer
scp *.py username@phone-ip:~/trading-bot/
```

### Method 3: Cloud Storage

1. Upload files to Google Drive/Dropbox
2. Download in Android browser
3. Copy to Termux storage

## 🎯 Advantages of Mobile Bot

✅ **Runs 24/7** - Phone stays on, bot keeps trading
✅ **Portable** - Monitor and control from anywhere
✅ **Low Power** - Uses minimal battery with optimization
✅ **No Computer Needed** - Completely standalone
✅ **Reliable** - Mobile connections are stable

## 🚀 Pro Tips

1. **Get a cheap dedicated phone** for running the bot
2. **Keep phone charged** (plugged in or power bank)
3. **Use stable WiFi** or unlimited data plan
4. **Enable notifications** for important bot messages
5. **Check logs daily** to monitor performance

---

Your bot is now running entirely on your Android phone! 📱🚀
