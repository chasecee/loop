# LOOP - Little Optical Output Pal

Network-connected GIF/video display optimized for Pi Zero 2 with real-time WebSocket updates and browser-side media processing.

![LOOP](https://img.shields.io/badge/Platform-Raspberry%20Pi-red) ![Python](https://img.shields.io/badge/Python-3.9+-blue) ![WebSocket](https://img.shields.io/badge/WebSocket-Real--time-green) ![License](https://img.shields.io/badge/License-MIT-green)

## **What It Does**

**Display Management**: Plays GIFs, videos (MP4/AVI/MOV), and images (PNG/JPG) on 240×320 ILI9341 SPI displays with smooth RGB565 frame conversion and configurable loop timing.

**Real-time Control**: Web interface with drag-and-drop uploads, instant WebSocket updates across all devices, live conversion progress, and collaborative multi-device control.

**Smart Processing**: Browser-side WebAssembly FFmpeg conversion eliminates Pi CPU load, transaction-based uploads prevent data corruption, and aggressive caching delivers sub-100ms dashboard responses.

## **Architecture**

### **Data Flow**

```
Browser (WASM FFmpeg) → RGB565 Frames → ZIP + Original Video
    ↓ (Transaction Upload)
Backend Coordinator → Atomic File Ops → Media Index Cache
    ↓ (WebSocket Broadcast)
Display Player ← Frame Buffer Queue ← Processed Frames
    ↓
All Connected Clients ← Real-time Updates ← WebSocket Manager
```

### **Key Components**

**Backend (Python/FastAPI)**

- `server.py` - FastAPI with WebSocket support, GZip compression, request deduplication
- `upload_coordinator.py` - Transaction-based upload processing with atomic rollback
- `display/player.py` - Frame playback with 30-frame producer-consumer buffering
- `media_index.py` - Single source of truth with 5-second aggressive caching
- `websocket.py` - Room-based real-time event broadcasting to connected clients
- `spiout.py` - ILI9341 SPI display driver with hardware abstraction

**Frontend (Next.js/TypeScript)**

- `ffmpeg-util.ts` - WebAssembly FFmpeg wrapper for browser-side RGB565 conversion
- `websocket.ts` - Auto-reconnecting WebSocket client with exponential backoff
- `upload-coordinator.ts` - Transaction-based upload with progress coordination
- `use-websocket-dashboard.ts` - React hook for real-time dashboard updates

### **Performance Optimizations**

**Real-time Communication**: WebSocket events eliminate 15-second polling, provide instant feedback across all devices with room-based subscriptions (dashboard, progress, wifi, system).

**Aggressive Caching**: Dashboard data cached 5 seconds, storage calculations cached 1 hour, media index cached 5 seconds to minimize SD card I/O on Pi Zero 2.

**Browser Processing**: WebAssembly FFmpeg converts media to Pi-optimized RGB565 format, zero Pi CPU usage for conversion, chunked processing handles large files without browser crashes.

**Transaction Safety**: Atomic upload operations with rollback on failure, duplicate detection prevents race conditions, parallel cleanup operations during error recovery.

**Frame Buffering**: Producer-consumer pattern with 30-frame queue, interruptible waits for pause/resume, automatic media switching with wraparound search.

## **Hardware Setup**

### **Requirements**

- **Raspberry Pi Zero 2 W** or **Pi 4**
- **Waveshare 2.4" ILI9341 LCD** (240×320 SPI display)
- **MicroSD card** (8GB+, Class 10 recommended)
- **5V USB power supply**

### **Wiring**

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

## **Installation**

### **System Setup**

1. Flash Raspberry Pi OS Lite (32-bit), enable SSH
2. Connect Pi to network (Ethernet or manual WiFi configuration)
3. Clone repository and run automated installer

```bash
git clone https://github.com/yourusername/loop.git
cd loop
sudo ./backend/deployment/scripts/install.sh
```

### **Installation Process**

The installer handles:

- System package dependencies (Python 3.9+, FFmpeg, NetworkManager)
- SPI interface configuration in `/boot/firmware/config.txt`
- Python virtual environment with optimized package installation
- Systemd service registration (`loop.service`, `boot-display.service`)
- WiFi power management configuration for stable connectivity
- Log rotation and directory permissions

### **Service Architecture**

- **loop.service** - Main application with GPIO/SPI permissions, port 80 binding
- **boot-display.service** - Sets display black during system startup
- **system-management.service** - WiFi power management configuration

## **Media Processing Pipeline**

### **Browser-Side Conversion**

1. **File Upload** - User drags media files to web interface
2. **WASM FFmpeg** - Browser converts to 320×240 RGB565 frames @ 25fps
3. **ZIP Packaging** - Frames packaged with metadata.json
4. **Transaction Upload** - Original video + frame ZIP sent atomically
5. **Progress Tracking** - Real-time WebSocket updates during entire process

### **Backend Processing**

1. **Transaction Coordination** - Atomic file operations with rollback safety
2. **Media Index Update** - Add to authoritative media state with caching
3. **Frame Organization** - Extract frames to `media/processed/{slug}/frames/`
4. **WebSocket Broadcast** - Notify all clients of new media availability
5. **Display Integration** - Media automatically available for playback

### **Browser Requirements**

- **WebAssembly support** (Chrome 57+, Firefox 52+, Safari 11+)
- **WebSocket support** for real-time updates (all modern browsers)
- **4GB+ RAM recommended** for large video processing
- **JavaScript enabled** for web interface functionality

## **Loop Management**

### **Media Queue**

- **Ordered playlist** with real-time drag-and-drop reordering
- **Configurable loop count** per media item (default: 2 loops)
- **Auto-advance enabled** by default with manual override
- **Instant activation** - click any media to jump immediately

### **Playback Modes**

- **Loop All** - Cycles through queue, repeating each item N times
- **Loop One** - Stays on current media, repeating N times
- **Manual Control** - Play/pause, next/previous with WebSocket feedback

### **Configuration**

Key settings in `backend/config/config.json`:

```json
{
  "media": {
    "loop_count": 2,
    "static_image_duration_sec": 10,
    "auto_advance_enabled": true,
    "max_file_size_mb": 50
  },
  "web": {
    "max_concurrent_requests": 12,
    "request_timeout_seconds": 300
  },
  "display": {
    "framerate": 25,
    "show_progress": true,
    "brightness": 100
  }
}
```

## **API Reference**

### **REST Endpoints**

```bash
# Media management
GET /api/media                    # List all media with metadata
POST /api/media                   # Upload processed media (transaction-based)
DELETE /api/media/{slug}          # Delete media with cleanup
POST /api/media/{slug}/activate   # Set active media

# Loop queue management
GET /api/loop                     # Get current loop queue
POST /api/loop                    # Add media to loop
PUT /api/loop                     # Reorder loop queue
DELETE /api/loop/{slug}           # Remove from loop

# Playback control
POST /api/playback/toggle         # Play/pause with WebSocket broadcast
POST /api/playback/next           # Next media
POST /api/playback/previous       # Previous media

# System status (performance optimized)
GET /api/dashboard                # All system status (50ms cached response)
GET /api/dashboard/storage        # Storage info (1-hour cached, only when needed)

# Real-time communication
GET /ws                           # WebSocket endpoint with room subscriptions
GET /api/websocket/status         # WebSocket connection diagnostics
```

### **WebSocket Events**

```typescript
// Room subscriptions
"dashboard"; // System status, media, loop changes
"progress"; // Upload/processing progress updates
"wifi"; // WiFi status changes
"system"; // System-level notifications

// Event types
"initial_dashboard"; // Complete state on connection
"dashboard_update"; // Incremental state changes
"media_uploaded"; // New media available
"media_deleted"; // Media removed
"loop_updated"; // Queue reordered
"playback_changed"; // Play/pause/next/previous
"upload_progress"; // Real-time conversion progress
```

## **Development**

### **Local Development**

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

# Frontend deployment to backend
./deploy-frontend.sh
```

### **Architecture Guidelines**

**Backend Patterns**:

- Media Index is single source of truth - never bypass
- WebSocket broadcasting for all state changes
- Transaction-based operations with atomic rollback
- Aggressive caching with explicit invalidation
- Hardware abstraction with fallback demo mode

**Frontend Patterns**:

- WebSocket-first for real-time updates, API for actions
- Transaction coordination for upload safety
- React hooks for WebSocket state management
- Web Workers for non-blocking processing
- Error boundaries with automatic retry logic

## **Performance Metrics**

| Operation           | Before Optimization | Current Performance | Improvement     |
| ------------------- | ------------------- | ------------------- | --------------- |
| Dashboard requests  | 1000ms+             | ~50ms (cached)      | 95% faster      |
| Real-time updates   | 15s polling delay   | Instant WebSocket   | Immediate       |
| Media upload        | HTTP timeouts       | Transaction-based   | Bulletproof     |
| Storage calculation | Every request       | 1-hour cache        | 90% fewer calls |
| Frame display       | Blocking I/O        | 30-frame buffer     | Smooth playback |

## **System Requirements**

### **Pi Zero 2 Constraints**

- **Single-core ARM Cortex-A53** @ 1GHz with limited thermal headroom
- **512MB RAM** shared between system and GPU
- **SD card I/O** inherently slower than SSD/eMMC storage
- **USB 2.0** bandwidth limitations for network connectivity

### **Optimization Strategy**

- **Offload processing** to browser WebAssembly FFmpeg
- **Minimize SD I/O** with aggressive caching and batch operations
- **Real-time communication** eliminates expensive polling cycles
- **Conservative memory usage** with bounded queues and cleanup
- **Hardware abstraction** allows development without physical display

## **Troubleshooting**

### **Performance Issues**

```bash
# Check dashboard response time
curl -w "Response: %{time_total}s\n" http://localhost/api/dashboard

# Monitor WebSocket connections
curl http://localhost/api/websocket/status

# Check caching effectiveness
sudo journalctl -u loop -f | grep -E "(Dashboard|Cache)"
```

### **WebSocket Problems**

```bash
# Test WebSocket connectivity
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Key: test" -H "Sec-WebSocket-Version: 13" \
  http://localhost/ws

# Monitor real-time events
sudo journalctl -u loop -f | grep "📡"
```

### **Upload Failures**

- **Browser compatibility** - Requires WebAssembly and WebSocket support
- **Memory constraints** - Large files need 4GB+ browser RAM
- **Network stability** - Check WebSocket connection status
- **File format support** - Test with simple GIF first
- **Transaction conflicts** - Check for concurrent upload attempts

### **Service Management**

```bash
# Service control
sudo systemctl status loop      # Check service status
sudo systemctl restart loop     # Restart after configuration changes
sudo systemctl stop loop        # Stop service

# Log analysis
sudo journalctl -u loop -f      # Real-time logs
sudo journalctl -u loop --since "1 hour ago" | grep ERROR

# Storage and performance monitoring
df -h                           # Check disk usage
sudo journalctl -u loop -f | grep -E "(Storage|WebSocket|Cache)"
```

## **Current Limitations**

### **Hardware**

- **Display dependency** - Requires ILI9341 SPI display (demo mode available)
- **GPIO access** - Needs Pi hardware or compatible SPI interface
- **Storage performance** - SD card I/O inherently limits throughput

### **Software**

- **Browser requirements** - Modern browser with WebAssembly + 4GB+ RAM
- **Network dependency** - Requires stable connectivity for WebSocket updates
- **File size limits** - Large videos (>50MB) may cause browser memory issues

### **Network Configuration**

- **Manual WiFi setup** - Initial connection requires OS-level configuration
- **IP-based access** - No automatic discovery (check router for Pi IP address)

## **Future Enhancements**

- **Physical controls** - Rotary encoder integration for standalone operation
- **Advanced scheduling** - Time-based media switching and automation
- **Multi-device sync** - Coordinate multiple LOOP displays
- **Offline conversion** - Pi-based processing fallback for constrained browsers
- **Mobile companion app** - Native iOS/Android control interface

## **Contributing**

Development focuses on Pi Zero 2 performance and real-time user experience:

1. **Respect caching architecture** - Invalidate appropriately, avoid cache bypass
2. **WebSocket-first communication** - Broadcast state changes, maintain consistency
3. **Transaction-based operations** - Ensure atomic file operations with rollback
4. **Hardware abstraction** - Support development without physical Pi/display
5. **Performance monitoring** - Measure and optimize for SD card I/O constraints

Fork the repository, create feature branches, test on actual hardware, and submit pull requests with performance impact analysis.

## **License**

MIT License - see [LICENSE](LICENSE) for details.

---

_Built for reliability on Pi Zero 2 with real-time WebSocket updates and browser-side processing._
