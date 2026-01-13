# Trading Bot Setup - Complete Conversation Summary

## 🎯 What We Built

A **Supertrend Trading Bot** for Bybit cryptocurrency derivatives that:
- ✅ Trades automatically based on Supertrend indicator
- ✅ Works on Windows PC and Android phones (no computer needed!)
- ✅ Supports 7 trading pairs: BTC, ETH, SOL, XRP, DOGE, ZEC, FARTCOIN
- ✅ Has web dashboard for remote control
- ✅ Includes ROI-based stop loss and take profit (42% loss / 150% gain)
- ✅ Uses dynamic position sizing (35% of wallet balance)

## 📦 Your GitHub Repository

**Repository URL:** https://github.com/raylaraykapre/Bybit-Auto-Bot

All your code is safely stored here and can be accessed from anywhere!

---

## 🖥️ Desktop Setup (Windows)

### Installation
```bash
cd d:\Documents\Autobot
pip install -r requirements.txt
```

### Run Desktop Bot
```bash
python bot.py
```

### Run Web Dashboard (Access from Phone Browser)
```bash
python web_dashboard.py
# Access at: http://YOUR_IP:5000
```

### Configuration
Edit `config.py`:
```python
BYBIT_API_KEY = "your_key"
BYBIT_API_SECRET = "your_secret"
USE_TESTNET = False  # True for testing, False for live
TRADING_PAIRS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT", "ZECUSDT", "FARTCOINUSDT"]
POSITION_SIZE_PERCENT = 35  # Use 35% of wallet per trade
LEVERAGE = {
    "BTCUSDT": 100,
    "ETHUSDT": 100,
    "SOLUSDT": 100,
    "XRPUSDT": 50,
    "DOGEUSDT": 50,
    "ZECUSDT": 25,
    "FARTCOINUSDT": 25
}
STOP_LOSS_PERCENT = 50  # Close position at 50% loss
TIMEFRAME = "5"  # 5 minute candles
```

---

## 📱 Android Setup (Standalone - No Computer!)

### Step 1: Install Termux
- Download from **F-Droid** (NOT Google Play): https://f-droid.org/packages/com.termux/
- Install the app

### Step 2: Setup Termux
```bash
# Update packages
pkg update && pkg upgrade -y

# Install Python and Git
pkg install python git -y

# Install requests library (only one needed!)
pip install requests

# Give storage access
termux-setup-storage
```

### Step 3: Clone Repository
```bash
git clone https://github.com/raylaraykapre/Bybit-Auto-Bot.git
cd Bybit-Auto-Bot
```

### Step 4: Configure Bot
```bash
# First run creates config file
python bot_mobile_lite.py

# Edit config with your API keys
nano mobile_config.json
```

**Important Config Settings:**
```json
{
    "api_key": "YOUR_BYBIT_API_KEY",
    "api_secret": "YOUR_BYBIT_API_SECRET",
    "testnet": false,
    "trading_pairs": ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT", "ZECUSDT", "FARTCOINUSDT"],
    "leverage": {
        "BTCUSDT": 100,
        "ETHUSDT": 100,
        "SOLUSDT": 100,
        "XRPUSDT": 50,
        "DOGEUSDT": 50,
        "ZECUSDT": 25,
        "FARTCOINUSDT": 25
    },
    "position_size_percent": 35,
    "timeframe": "5",
    "stop_loss_percent": 50,
    "enable_stop_loss": true,
    "check_interval": 60
}
```

In nano editor:
- Arrow keys to move
- `Ctrl+X`, then `Y`, then `Enter` to save

### Step 5: Run Bot
```bash
# Prevent phone from sleeping
termux-wake-lock

# Run bot
python bot_mobile_lite.py
```

### Keep Bot Running 24/7
```bash
# Install screen
pkg install screen -y

# Start screen session
screen -S trading

# Run bot
termux-wake-lock
python bot_mobile_lite.py

# Detach: Press Ctrl+A then D
# Bot keeps running in background!

# Reattach later
screen -r trading
```

---

## 🔑 Getting API Keys

### For Live Trading (Mainnet)
1. Go to: https://www.bybit.com
2. Account → API Management
3. Create API Key
4. Enable: **Derivatives Contract** permission
5. Copy API Key and Secret
6. Set in config: `"testnet": false`

### For Testing (Testnet - Often Has Issues)
1. Go to: https://testnet.bybit.com
2. Same process as above
3. Set in config: `"testnet": true`

**⚠️ Important:** Testnet keys don't work on mainnet and vice versa!

---

## 🎮 Daily Usage Commands

### On Android (Termux)

**Start Bot:**
```bash
cd Bybit-Auto-Bot
termux-wake-lock
python bot_mobile_lite.py
```

**View Logs:**
```bash
tail -f bot.log
```

**Stop Bot:**
```
Press Ctrl+C
```

**Update Bot (when you make changes):**
```bash
cd Bybit-Auto-Bot
git pull
python bot_mobile_lite.py
```

**Check Status (while bot running in screen):**
```bash
screen -r trading
# Press Ctrl+A then D to detach again
```

---

## 🛠️ Troubleshooting

### "ModuleNotFoundError: No module named 'pandas'"
✅ **Fixed!** Use `bot_mobile_lite.py` (not `bot_mobile.py`)
- Only needs `requests` library
- No pandas or numpy required

### "API Error: Invalid API Key"
1. Check testnet/mainnet setting matches your API keys
2. Testnet keys: https://testnet.bybit.com
3. Mainnet keys: https://www.bybit.com
4. Ensure API key has "Derivatives Contract" permission

### "Empty response from API"
- Bybit testnet is unreliable, use mainnet instead
- Change `"testnet": false` in config
- Use mainnet API keys from https://www.bybit.com

### Bot Stops When Screen Off
```bash
# Use wakelock
termux-wake-lock

# Or use screen
screen -S trading
python bot_mobile_lite.py
# Press Ctrl+A then D
```

### Connection Issues
```bash
# Check internet
ping -c 3 google.com

# Reinstall requests
pip uninstall requests -y
pip install requests
```

---

## 📊 Strategy Details

**Supertrend Indicator:**
- Uses ATR (Average True Range) to identify trend direction
- **Long Signal:** Direction changes from bearish to bullish (price crosses above Supertrend line)
- **Short Signal:** Direction changes from bullish to bearish (price crosses below Supertrend line)

**Parameters:**
- ATR Period: 10
- Supertrend Factor: 3.0
- Timeframe: 5 minutes (configurable)

**Risk Management (ROI-Based):**
- Dynamic position sizing: 35% of wallet balance per trade
- Stop Loss: 42% ROI loss (automatically calculated based on leverage)
- Take Profit: 150% ROI gain (automatically calculated based on leverage)
- Leverage: 25-100x depending on coin
- Auto-closes opposite position FIRST before opening new trade

**Example with 100x leverage:**
- 42% ROI loss = 0.42% price move
- 150% ROI gain = 1.5% price move

---

## 📁 Important Files

| File | Purpose |
|------|---------|
| `bot.py` | Desktop bot (needs pandas) |
| `bot_mobile_lite.py` | **Android bot (no pandas needed)** |
| `web_dashboard.py` | Web interface for remote control |
| `bybit_client_lite.py` | Lightweight API client for mobile |
| `supertrend.py` | Supertrend indicator (pandas) |
| `supertrend_lite.py` | Supertrend indicator (no pandas) |
| `config.py` | Desktop configuration |
| `mobile_config.json` | Mobile configuration |

**For Android, always use:** `bot_mobile_lite.py`

---

## ⚙️ Configuration Tips

### Safe Settings for Beginners
```json
{
    "position_size_percent": 20,
    "leverage": {
        "BTCUSDT": 25,
        "ETHUSDT": 25,
        "SOLUSDT": 25,
        "XRPUSDT": 20,
        "DOGEUSDT": 20,
        "ZECUSDT": 15,
        "FARTCOINUSDT": 15
    },
    "stop_loss_percent": 40,
    "timeframe": "15"
}
```

### Aggressive Settings
```json
{
    "position_size_percent": 35,
    "leverage": {
        "BTCUSDT": 100,
        "ETHUSDT": 100,
        "SOLUSDT": 100,
        "XRPUSDT": 50,
        "DOGEUSDT": 50,
        "ZECUSDT": 25,
        "FARTCOINUSDT": 25
    },
    "stop_loss_percent": 50,
    "timeframe": "5"
}
```

---

## 🔒 Security Best Practices

1. ✅ **API Key Restrictions:**
   - Enable only "Derivatives Contract" permission
   - No withdrawal permission
   - Use IP whitelist if possible

2. ✅ **Start Small:**
   - Test with small amounts first
   - Use 10-20% position size initially
   - Lower leverage (10-25x) until confident

3. ✅ **Never Share:**
   - Don't share API keys
   - Don't commit config files to public repos
   - Keep your GitHub repo private

4. ✅ **Monitor Regularly:**
   - Check logs daily: `tail -f bot.log`
   - Review trades on Bybit
   - Adjust settings based on performance

---

## 📈 What Happens When Bot Runs

1. **Every 60 seconds:**
   - Checks for stop loss triggers (closes if position down 50%)
   - Fetches latest price data for all 7 pairs
   - Calculates Twin Range Filter signals
   - Executes trades if signal changes

2. **When LONG signal:**
   - Closes any existing SHORT position
   - Opens LONG position with configured size
   - Logs trade to console and log file

3. **When SHORT signal:**
   - Closes any existing LONG position
   - Opens SHORT position with configured size
   - Logs trade to console and log file

4. **Every 5 minutes:**
   - Prints status summary
   - Shows all positions and unrealized PnL
   - Updates wallet balance

---

## 🚀 Quick Start Checklist

### On Android:
- [ ] Install Termux from F-Droid
- [ ] Run: `pkg install python git -y`
- [ ] Run: `pip install requests`
- [ ] Clone: `git clone https://github.com/raylaraykapre/Bybit-Auto-Bot.git`
- [ ] Get API keys from https://www.bybit.com
- [ ] Edit `mobile_config.json` with your keys
- [ ] Run: `termux-wake-lock`
- [ ] Run: `python bot_mobile_lite.py`
- [ ] Set up screen session for 24/7 running

### Battery Optimization:
- Go to Android Settings → Apps → Termux → Battery → Unrestricted
- Keep phone plugged in or use power bank
- Use WiFi instead of mobile data (more stable)

---

## 💡 Pro Tips

1. **Cheap Dedicated Phone:** Get an old/cheap Android phone just for trading
2. **Stable Internet:** Use reliable WiFi or unlimited data plan
3. **Multiple Timeframes:** Test 5min, 15min, 1hr to find what works
4. **Start Conservative:** Low leverage + small position size first
5. **Keep Logs:** Review `bot.log` to understand performance
6. **Paper Trade First:** If testnet works, test there first
7. **Set Alerts:** Check Termux notifications regularly

---

## 📞 Support & Updates

- **GitHub Repository:** https://github.com/raylaraykapre/Bybit-Auto-Bot
- **Update Bot:** `cd Bybit-Auto-Bot && git pull`
- **Issues:** Open issue on GitHub

---

## ⚠️ Disclaimer

- This bot is for educational purposes
- Cryptocurrency trading involves substantial risk
- You can lose all your capital
- Never invest more than you can afford to lose
- Start with small amounts and test thoroughly
- Monitor the bot regularly, especially initially
- Past performance does not guarantee future results

---

## 📝 Your Current Setup

**Desktop:** Windows PC at `d:\Documents\Autobot`
**GitHub:** https://github.com/raylaraykapre/Bybit-Auto-Bot
**Android:** Using `bot_mobile_lite.py` (pandas-free version)
**Trading Pairs:** 7 pairs (BTC, ETH, SOL, XRP, DOGE, ZEC, FARTCOIN)
**Configuration:** 35% position size, 50% stop loss, 5min timeframe

---

## 🎯 Current Status

✅ Bot created and tested
✅ Uploaded to GitHub
✅ Android version working (pandas-free)
✅ API keys configured
✅ 7 trading pairs integrated
✅ Stop loss enabled
✅ Bot running successfully on your phone

**You're all set! Happy trading! 🚀💰**

---

*Document created: January 12, 2026*
*Last updated: When you integrated XRP, DOGE, ZEC, FARTCOIN*
