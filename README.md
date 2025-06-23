# LOOP - Little Optical Output Pal

Your pocket-sized animation companion! LOOP is a Wi-Fi enabled display that brings your GIFs and videos to life on a tiny screen. **Optimized for Pi Zero 2 performance** with aggressive caching and browser-first processing.

![LOOP](https://img.shields.io/badge/Platform-Raspberry%20Pi-red) ![Python](https://img.shields.io/badge/Python-3.9+-blue) ![License](https://img.shields.io/badge/License-MIT-green)

## What Can LOOP Do?

### Show Your Media

- Plays GIFs, videos (MP4, AVI, MOV), and images (PNG, JPG)
- Optimized for 240×320 ILI9341 SPI displays
- Smooth playback with efficient RGB565 frame conversion
- Smart loop management with configurable timing
- **Pi Zero 2 optimized** with aggressive caching and minimal SD card I/O

### Easy Control

- Modern web interface with drag & drop uploads
- Real-time conversion progress in your browser
- Browse your media library with instant previews
- Loop queue management - drag to reorder, click to activate
- Playback controls: play/pause, next/previous, loop modes
- **Performance-optimized dashboard** with 5-second caching

### Smart Connection

- Auto-connects to your WiFi
- Sets up its own "LOOP-Setup" network when needed
- Web-based WiFi configuration
- System updates via web interface

> **Note**: WiFi functionality may have limitations in current build

## Architecture

LOOP uses a **performance-first architecture** designed specifically for Pi Zero 2 constraints:

### Data Flow

1. **Browser Conversion** (`ffmpeg-util.ts`) - WebAssembly FFmpeg converts media to RGB565 frames
2. **Dual Upload** - Browser uploads original video + processed frame ZIP separately
3. **Media Management** (`media_index.py`) - Single source of truth with aggressive in-memory caching
4. **Web API** (`server.py`) - Handles uploads with 5-second dashboard caching
5. **Display Player** (`player.py`) - Reads processed frames with producer-consumer buffering

### Key Components

- **`media_index.py`** - Authoritative media state manager with 5-second aggressive caching
- **`server.py`** - FastAPI web server with performance-optimized endpoints
- **`player.py`** - Display controller with frame buffering for smooth playback
- **`ffmpeg-util.ts`** - Browser-side media processing using WebAssembly FFmpeg
- **`spiout.py`** - Hardware driver optimized for Pi Zero 2 performance

### Performance Optimizations

- **Aggressive Caching** - Dashboard data cached for 5 seconds, eliminates SD card I/O
- **Separated Storage** - Storage calculations only when settings modal opened
- **Browser Processing** - Zero Pi CPU used for media conversion
- **Frame Buffering** - Producer-consumer pattern for smooth playback
- **Smart Polling** - Reduced frequency during uploads, backoff on errors

This architecture ensures:

- **Fast responses** - Dashboard loads in ~50ms (was 1000ms+)
- **Consistency** - Single source of truth prevents race conditions
- **Pi Zero 2 Optimized** - Minimal SD card I/O and memory usage
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

### Slow Dashboard Response?

Recent optimizations should have fixed this, but if you see slow responses:

```bash
# Check if caching is working
curl -w "%{time_total}" http://localhost/api/dashboard

# Should be <0.1s for cached requests, <1s for cache misses
```

### Storage Calculation Taking Forever?

This is normal on first startup but should be cached afterwards:

```bash
# Storage is now only calculated when settings modal opened
# First calculation may take 30+ seconds, then cached for 5 minutes
```

### Display Issues?

```bash
# Check LOOP service status
sudo systemctl status loop

# View real-time logs
sudo journalctl -u loop -f

# Performance-specific logs
sudo journalctl -u loop -f | grep -E "(Dashboard|Storage|Cache)"
```

### Upload Problems?

- **Check browser compatibility** - WebAssembly FFmpeg requires modern browser
- **Monitor memory usage** - Large files need 4GB+ browser RAM
- **Try smaller files** - Test with simple GIF first
- **Check browser console** - Look for WebAssembly errors

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

### Pi Zero 2 Specific Optimizations

- **5-second dashboard caching** eliminates file I/O on every request
- **Storage separation** - Only calculated when settings modal opened
- **Media index caching** - 5-second aggressive file stat avoidance
- **Frame queue buffering** - 30-frame producer-consumer buffer
- **Request deduplication** for polling endpoints
- **Conservative memory usage** with automatic cleanup

### Performance Metrics

| Operation            | Before Optimization | After Optimization      |
| -------------------- | ------------------- | ----------------------- |
| Dashboard requests   | 1000ms+             | ~50ms (cached)          |
| Storage calculation  | Every 15s           | Only when needed        |
| Media index reads    | File I/O every time | 5s cache                |
| Startup storage scan | 36+ seconds         | Skipped if recent cache |

### Browser Optimization

- **WebAssembly FFmpeg** for native-speed conversion
- **Progressive upload** with real-time progress
- **Chunked processing** to handle large files
- **Memory management** to prevent browser crashes

## Current Limitations

- **WiFi Management** - May have functionality gaps in current build
- **Browser Requirements** - WebAssembly FFmpeg needs modern browser + 4GB+ RAM
- **Storage Performance** - Pi Zero 2 + SD card inherently limits I/O speed
- **File Resume** - Large uploads can't be resumed if interrupted
- **Physical Controls** - Rotary encoder not yet implemented

## Known Issues

- WiFi scanning/connection functionality may be incomplete
- Large files (>100MB) may require significant browser memory
- Storage calculations can be slow on first run (30+ seconds)
- Upload progress may pause during browser processing phases

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

## Architecture Philosophy

LOOP prioritizes **Pi Zero 2 performance** above all else:

1. **Browser does the work** - Pi never processes media
2. **Aggressive caching** - Minimize SD card I/O at all costs
3. **Smart separation** - Storage only calculated when needed
4. **Conservative resources** - Respect Pi Zero 2 limitations
5. **Honest documentation** - Document what works and what doesn't

## Performance Monitoring

### Check Dashboard Performance

```bash
# Monitor dashboard response times
curl -w "Response time: %{time_total}s\n" http://localhost/api/dashboard

# Watch for cache hits/misses in logs
sudo journalctl -u loop -f | grep "Dashboard"
```

### Storage Performance

```bash
# Check if storage caching is working
sudo journalctl -u loop -f | grep "Storage"

# Should see cache hits after first calculation
```
