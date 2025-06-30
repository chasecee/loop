# LOOP - Little Optical Output Pal

Pi Zero 2 W display device for GIFs and videos with web-based control.

![LOOP](https://img.shields.io/badge/Platform-Raspberry%20Pi-red) ![Python](https://img.shields.io/badge/Python-3.9+-blue) ![License](https://img.shields.io/badge/License-MIT-green)

## What It Does

Network-connected 240×320 LCD display that plays GIFs, videos, and images. Upload media through a web interface, manage playlists, and control playback remotely. Browser-side FFmpeg processing eliminates Pi CPU load.

## Hardware

- **Raspberry Pi Zero 2 W** or Pi 4
- **Waveshare 2.4" ILI9341 LCD** (240×320 SPI display)
- **MicroSD card** (8GB+, Class 10)
- **5V USB power supply**

### Wiring

```
LCD Pin  → Pi Pin (BCM)  → Physical Pin
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

1. Flash Raspberry Pi OS Lite, enable SSH
2. Clone and install:

```bash
git clone https://github.com/yourusername/loop.git
cd loop
sudo ./backend/deployment/scripts/install.sh
```

The installer handles:

- System dependencies (Python, FFmpeg, NetworkManager)
- SPI interface configuration
- Virtual environment setup
- Systemd services (`loop.service`, `boot-display.service`)
- WiFi permissions

Access the web interface at `http://[pi-ip-address]` after installation.

## Usage

### Media Upload

- Drag & drop files to web interface
- Browser converts media to Pi-optimized format (RGB565 frames)
- Supports: MP4, MOV, AVI, GIF, PNG, JPG (max 100MB)

### Playback Control

- **Queue Management**: Drag to reorder playlist
- **Loop Settings**: Configure per-media loop count
- **Manual Control**: Play/pause, next/previous
- **Auto-advance**: Automatic playlist progression

### WiFi Management

- Configure networks through web interface
- Hotspot mode for initial setup (`LOOP-Setup` / `loop12345`)
- Automatic power management optimization

## Configuration

Key settings in `backend/config/config.json`:

```json
{
  "media": {
    "loop_count": 2,
    "static_image_duration_sec": 10,
    "auto_advance_enabled": true
  },
  "display": {
    "framerate": 25,
    "brightness": 100,
    "show_progress": true
  }
}
```

## Service Management

```bash
sudo systemctl status loop              # Check service status
sudo systemctl restart loop             # Restart service
sudo journalctl -u loop -f              # View logs
```

## Development

### Backend Development

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

### Frontend Development

```bash
cd frontend/loop-frontend
npm install
npm run dev
```

Deploy frontend to backend:

```bash
./deploy-frontend.sh
```

## Architecture

- **Backend**: FastAPI/Python with SQLite storage
- **Frontend**: Next.js/React with polling updates
- **Display**: Direct SPI communication (no framebuffer)
- **Processing**: Browser-side WebAssembly FFmpeg
- **Communication**: RESTful API with smart polling

## Troubleshooting

### Service Issues

```bash
# Check all services
sudo systemctl status loop boot-display system-management

# Check logs
sudo journalctl -u loop --since "1 hour ago"
```

### Display Problems

- Verify SPI enabled: `ls /dev/spi*`
- Check wiring connections
- Ensure user in `gpio` and `spi` groups

### Network Issues

- Check WiFi power management: `iw dev wlan0 get power_save`
- Test mDNS: `getent hosts loop.local`

## License

MIT License - see [LICENSE](LICENSE) for details.
