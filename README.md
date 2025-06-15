# LOOP - Little Optical Output Pal

Your pocket-sized animation companion! LOOP is a Wi-Fi enabled display that brings your GIFs and videos to life on a tiny screen. Perfect for desk companions, status displays, or just sharing moments of joy!

![LOOP](https://img.shields.io/badge/Platform-Raspberry%20Pi-red) ![Python](https://img.shields.io/badge/Python-3.9+-blue) ![License](https://img.shields.io/badge/License-MIT-green)

## What Can LOOP Do?

### Show Your Media

- Plays GIFs, videos (MP4, AVI, MOV), and images (PNG, JPG)
- Optimized for 240×320 ILI9341 SPI displays
- Smooth playback with efficient frame conversion
- Web-based controls from any device

### Easy Control

- Modern web interface with drag & drop uploads
- Control playback from any device on your network
- Browse your media library with thumbnails
- Real-time status monitoring

### Smart Connection

- Auto-connects to your WiFi
- Sets up its own "LOOP-Setup" network when needed
- Web-based WiFi configuration
- Accessible via web browser

## Hardware Setup

### What You'll Need

- **Raspberry Pi Zero 2 W** or **Raspberry Pi 4** (LOOP's brain!)
- **Waveshare 2.4" ILI9341 LCD** (LOOP's face!)
- **MicroSD card** (8GB+, Class 10)
- **5V USB power** (LOOP gets hungry!)

### Wiring Guide

Connect your display to your Raspberry Pi:

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

## Installation

### 1. Prepare Pi

Flash Raspberry Pi OS Lite (32-bit) and enable SSH.

### 2. Install LOOP

```bash
git clone https://github.com/yourusername/loop.git
cd loop
# Install system dependencies first
sudo apt-get update
sudo apt-get install -y python3-opencv
# Then run the installer
./deployment/scripts/install.sh
```

The installer will set up everything needed and show you the IP address when ready.

### 3. First Time Setup

1. **Connect to WiFi**:

   - Look for "LOOP-Setup" network (password: loop123)
   - Open any website and configure WiFi via the web interface

2. **Upload Media**:
   - Visit LOOP's web interface
   - Drag and drop your GIFs, videos, and images
   - Watch LOOP bring them to life!

### 4. Updates

Keep LOOP up to date:

```bash
cd /home/pi/loop
git pull
sudo systemctl restart loop
```

## Controls

### Web Interface

- **Upload**: Drag & drop files anywhere on the page
- **Play/Pause**: Space bar or click the play button
- **Next/Previous**: Arrow keys or navigation buttons
- **Activate Media**: Click on any media item to play it

## Troubleshooting

### Display Issues?

```bash
# Test LOOP's screen
source venv/bin/activate
python -c "from display.spiout import ILI9341Driver; from config.schema import get_config; d = ILI9341Driver(get_config().display); d.init(); d.fill_screen(0xF800)"
```

### Service Problems?

```bash
sudo systemctl status loop     # Check LOOP status
sudo journalctl -u loop -f     # View logs
sudo systemctl restart loop    # Restart LOOP
```

### WiFi Troubles?

```bash
sudo systemctl restart wpa_supplicant  # Reset WiFi
loop-hotspot start                     # Start hotspot mode
```

## Current Limitations

- Physical controls (rotary encoder) are not yet implemented
- Only supports basic media formats (expanding over time)
- Performance depends on Pi model and media complexity
- No advanced video effects or filters

## Planned Features

- Physical rotary encoder controls
- More media format support
- Playlist management
- Scheduling and automation
- Mobile app companion

## Want to Help?

LOOP loves new contributors! Here's how to get involved:

1. **Fork** the repository
2. **Create** a feature branch
3. **Make** your changes
4. **Test** thoroughly
5. **Submit** a Pull Request

Check the issues page for tasks that need attention!

## License

LOOP is open source! See [LICENSE](LICENSE) for details.

## Thanks

- **Waveshare** for the excellent displays
- **FastAPI** for the speedy web framework
- **Raspberry Pi Foundation** for amazing hardware
- **Contributors** for making LOOP better

---

Made with love by the LOOP community  
_"Your pocket-sized animation companion!"_
