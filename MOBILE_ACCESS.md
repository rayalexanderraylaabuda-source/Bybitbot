# Access Trading Bot from Android Phone

## Quick Start

### 1. Start the Dashboard on Your Computer

Double-click `START_DASHBOARD.bat` or run:
```bash
py web_dashboard.py
```

### 2. Find Your Computer's IP Address

**On Windows:**
1. Press `Windows + R`
2. Type `cmd` and press Enter
3. Type `ipconfig` and press Enter
4. Look for "IPv4 Address" (example: 192.168.1.100)

### 3. Connect from Your Android Phone

1. Make sure your phone is on the **same WiFi network** as your computer
2. Open any browser (Chrome, Firefox, etc.)
3. Type in the address bar: `http://YOUR_IP:5000`
   - Example: `http://192.168.1.100:5000`
4. Bookmark the page for easy access!

## Features

✅ **Start/Stop Bot** - Control your trading bot from anywhere
✅ **Real-time Status** - See positions, PnL, and wallet balance
✅ **Close Positions** - Emergency close all positions with one tap
✅ **Mobile Optimized** - Designed to work perfectly on phone screens
✅ **Auto-refresh** - Updates every 5 seconds automatically

## Troubleshooting

### Can't Connect from Phone?

1. **Check WiFi**: Phone and computer must be on same network
2. **Check Firewall**: Windows Firewall might block port 5000
   - Go to Windows Defender Firewall
   - Allow Python through firewall
3. **Verify IP**: Make sure you're using the correct IP address

### Allow Through Firewall

Run this in Administrator Command Prompt:
```cmd
netsh advfirewall firewall add rule name="Trading Bot Dashboard" dir=in action=allow protocol=TCP localport=5000
```

## Security Notes

⚠️ This dashboard is accessible to anyone on your local network
⚠️ Do not expose this to the internet without proper security
⚠️ Only use on trusted WiFi networks

## Optional: Access from Outside Your Home

If you want to access from anywhere (not just home WiFi):

1. Use a VPN solution like:
   - Tailscale (easiest)
   - WireGuard
   - ZeroTier

2. Or use a reverse proxy service (advanced)

## Making it More Convenient

### Add to Android Home Screen

1. Open the dashboard in Chrome
2. Tap the menu (⋮)
3. Tap "Add to Home screen"
4. Now you have an app icon!

### Keep Computer Awake

Go to Windows Settings:
- System → Power & sleep
- Set "When plugged in, PC goes to sleep after" to "Never"

This ensures your bot keeps running!
