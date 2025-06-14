# LOOP - Little Optical Output Pal 🤖

Your pocket-sized animation companion! LOOP is a Wi-Fi enabled display that brings your GIFs and videos to life on a tiny screen. Perfect for desk companions, status displays, or just sharing moments of joy!

![LOOP](https://img.shields.io/badge/Platform-Raspberry%20Pi-red) ![Python](https://img.shields.io/badge/Python-3.9+-blue) ![License](https://img.shields.io/badge/License-MIT-green)

## ✨ What Can LOOP Do?

### 🎬 Show Your Media

- Plays GIFs, videos (MP4, AVI, MOV), images (PNG, JPG)
- Optimized for crisp display on 240×320 ILI9341 screen
- Smooth playback with hardware acceleration
- Physical controls via optional rotary encoder

### 🌐 Easy Control

- Modern web interface with drag & drop uploads
- Control playback from any device
- Browse your media library with thumbnails
- Monitor system status in real-time

### 📡 Smart Connection

- Auto-connects to your WiFi
- Sets up its own "LOOP-Setup" network when needed
- Visual WiFi network browser
- Never gets stuck - always accessible!

## 🔌 Hardware Setup

### What You'll Need

- **Raspberry Pi Zero 2 W** (LOOP's brain!)
- **Waveshare 2.4" LCD** (LOOP's face!)
- **MicroSD card** (8GB+, Class 10)
- **5V USB power** (LOOP gets hungry!)
- **Optional**: Rotary encoder (for physical controls)

### Wiring Guide

Connect your display:

```
LCD Pin  → Pi Pin (BCM)  → Pi Pin (Physical)
VCC      → 3.3V          → Pin 1
GND      → GND           → Pin 6
DIN      → GPIO 10       → Pin 19 (MOSI)
CLK      → GPIO 11       → Pin 23 (SCLK)
CS       → GPIO 8        → Pin 24 (CE0)
DC       → GPIO 25       → Pin 22
RST      → GPIO 27       → Pin 13
BL       → GPIO 18       → Pin 12
```

Optional rotary encoder:

```
Encoder   → Pi Pin (BCM)
Pin A     → GPIO 2
Pin B     → GPIO 3
Button    → GPIO 4
```

## 🚀 Installation

### 1. Prepare Pi

Flash Raspberry Pi OS Lite (32-bit) and enable SSH.

### 2. Install LOOP

```bash
git clone https://github.com/yourusername/loop.git
cd loop
./deployment/scripts/install.sh
```

That's it! LOOP will show you its IP address when ready (e.g., http://192.168.1.100:8080)

### 3. First Time Setup

1. **Connect to WiFi**:

   - Look for "LOOP-Setup" network (password: loop123)
   - Open any website to configure WiFi

2. **Upload Media**:
   - Visit LOOP's web interface
   - Drop your favorite GIFs and videos
   - Watch LOOP bring them to life!

### 4. Updates

Keeping LOOP fresh is super simple:

```bash
cd /home/pi/loop
git pull
sudo systemctl restart loop
```

## 🎮 Controls

### Web Interface

- **Upload**: Drag & drop anywhere
- **Play/Pause**: Space bar
- **Next/Previous**: Arrow keys
- **Settings**: Configure everything!

### Physical Controls (if encoder connected)

- **Turn Right**: Next animation
- **Turn Left**: Previous animation
- **Press**: Play/Pause

## 🔧 Troubleshooting

### Display Issues?

```bash
# Test LOOP's screen
source venv/bin/activate
python -c "from display.spiout import ILI9341Driver; from config.schema import get_config; d = ILI9341Driver(get_config().display); d.init(); d.fill_screen(0xF800)"
```

### Service Problems?

```bash
sudo systemctl status loop     # Check on LOOP
sudo journalctl -u loop -f     # See what's up
sudo systemctl restart loop    # Give LOOP a restart
```

### WiFi Troubles?

```bash
sudo systemctl restart wpa_supplicant  # Reset WiFi
loop-hotspot start                     # Start hotspot
```

## 🤝 Want to Help?

LOOP loves new friends! Here's how to contribute:

1. **Fork** LOOP's home
2. **Create** a feature branch
3. **Make** your changes
4. **Test** everything works
5. **Send** a Pull Request

## 📄 License

LOOP is free to share! See [LICENSE](LICENSE) for details.

## 🙏 Thanks

- **Waveshare** for the amazing display
- **FastAPI** for the speedy web server
- **Raspberry Pi** for the perfect brain
- **Contributors** for making LOOP better

---

Made with 💝 by your friends at LOOP  
_"Your pocket-sized animation companion!"_
