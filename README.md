# 🎬 VidBox - GIF Player & Uploader Appliance

A standalone, Wi-Fi-enabled device that displays uploaded GIFs and videos on a small SPI screen. Built for Raspberry Pi with a beautiful web interface for media management and system configuration.

![VidBox](https://img.shields.io/badge/Platform-Raspberry%20Pi-red) ![Python](https://img.shields.io/badge/Python-3.9+-blue) ![License](https://img.shields.io/badge/License-MIT-green)

## ✨ Features

### 🎞️ Media Playback

- **Multi-format support**: GIFs, MP4, AVI, MOV, PNG, JPG
- **Hardware-optimized display**: 240×320 ILI9341 SPI screen support
- **Smooth playback**: Frame-accurate timing with RGB565 optimization
- **Physical controls**: Optional rotary encoder for navigation

### 🌐 Web Interface

- **Modern UI**: Responsive design with drag & drop uploads
- **Real-time controls**: Play, pause, skip media from browser
- **Media library**: Grid view with metadata and thumbnails
- **Live status**: WiFi connection, playback state, system info
- **Mobile-friendly**: Works great on phones and tablets

### 📡 Network Management

- **Auto-configuration**: Connects to saved WiFi or starts hotspot
- **Captive portal**: Easy setup via "VidBox-Setup" network
- **Network scanning**: Visual WiFi network browser
- **Hotspot fallback**: Never get locked out of your device

### 🔄 Smart Updates

- **Multiple update methods**: GitHub Actions, git pull, OTA updates
- **Automatic deployment**: Push to main branch = instant deployment
- **Backup & rollback**: Safe updates with automatic backups
- **Web-based updates**: Check and install updates via browser

### 🔧 System Management

- **Hardware monitoring**: Display status, WiFi signal, system health
- **Configuration management**: JSON-based settings with validation
- **Logging & debugging**: Comprehensive logging with rotation
- **Service integration**: systemd service for reliable operation

## 🔌 Hardware Requirements

### Required Components

- **Raspberry Pi Zero 2 W** (or any Pi with GPIO)
- **Waveshare 2.4" LCD** (ILI9341 controller, 240×320)
- **MicroSD card** (8GB+, Class 10 recommended)
- **5V USB power supply** (2A recommended)

### Optional Components

- **Rotary encoder** with push button (for physical controls)
- **Case/enclosure** (3D printable designs available)

### Wiring Diagram

Connect your Waveshare 2.4" LCD to the Raspberry Pi:

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

**Optional Rotary Encoder:**

```
Encoder Pin → Pi Pin (BCM)
Pin A       → GPIO 2
Pin B       → GPIO 3
Button      → GPIO 4
```

## 🚀 Quick Start

### 1. Prepare Your Pi

Flash **Raspberry Pi OS Lite (32-bit)** to your SD card and enable SSH.

### 2. Install VidBox

```bash
# SSH into your Pi
ssh pi@your-pi-ip

# Clone and install
git clone https://github.com/yourusername/vidbox.git
cd vidbox
chmod +x deployment/scripts/install.sh
sudo ./deployment/scripts/install.sh
```

The installer will:

- Install system dependencies (Python, ffmpeg, hostapd, etc.)
- Set up Python virtual environment
- Configure SPI interface
- Create systemd service
- Start VidBox automatically

### 3. First Setup

1. **Connect to WiFi**:

   - If no WiFi configured, connects to hotspot "VidBox-Setup" (password: vidbox123)
   - Open any website to configure your WiFi

2. **Access Web Interface**:

   ```
   http://your-pi-ip:8080
   ```

3. **Upload Media**:
   - Drag & drop GIFs, videos, or images
   - Watch them appear on your display!

## 🖥️ Web Interface Guide

### Home Page

- **System Status**: WiFi connection, current playback, frame counter
- **Playback Controls**: Play, pause, next/previous media
- **Upload Area**: Drag & drop or click to upload files
- **Media Library**: Grid view of all uploaded media

### Settings Page

- **WiFi Configuration**: Scan networks, connect, manage hotspot
- **System Updates**: Check for and install updates
- **Device Information**: Version, platform, display info
- **Advanced Settings**: Service restart, factory reset

### Keyboard Shortcuts

- **Space**: Toggle pause/play
- **← →**: Navigate between media
- **Upload**: Drag files anywhere on the page

## 🏗️ Architecture

VidBox is built with a modular architecture for reliability and extensibility:

```
vidbox/
├── 📁 boot/                 # Network & startup management
│   ├── wifi.py             # WiFi connection & hotspot
│   └── hotspot.sh          # Standalone hotspot script
├── 📁 web/                  # FastAPI web interface
│   ├── server.py           # Main web application
│   └── templates/          # HTML templates
├── 📁 display/              # Screen management
│   ├── player.py           # Playback engine
│   ├── spiout.py           # ILI9341 SPI driver
│   └── framebuf.py         # Frame buffer management
├── 📁 utils/                # Utilities
│   ├── convert.py          # Media conversion (ffmpeg+PIL)
│   └── logger.py           # Centralized logging
├── 📁 config/               # Configuration management
│   ├── schema.py           # Type-safe config classes
│   └── config.json         # Hardware settings
├── 📁 deployment/           # Update & deployment
│   ├── updater.py          # Multi-source update system
│   └── scripts/            # Installation scripts
└── 📁 media/                # Media storage
    ├── raw/                # Original uploads
    └── processed/          # Converted frames
```

### Core Components

- **Display Engine**: Threaded playback with frame-accurate timing
- **Web Server**: FastAPI with real-time status updates
- **Media Processor**: Automatic GIF/video → RGB565 conversion
- **Network Manager**: WiFi with hotspot fallback
- **Update System**: Multiple deployment methods with backups
- **Configuration**: Type-safe settings with validation

## 🔄 Deployment & Updates

VidBox supports multiple deployment methods:

### 1. GitHub Actions (Recommended)

Fully automated CI/CD pipeline with testing and deployment.

**Setup:**

1. Fork this repository
2. Add secrets: `PI_HOST`, `PI_USER`, `PI_SSH_KEY`, `PI_PATH`
3. Push to main branch or create tags for releases

**Features:**

- Automatic testing and building
- Direct SSH deployment to your Pi
- Service restart and health checks
- GitHub releases for version tracking

### 2. Simple Git Updates

For quick development iterations:

```bash
cd /home/pi/vidbox
git pull
sudo systemctl restart vidbox
```

### 3. Web Interface Updates

Check and install updates through the web interface:

- Go to Settings → System Updates
- Click "Check for Updates"
- Install with one click

### 4. Remote OTA Updates

Set up your own update server for multiple devices:

```json
{
  "sync": {
    "enabled": true,
    "server_url": "https://your-update-server.com/updates"
  }
}
```

### 5. Manual Installation

Download and extract releases manually:

```bash
wget https://github.com/yourusername/vidbox/releases/latest/download/vidbox-latest.tar.gz
tar -xzf vidbox-latest.tar.gz
sudo systemctl restart vidbox
```

## 🛠️ Development

### Local Development

```bash
# Set up development environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run in development mode
export VIDBOX_DEBUG=1
python main.py
```

### Testing on Pi

```bash
# Quick deploy for testing
rsync -av --exclude='.git' . pi@your-pi:/tmp/vidbox-test/
ssh pi@your-pi "cd /tmp/vidbox-test && python3 main.py"
```

### Configuration

Edit `config/config.json` for hardware-specific settings:

```json
{
  "display": {
    "width": 240,
    "height": 320,
    "dc_pin": 25,
    "rst_pin": 27,
    "bl_pin": 18
  },
  "wifi": {
    "hotspot_ssid": "VidBox-Setup",
    "hotspot_password": "vidbox123"
  }
}
```

## 📋 System Requirements

### Operating System

- **Raspberry Pi OS Lite** (32-bit, Bookworm recommended)
- **Python 3.9+** with pip and venv
- **SPI interface enabled**

### Dependencies

- **System**: ffmpeg, hostapd, dnsmasq, git
- **Python**: FastAPI, Pillow, OpenCV, RPi.GPIO, spidev
- **Development**: pytest, black, isort (optional)

### Performance

- **Boot time**: < 15 seconds to web interface
- **Frame rate**: Up to 30 FPS on Pi Zero 2W
- **Memory usage**: ~180MB RAM (plenty of headroom)
- **Storage**: ~50MB for application + media storage

## 🔧 Troubleshooting

### Display Issues

```bash
# Check SPI is enabled
lsmod | grep spi

# Test display directly
cd /home/pi/vidbox
source venv/bin/activate
python -c "from display.spiout import ILI9341Driver; from config.schema import get_config; d = ILI9341Driver(get_config().display); d.init(); d.fill_screen(0xF800)"
```

### Service Issues

```bash
# Check service status
sudo systemctl status vidbox

# View logs
sudo journalctl -u vidbox -f

# Restart service
sudo systemctl restart vidbox
```

### WiFi Issues

```bash
# Check WiFi status
iwconfig

# Force hotspot mode
sudo /home/pi/vidbox/boot/hotspot.sh start

# Restart networking
sudo systemctl restart wpa_supplicant
```

### Update Issues

```bash
# Manual update rollback
cd /home/pi/vidbox
sudo systemctl stop vidbox
cp -r ../vidbox_backup_* .
sudo systemctl start vidbox
```

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Development Guidelines

- Follow Python PEP 8 style guidelines
- Add type hints for new functions
- Include tests for new features
- Update documentation as needed

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Waveshare** for excellent LCD documentation and examples
- **FastAPI** for the outstanding web framework
- **Raspberry Pi Foundation** for the amazing hardware platform
- **Contributors** who make this project better

## 📞 Support

- **Documentation**: Check [QUICKSTART.md](QUICKSTART.md) and [DEPLOYMENT.md](DEPLOYMENT.md)
- **Issues**: Report bugs on [GitHub Issues](https://github.com/yourusername/vidbox/issues)
- **Discussions**: Join conversations in [GitHub Discussions](https://github.com/yourusername/vidbox/discussions)

---

**Made with ❤️ for the maker community**

_Turn any Raspberry Pi into a beautiful GIF display device!_ 🎬✨
