# Building the Android APK

## Prerequisites

You need a **Linux machine** or **WSL (Windows Subsystem for Linux)** to build Android APKs with Buildozer.

## Installation Steps

### 1. Install Dependencies (Ubuntu/Debian)

```bash
# Update system
sudo apt update
sudo apt upgrade -y

# Install required packages
sudo apt install -y python3-pip git zip unzip openjdk-17-jdk wget
sudo apt install -y autoconf libtool pkg-config zlib1g-dev libncurses5-dev
sudo apt install -y libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev

# Install Cython and Buildozer
pip3 install --upgrade pip
pip3 install --upgrade cython
pip3 install --upgrade buildozer
```

### 2. Install Android SDK/NDK

Buildozer will download these automatically on first build, but you can pre-download:

```bash
# Create directory
mkdir -p ~/.buildozer/android/platform

# Buildozer will handle downloads automatically
```

### 3. Prepare Project

```bash
# Copy parent files
cd android_app
cp ../bybit_client_lite.py .
cp ../twin_range_filter_lite.py .
```

### 4. Build APK

```bash
# Initialize buildozer (first time only)
buildozer init

# Build APK (takes 30-60 minutes first time)
buildozer -v android debug

# Or for release APK (requires keystore)
buildozer -v android release
```

### 5. Get APK

```bash
# APK will be in:
ls bin/
# bybitbot-1.0-arm64-v8a-debug.apk
```

### 6. Install on Phone

Transfer the APK to your phone via:
- USB cable: `adb install bin/bybitbot-1.0-arm64-v8a-debug.apk`
- Cloud storage: Upload to Google Drive, download on phone
- Direct download: Host on GitHub releases

---

## Troubleshooting

### Build Errors

**"Command failed: python -m pythonforandroid.toolchain"**
```bash
buildozer android clean
buildozer -v android debug
```

**"NDK not found"**
```bash
# Buildozer should download automatically
# If not, manually download from:
# https://developer.android.com/ndk/downloads
```

**"Java version issues"**
```bash
sudo update-alternatives --config java
# Select OpenJDK 17
```

### Performance

- First build: 30-60 minutes
- Subsequent builds: 5-10 minutes
- Use `-v` flag for verbose output

---

## Quick Build on Windows

### Option 1: WSL (Recommended)

```bash
# Install WSL
wsl --install

# In WSL terminal:
cd /mnt/d/Documents/Autobot/android_app
# Follow Linux instructions above
```

### Option 2: Cloud Build Service

Use **GitHub Actions** to build automatically:

1. Push code to GitHub
2. Create `.github/workflows/build.yml`:

```yaml
name: Build APK
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: |
          pip install buildozer cython
          sudo apt update
          sudo apt install -y openjdk-17-jdk autoconf libtool
      - name: Build APK
        run: |
          cd android_app
          buildozer -v android debug
      - name: Upload APK
        uses: actions/upload-artifact@v2
        with:
          name: apk
          path: android_app/bin/*.apk
```

3. Download APK from Actions artifacts

---

## Alternative: Online Build Services

### BeeWare Briefcase (Easier)

```bash
pip install briefcase
briefcase create android
briefcase build android
briefcase package android
```

### Kivy Buildozer Docker

```bash
docker pull kivy/buildozer
docker run -v "$(pwd)":/home/user/hostcwd kivy/buildozer android debug
```

---

## App Features

✅ **GUI Controls:**
- API Key & Secret input
- Trading pairs selection (checkboxes)
- Stop Loss % slider
- Take Profit % slider
- Leverage settings per pair
- Timeframe selector
- Start/Stop buttons
- Save configuration

✅ **Background Running:**
- Bot runs in background thread
- Status updates in real-time
- Doesn't block UI

✅ **Configuration:**
- Saves to `bot_config.json`
- Persists between app restarts
- All settings configurable

---

## Testing Before Building

Test the app on desktop first:

```bash
cd android_app
pip install kivy
python main.py
```

This will run the app in a desktop window for testing!

---

## Need Help?

If you encounter issues:
1. Check buildozer logs in `.buildozer/`
2. Run `buildozer android clean`
3. Try building with `-v` for verbose output
4. Check Kivy/Buildozer documentation
