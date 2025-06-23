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
- Real-time conversion progress in your browser
- Browse your media library with instant previews
- Loop queue management - drag to reorder, click to activate
- Playback controls: play/pause, next/previous, loop modes

### Smart Connection

- Auto-connects to your WiFi
- Sets up its own "LOOP-Setup" network when needed
- Web-based WiFi configuration
- System updates via web interface

## Architecture

LOOP uses a modern browser-first architecture that keeps the Pi lightweight:

### Data Flow

1. **Browser Conversion** (`ffmpeg-util.ts`) - WebAssembly FFmpeg converts media to RGB565 frames
2. **File Upload** - Browser uploads original video + processed frame ZIP to Pi
3. **Media Management** (`media_index.py`) - Single source of truth for media state and loop ordering
4. **Web API** (`server.py`) - Handles uploads and state changes, respects media_index authority
5. **Display Player** (`player.py`) - Reads processed frames for Pi display, never modifies state

### Key Components

- **`media_index.py`** - Authoritative media state manager with in-memory caching
- **`server.py`** - FastAPI web server handling uploads and API requests
- **`player.py`** - Display controller that reads from media_index
- **`ffmpeg-util.ts`** - Browser-side media processing using WebAssembly FFmpeg
- **`spiout.py`** - Hardware driver for Waveshare ILI9341 displays

This architecture ensures:

- **Fast uploads** - No Pi CPU spent on conversion
- **Consistency** - Single source of truth prevents race conditions
- **Scalability** - Browser does the heavy lifting
- **Reliability** - Pi focuses on display and file management

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
- Deploy the pre-built web interface
- Show you the IP address when ready

### 3. First Time Setup

1. **Connect to WiFi**:

   - Look for "LOOP-Setup" network (password: loop123)
   - Open any website and configure WiFi via the captive portal

2. **Upload Media**:
   - Visit LOOP's web interface at `http://[pi-ip]`
   - Drag and drop your GIFs, videos, and images
   - Watch real-time conversion progress in your browser
   - Media automatically joins the loop queue

### 4. Updates

Keep LOOP up to date via the web interface or manually:

```bash
cd /home/pi/loop
git pull
sudo systemctl restart loop
```

## Media Processing

LOOP uses **browser-side processing** for optimal performance:

### Conversion Process

1. **Browser Conversion**: Your browser uses WebAssembly FFmpeg to convert media
2. **Frame Extraction**: Video converted to 320×240 RGB565 frames at 25fps
3. **ZIP Packaging**: Frames packaged into ZIP with metadata
4. **Upload**: Original video + frame ZIP uploaded to Pi
5. **Storage**: Pi stores files and updates media index

### Benefits

- **Fast**: No Pi CPU used for conversion
- **Compatible**: Works with all major video formats
- **Reliable**: Browser handles complex codec support
- **Efficient**: Only final processed files sent to Pi

### Browser Requirements

- **Modern browser** with WebAssembly support (Chrome 57+, Firefox 52+, Safari 11+)
- **Sufficient RAM** for video processing (4GB+ recommended for large files)
- **JavaScript enabled** for the web interface

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

- `loop_count`: How many times each media repeats (default: 2)
- `static_image_duration_sec`: How long static images display (default: 10)
- `auto_advance_enabled`: Whether to automatically advance (default: true)
- `max_file_size_mb`: Maximum file size for uploads (default: 200MB)

## Controls

### Web Interface

- **Upload**: Drag & drop files anywhere on the page
- **Real-time Progress**: See conversion progress in your browser
- **Play/Pause**: Click the play button or use API
- **Next/Previous**: Navigation buttons
- **Activate Media**: Click on any media item to jump to it
- **Loop Management**: Drag to reorder, toggle loop modes
- **System Settings**: Brightness, WiFi, updates

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
POST /api/media             # Upload processed media
DELETE /api/media/{slug}    # Delete media

# System status (consolidated)
GET /api/dashboard          # All system status in one call
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

### Upload Problems?

- **Check browser compatibility** - WebAssembly FFmpeg requires modern browser
- **Verify file size** - Large files may need more time/memory
- **Monitor browser console** - Check for JavaScript errors
- **Try smaller files** - Test with simple GIF first

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
curl -X POST http://localhost/api/media/cleanup
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
├── utils/           # Media indexing and utilities
├── web/             # FastAPI server and SPA
└── boot/            # WiFi and system setup

frontend/loop-frontend/  # Next.js web interface
├── lib/ffmpeg-util.ts   # Browser-side media processing
├── components/          # UI components
└── app/                 # Pages and routing
```

## Performance

### Pi Optimization

- **In-memory caching** for media index operations
- **Batch operations** for multiple uploads
- **Deferred persistence** to reduce SD card writes
- **Request deduplication** for polling endpoints
- **Conservative memory usage** with cleanup

### Browser Optimization

- **WebAssembly FFmpeg** for native-speed conversion
- **Progressive upload** with real-time progress
- **Chunked processing** to handle large files
- **Memory management** to prevent browser crashes

## Current Limitations

- Physical controls (rotary encoder) not yet implemented
- Browser-side processing requires modern browser with sufficient RAM
- Large video files may take time to process in browser
- No advanced scheduling features yet

## Planned Features

- Physical rotary encoder controls
- Advanced scheduling and automation
- Mobile app companion
- Offline conversion support
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
- **FFmpeg** team for the amazing media processing library
- **WebAssembly** community for making browser-side processing possible
- **FastAPI** for the speedy web framework
- **Raspberry Pi Foundation** for amazing hardware
- **Contributors** for making LOOP better

---

Made with love by the LOOP community  
_"Your pocket-sized animation companion!"_
