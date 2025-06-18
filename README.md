# LOOP - Little Optical Output Pal

Your pocket-sized animation companion! LOOP is a Wi-Fi enabled display that brings your GIFs and videos to life on a tiny screen. Perfect for desk companions, status displays, or just sharing moments of joy!

![LOOP](https://img.shields.io/badge/Platform-Raspberry%20Pi-red) ![Python](https://img.shields.io/badge/Python-3.9+-blue) ![License](https://img.shields.io/badge/License-MIT-green)

## What Can LOOP Do?

### Show Your Media

- Plays GIFs, videos (MP4, AVI, MOV), and images (PNG, JPG)
- Optimized for 240×320 ILI9341 SPI displays
- Smooth playback with efficient RGB565 frame conversion
- Smart loop management with configurable timing

### Easy Control

- Modern web interface with drag & drop uploads
- Real-time progress tracking during uploads
- Browse your media library with instant previews
- Loop queue management - drag to reorder, click to activate
- Playback controls: play/pause, next/previous, loop modes

### Smart Connection

- Auto-connects to your WiFi
- Sets up its own "LOOP-Setup" network when needed
- Web-based WiFi configuration
- System updates via web interface

## Architecture

LOOP uses a clean, authority-based architecture:

- **`media_index.py`** - Single source of truth for all media state, loop ordering, and active media
- **`server.py`** - Web API that respects media_index authority for all state changes
- **`player.py`** - Display controller that reads from media_index, never modifies state directly
- **`convert.py`** - Media processing engine that only reports progress, doesn't manage state

This ensures consistency and prevents race conditions across the system.

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
# Clone the repository
git clone https://github.com/yourusername/loop.git
cd loop

# Run the installer (handles all dependencies)
sudo ./backend/deployment/scripts/install.sh
```

The installer will:

- Install Python dependencies and system packages
- Set up the systemd service
- Configure SPI for the display
- Show you the IP address when ready

### 3. First Time Setup

1. **Connect to WiFi**:

   - Look for "LOOP-Setup" network (password: loop123)
   - Open any website and configure WiFi via the captive portal

2. **Upload Media**:
   - Visit LOOP's web interface at `http://[pi-ip]:8000`
   - Drag and drop your GIFs, videos, and images
   - Watch real-time conversion progress
   - Media automatically joins the loop queue

### 4. Updates

Keep LOOP up to date via the web interface or manually:

```bash
cd /home/pi/loop
git pull
sudo systemctl restart loop
```

## Loop Management

LOOP's media management is powerful yet simple:

### Loop Queue

- **Ordered playlist** of your media
- **Drag to reorder** items in the web interface
- **Add/remove** media from the queue
- **Configurable loop count** (how many times each item plays)

### Playback Modes

- **Loop All**: Cycles through entire queue, repeating each item N times
- **Loop One**: Stays on current media, repeating N times
- **Auto-advance**: Automatically moves to next after completion

### Configuration

Key settings in `backend/config/config.json`:

- `loop_count`: How many times each media repeats (default: 3)
- `static_image_duration_sec`: How long static images display (default: 10)
- `auto_advance_enabled`: Whether to automatically advance (default: true)

## Controls

### Web Interface

- **Upload**: Drag & drop files anywhere on the page
- **Play/Pause**: Click the play button or use API
- **Next/Previous**: Navigation buttons
- **Activate Media**: Click on any media item to jump to it
- **Loop Management**: Drag to reorder, toggle loop modes
- **Progress Tracking**: Real-time upload and conversion progress

### API Endpoints

```bash
# Playback control
POST /api/playback/toggle     # Play/pause
POST /api/playback/next       # Next media
POST /api/playback/previous   # Previous media

# Loop management
GET /api/loop                 # Get loop queue
POST /api/loop               # Add to loop
PUT /api/loop                # Reorder loop
DELETE /api/loop/{slug}      # Remove from loop

# Media management
GET /api/media               # List all media
POST /api/media             # Upload new media
DELETE /api/media/{slug}    # Delete media
```

## Troubleshooting

### Display Issues?

```bash
# Check LOOP service status
sudo systemctl status loop

# View real-time logs
sudo journalctl -u loop -f

# Test display hardware
cd /home/pi/loop/backend
source ../venv/bin/activate
python test_display_progress.py
```

### Service Problems?

```bash
sudo systemctl restart loop    # Restart LOOP
sudo systemctl stop loop       # Stop LOOP
sudo systemctl start loop      # Start LOOP
```

### WiFi Troubles?

```bash
# Reset WiFi and start hotspot
sudo systemctl restart wpa_supplicant
cd /home/pi/loop/backend
python -c "from boot.wifi import WiFiManager; WiFiManager().start_hotspot()"
```

### Storage Issues?

Check storage via the web interface or:

```bash
# Check disk usage
df -h

# Clean up orphaned media files
curl -X POST http://localhost:8000/api/media/cleanup
```

## Development

### Local Development

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py

# Frontend
cd frontend/loop-frontend
npm install
npm run dev
```

### File Structure

```
backend/
├── config/          # Configuration management
├── display/         # Display drivers and player
├── utils/           # Media conversion and indexing
├── web/             # FastAPI server and SPA
└── boot/            # WiFi and system setup

frontend/loop-frontend/  # Next.js web interface
```

## Current Limitations

- Physical controls (rotary encoder) not yet implemented
- Video format support limited to common formats
- Performance depends on Pi model and media complexity
- No advanced scheduling features yet

## Planned Features

- Physical rotary encoder controls
- Advanced scheduling and automation
- Mobile app companion
- More media format support
- Custom display effects

## Contributing

LOOP loves new contributors! Here's how to get involved:

1. **Fork** the repository
2. **Create** a feature branch
3. **Follow** the architecture patterns (respect media_index.py authority!)
4. **Test** thoroughly on actual hardware
5. **Submit** a Pull Request

Check the issues page for tasks that need attention!

## License

LOOP is open source under the MIT License. See [LICENSE](LICENSE) for details.

## Thanks

- **Waveshare** for excellent displays
- **FastAPI** for the speedy web framework
- **Raspberry Pi Foundation** for amazing hardware
- **Contributors** for making LOOP better

---

Made with love by the LOOP community  
_"Your pocket-sized animation companion!"_
