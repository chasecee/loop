# LOOP - Little Optical Output Pal

Your pocket-sized animation companion! LOOP is a network-connected display that brings your GIFs and videos to life on a tiny screen. **Optimized for Pi Zero 2 with real-time WebSocket updates** and aggressive performance caching.

![LOOP](https://img.shields.io/badge/Platform-Raspberry%20Pi-red) ![Python](https://img.shields.io/badge/Python-3.9+-blue) ![WebSocket](https://img.shields.io/badge/WebSocket-Real--time-green) ![License](https://img.shields.io/badge/License-MIT-green)

## What Can LOOP Do?

### Show Your Media

- Plays GIFs, videos (MP4, AVI, MOV), and images (PNG, JPG)
- Optimized for 240×320 ILI9341 SPI displays
- Smooth playback with efficient RGB565 frame conversion
- Smart loop management with configurable timing
- **Pi Zero 2 optimized** with real-time WebSocket updates and aggressive caching

### Easy Control

- Modern web interface with drag & drop uploads
- **Real-time WebSocket updates** - see changes instantly across all devices
- Real-time conversion progress in your browser
- Browse your media library with instant previews
- Loop queue management - drag to reorder, click to activate
- Playback controls: play/pause, next/previous, loop modes
- **Lightning-fast dashboard** with 50ms response times (was 1000ms+)

### Smart Connection

- **Manual IP Configuration** - Access LOOP via its IP address on your network
- **Web-based Interface** - Control everything through your browser
- **System updates** via web interface
- **WiFi Configuration UI** - Interface ready for future WiFi implementation

> **⚠️ WiFi Status**: WiFi functionality is currently **non-functional** in this build. The WiFi manager has been gutted and hotspot features are disabled. You'll need to connect LOOP to your network via Ethernet or manually configure WiFi through Raspberry Pi OS.

## Architecture

LOOP uses a **real-time, performance-first architecture** designed specifically for Pi Zero 2 constraints:

### Data Flow

1. **Browser Conversion** (`ffmpeg-util.ts`) - WebAssembly FFmpeg converts media to RGB565 frames
2. **Transaction-based Upload** - Browser uploads original video + processed frame ZIP with atomic coordination
3. **Real-time Updates** - WebSocket broadcasting eliminates polling, provides instant feedback
4. **Async Processing** - ZIP extraction happens in background threads without blocking
5. **Media Management** (`media_index.py`) - Single source of truth with 5-second aggressive caching
6. **Web API** (`server.py`) - Handles uploads with aggressive caching and GZip compression
7. **Display Player** (`player.py`) - Reads processed frames with producer-consumer buffering

### Key Components

- **`media_index.py`** - Authoritative media state manager with 5-second aggressive caching
- **`server.py`** - FastAPI web server with performance-optimized endpoints and WebSocket support
- **`player.py`** - Display controller with frame buffering for smooth playback
- **`ffmpeg-util.ts`** - Browser-side media processing using WebAssembly FFmpeg
- **`websocket.ts`** - Real-time communication client with auto-reconnection
- **`spiout.py`** - Hardware driver optimized for Pi Zero 2 performance

### Performance Optimizations

- **Real-time WebSocket Updates** - Eliminates 15-second polling, instant UI feedback
- **Aggressive Caching** - Dashboard data cached for 5 seconds, eliminates SD card I/O
- **Separated Storage** - Storage calculations only when settings modal opened
- **Browser Processing** - Zero Pi CPU used for media conversion
- **Frame Buffering** - Producer-consumer pattern for smooth playback
- **Request Deduplication** - Prevents multiple simultaneous API calls
- **Transaction Coordination** - Bulletproof upload system with atomic operations

This architecture ensures:

- **Instant responses** - Dashboard loads in ~50ms (was 1000ms+)
- **Real-time updates** - See changes instantly across all devices
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
- Enable WebSocket real-time communication
- Show you the IP address when ready

### 3. First Time Setup

1. **Network Connection**:

   - **Option A**: Connect Pi to your router via Ethernet cable
   - **Option B**: Manually configure WiFi through Raspberry Pi OS (SSH required)
   - **Note**: Built-in WiFi configuration is currently non-functional

2. **Find LOOP's IP Address**:

   - Check your router's admin panel for connected devices
   - Or SSH to Pi and run `hostname -I`

3. **Upload Media**:
   - Visit LOOP's web interface at `http://[pi-ip]`
   - Drag and drop your GIFs, videos, and images
   - Watch real-time conversion progress in your browser
   - See instant real-time updates via WebSocket
   - Media automatically joins the loop queue

### 4. Updates

Keep LOOP up to date via the web interface or manually:

```bash
cd /home/pi/loop
git pull
sudo systemctl restart loop
```

## Media Processing

LOOP uses **browser-side processing** for optimal performance with **transaction-based coordination**:

### Conversion Process

1. **Browser Conversion**: Your browser uses WebAssembly FFmpeg to convert media
2. **Frame Extraction**: Video converted to 320×240 RGB565 frames at 25fps
3. **ZIP Packaging**: Frames packaged into ZIP with metadata
4. **Transaction Upload**: Original video + frame ZIP uploaded with atomic coordination
5. **Real-time Progress**: WebSocket updates provide instant progress feedback
6. **Background Processing**: ZIP extraction happens asynchronously with real-time status

### Benefits

- **Instant**: Real-time WebSocket updates, no more 15-second polling delays
- **Fast**: No Pi CPU used for conversion, 50ms dashboard responses
- **Compatible**: Works with all major video formats
- **Reliable**: Transaction-based coordination prevents data loss, WebSocket auto-reconnection
- **Efficient**: Only final processed files sent to Pi, GZip-compressed responses

### Browser Requirements

- **Modern browser** with WebAssembly support (Chrome 57+, Firefox 52+, Safari 11+)
- **WebSocket support** for real-time updates (all modern browsers)
- **Sufficient RAM** for video processing (4GB+ recommended for large files)
- **JavaScript enabled** for the web interface

## Loop Management

LOOP's media management is powerful yet simple with **real-time updates**:

### Loop Queue

- **Ordered playlist** of your media with instant WebSocket updates
- **Drag to reorder** items in the web interface - see changes immediately
- **Add/remove** media from the queue with real-time feedback
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
- `max_file_size_mb`: Maximum file size for uploads (default: 50MB)
- `max_concurrent_requests`: Concurrency limit for Pi Zero 2 (default: 12)

## Controls

### Web Interface

- **Upload**: Drag & drop files anywhere on the page
- **Real-time Progress**: See conversion progress and instant WebSocket updates
- **Play/Pause**: Click the play button with instant feedback
- **Next/Previous**: Navigation buttons with real-time response
- **Activate Media**: Click on any media item to jump to it instantly
- **Loop Management**: Drag to reorder with real-time updates, toggle loop modes
- **System Settings**: Brightness, WiFi, updates with instant feedback

### API Endpoints

```bash
# Playback control (with WebSocket broadcasting)
POST /api/playback/toggle     # Play/pause
POST /api/playback/next       # Next media
POST /api/playback/previous   # Previous media

# Loop management (with real-time updates)
GET /api/loop                 # Get loop queue
POST /api/loop               # Add to loop
PUT /api/loop                # Reorder loop
DELETE /api/loop/{slug}      # Remove from loop

# Media management (with WebSocket events)
GET /api/media               # List all media
POST /api/media             # Upload processed media
DELETE /api/media/{slug}    # Delete media

# Real-time communication
GET /ws                      # WebSocket endpoint for real-time updates

# System status (high-performance)
GET /api/dashboard          # All system status in one call (50ms response)
GET /api/dashboard/storage  # Storage info (only when needed)
```

## Troubleshooting

### Slow Dashboard Response?

This should now be fixed with aggressive caching and WebSocket updates:

```bash
# Check if caching is working
curl -w "%{time_total}" http://localhost/api/dashboard

# Should be <0.1s for cached requests, <1s for cache misses
```

### WebSocket Connection Issues?

```bash
# Check WebSocket status
curl http://localhost/api/websocket/status

# Check real-time logs for WebSocket events
sudo journalctl -u loop -f | grep -E "(WebSocket|📡)"
```

### Storage Calculation Taking Forever?

This is now optimized and only calculated when needed:

```bash
# Storage is now only calculated when settings modal opened
# First calculation may take 30+ seconds, then cached for 1 hour
```

### Display Issues?

```bash
# Check LOOP service status
sudo systemctl status loop

# View real-time logs
sudo journalctl -u loop -f

# Performance-specific logs
sudo journalctl -u loop -f | grep -E "(Dashboard|Storage|Cache|WebSocket)"
```

### Upload Problems?

- **Check browser compatibility** - WebAssembly FFmpeg requires modern browser
- **Monitor memory usage** - Large files need 4GB+ browser RAM
- **Check WebSocket connection** - Real-time updates require WebSocket support
- **Try smaller files** - Test with simple GIF first
- **Check browser console** - Look for WebAssembly or WebSocket errors

### Service Problems?

```bash
sudo systemctl restart loop    # Restart LOOP
sudo systemctl stop loop       # Stop LOOP
sudo systemctl start loop      # Start LOOP
```

### Network Connection Issues?

```bash
# Check network interface status
ip addr show

# Check if Pi is connected to network
ping -c 3 8.8.8.8

# For WiFi configuration, use Raspberry Pi OS tools
sudo raspi-config  # Network Options > Wi-fi

# Note: Built-in WiFi manager is currently gutted and non-functional
# Use standard Raspberry Pi OS WiFi configuration instead
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
├── web/             # FastAPI server, WebSocket, and SPA
│   ├── core/        # WebSocket, events, models, middleware
│   ├── routes/      # API endpoints with WebSocket broadcasting
│   └── spa/         # Deployed Next.js build
└── boot/            # WiFi and system setup

frontend/loop-frontend/  # Next.js web interface
├── lib/ffmpeg-util.ts   # Browser-side media processing
├── lib/websocket.ts     # Real-time WebSocket client
├── hooks/               # WebSocket React hooks
├── components/          # UI components
└── app/                 # Pages and routing
```

## Performance

### Pi Zero 2 Specific Optimizations

- **Real-time WebSocket communication** eliminates 15-second polling overhead
- **5-second dashboard caching** eliminates file I/O on every request
- **Storage separation** - Only calculated when settings modal opened
- **Media index caching** - 5-second aggressive file stat avoidance
- **Frame queue buffering** - 30-frame producer-consumer buffer
- **Request deduplication** for API endpoints
- **Transaction coordination** prevents race conditions and data loss
- **Conservative memory usage** with automatic cleanup

### Performance Metrics

| Operation           | Before Optimization | After Optimization    | Improvement |
| ------------------- | ------------------- | --------------------- | ----------- |
| Dashboard requests  | 1000ms+             | ~50ms (cached + GZip) | 95%+ faster |
| Real-time updates   | 15-second polling   | Instant WebSocket     | Immediate   |
| Large file uploads  | HTTP timeouts       | Transaction-based     | Bulletproof |
| Media deletion      | Race conditions     | Clean atomic ops      | Reliable    |
| API responses       | Uncompressed        | 5-10x smaller (GZip)  | Bandwidth   |
| Storage calculation | Every 15s           | Only when needed      | 90% fewer   |

### Browser Optimization

- **WebAssembly FFmpeg** for native-speed conversion
- **Real-time WebSocket progress** with instant feedback
- **Transaction-based upload** with automatic retry
- **Chunked processing** to handle large files
- **Memory management** to prevent browser crashes

## Current Limitations

- **WiFi Management** - **Completely non-functional** - WiFi manager is gutted, hotspot disabled
- **Network Setup** - Requires manual Ethernet or OS-level WiFi configuration
- **Browser Requirements** - WebAssembly FFmpeg needs modern browser + 4GB+ RAM
- **Storage Performance** - Pi Zero 2 + SD card inherently limits I/O speed
- **Physical Controls** - Rotary encoder not yet implemented

## Known Issues

- **WiFi functionality is gutted** - All WiFi/hotspot features return errors
- Large files (>50MB) may require significant browser memory
- Storage calculations can be slow on first run (30+ seconds)
- WiFi configuration UI exists but calls non-functional backend

## Planned Features

- Physical rotary encoder controls
- Advanced scheduling and automation
- Mobile app companion
- Offline conversion support
- Custom display effects
- Multi-device synchronization

## Contributing

LOOP loves new contributors! Here's how to get involved:

1. **Fork** the repository
2. **Create** a feature branch
3. **Follow** the architecture patterns (respect WebSocket events and media_index.py authority!)
4. **Test** thoroughly on actual hardware with WebSocket functionality
5. **Submit** a Pull Request

Check the issues page for tasks that need attention!

## License

LOOP is open source under the MIT License. See [LICENSE](LICENSE) for details.

## Thanks

- **Waveshare** for excellent displays
- **FFmpeg** team for the amazing media processing library
- **WebAssembly** community for making browser-side processing possible
- **FastAPI** for the speedy web framework with WebSocket support
- **Raspberry Pi Foundation** for amazing hardware
- **Contributors** for making LOOP better

---

Made with love by the LOOP community  
_"Your pocket-sized animation companion with real-time updates!"_

## Architecture Philosophy

LOOP prioritizes **Pi Zero 2 performance and real-time user experience** above all else:

1. **Browser does the work** - Pi never processes media
2. **Real-time WebSocket updates** - No more waiting for polling cycles
3. **Aggressive caching** - Minimize SD card I/O at all costs
4. **Smart separation** - Storage only calculated when needed
5. **Transaction coordination** - Bulletproof upload handling
6. **Conservative resources** - Respect Pi Zero 2 limitations
7. **Honest documentation** - Document what works and what doesn't

## Performance Monitoring

### Check Dashboard Performance

```bash
# Monitor dashboard response times
curl -w "Response time: %{time_total}s\n" http://localhost/api/dashboard

# Watch for cache hits/misses in logs
sudo journalctl -u loop -f | grep "Dashboard"
```

### WebSocket Performance

```bash
# Check WebSocket connection status
curl http://localhost/api/websocket/status

# Monitor real-time events
sudo journalctl -u loop -f | grep "📡"
```

### Storage Performance

```bash
# Check if storage caching is working
sudo journalctl -u loop -f | grep "Storage"

# Should see cache hits after first calculation
```
