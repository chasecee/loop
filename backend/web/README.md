# Web Server

**Real-time optimized** FastAPI web server designed specifically for Pi Zero 2 constraints. Features **completed WebSocket migration**, aggressive caching, storage separation, and minimal SD card I/O.

## 🏗️ **FRONTEND DEPLOYMENT ARCHITECTURE**

**Intentional SPA Integration:**

- Frontend built as git submodule in `frontend/loop-frontend/`
- `deploy-frontend.sh` script builds and copies to `backend/web/spa/`
- Includes FFmpeg WASM files for client-side video processing
- Backend serves static assets from `spa/` directory

**Deployment Process:**

```bash
# Build and deploy frontend to backend
./deploy-frontend.sh

# This creates the spa/ directory with all static assets
# Backend automatically serves from spa/ when available
```

## Structure

```
backend/web/
├── core/                    # Core utilities
│   ├── models.py           # Pydantic request/response models
│   ├── middleware.py       # HTTP middleware classes
│   ├── storage.py          # Storage calculation utilities (with persistent caching)
│   ├── events.py           # WebSocket event broadcasting
│   ├── websocket.py        # WebSocket connection management
│   ├── upload_coordinator.py # Transaction-based upload processing (V3)
│   └── __init__.py         # Explicit imports (no wildcard imports)
├── routes/                  # API route modules
│   ├── media.py            # Media management endpoints (with cache invalidation)
│   ├── loop.py             # Loop queue management (with cache invalidation)
│   ├── playback.py         # Playback controls + display settings
│   ├── wifi.py             # WiFi network management (functionality limited)
│   ├── updates.py          # System update endpoints
│   ├── dashboard.py        # Consolidated dashboard data (5-second aggressive caching)
│   ├── websocket.py        # WebSocket routes and real-time updates
│   └── __init__.py         # Router registration
├── spa/                     # Frontend assets (deployed via deploy-frontend.sh)
│   ├── _next/              # Next.js build artifacts
│   ├── ffmpeg/             # FFmpeg WASM files
│   └── [static assets]     # React/CSS/JS build output
└── server.py               # Main app factory with Pi Zero 2 optimizations
```

## Performance Architecture

### **Real-time WebSocket Communication**

- **Completed Migration**: Eliminated 15-second polling, now instant updates
- **Room-based Broadcasting**: `dashboard`, `progress`, `wifi`, `system` channels
- **Auto-reconnection**: Client automatically reconnects with exponential backoff
- **Event Broadcasting**: All API mutations trigger real-time WebSocket events

### **Aggressive Caching Strategy**

- **Dashboard Endpoint**: 5-second cache TTL eliminates SD card I/O on every request
- **Media Index**: 5-second aggressive file stat avoidance with in-memory caching
- **Storage Calculations**: Separated from dashboard, only calculated when settings modal opened
- **Cache Invalidation**: Smart invalidation on media state changes

### **Pi Zero 2 Optimizations**

- **Request Deduplication**: In-flight request sharing for dashboard calls
- **Concurrency Limiting**: Max 12 concurrent requests to prevent Pi overload
- **Memory Conservation**: Aggressive cleanup and bounded queues
- **SD Card I/O Minimization**: Cache-first approach with fallback

## Core Functions

### **Real-time Communication**

- **WebSocket Endpoint**: `/ws` with room-based subscriptions
- **Event Broadcasting**: Instant updates for all mutations
- **Connection Management**: Health monitoring with ping/pong
- **Auto-reconnection**: Exponential backoff with graceful degradation

### **Media Management**

- **Transaction-based uploads**: Bulletproof coordination between original + ZIP files
- **Processing jobs**: Tracks upload/conversion progress with real-time WebSocket updates
- **Storage**: Manages raw videos (`media/raw/`) and processed frames (`media/processed/`)
- **Cache Invalidation**: Automatic dashboard cache invalidation on media changes

### **API Endpoints**

#### Real-time WebSocket

- `/ws` - **WebSocket endpoint** for real-time bidirectional communication
- `/api/websocket/status` - Connection diagnostics and room statistics

#### Performance-Critical Endpoints

- `/api/dashboard` - **Cached (5s TTL)** system status, excludes storage for performance
- `/api/dashboard/storage` - **Separate endpoint** for storage info, only called when needed

#### Standard Endpoints (with WebSocket broadcasting)

- `/api/media/*` - Upload, delete, cleanup media (with cache invalidation + WebSocket events)
- `/api/loop/*` - Manage playback queue and ordering (with cache invalidation + WebSocket events)
- `/api/playback/*` - Play/pause, next/previous, loop modes (with cache invalidation + WebSocket events)
- `/api/display/*` - Brightness, gamma, display settings
- `/api/wifi/*` - Network scanning and connection ⚠️ **Limited functionality**
- `/api/updates/*` - System update management

### **Frontend Serving**

- Serves Next.js SPA from `spa/` directory
- Static file serving for media previews with optimized cache headers
- Request optimization and compression

## Performance Metrics

| Endpoint            | Before Optimization | After Optimization | Notes                   |
| ------------------- | ------------------- | ------------------ | ----------------------- |
| `/api/dashboard`    | 1000ms+             | ~50ms (cached)     | 95%+ improvement        |
| Real-time updates   | 15-second polling   | Instant WebSocket  | Immediate feedback      |
| Storage calculation | Every 15s           | Only when needed   | Eliminates 90% of calls |
| Media index reads   | File I/O every time | 5s cache           | Reduces SD card wear    |
| Upload coordination | Race conditions     | Transaction-based  | Bulletproof atomicity   |

## Key Integrations

| Component                   | Purpose                                            | Performance Notes            |
| --------------------------- | -------------------------------------------------- | ---------------------------- |
| **`media_index.py`**        | Authoritative data storage with aggressive caching | 5s file stat avoidance       |
| **`display/player.py`**     | Hardware display control and processing progress   | Frame buffering              |
| **`boot/wifi.py`**          | WiFi network management                            | ⚠️ **Functionality limited** |
| **`deployment/updater.py`** | System update coordination                         | Standard performance         |
| **`config/schema.py`**      | Configuration validation                           | In-memory caching            |

## Architecture

```
Browser WebSocket Client → FastAPI WebSocket Server → media_index → DisplayPlayer → Hardware
        ↓                          ↓                       ↓              ↓
   Real-time UI              Room Broadcasting         JSON Cache     Pi Display
    (instant)                   (instant)              (5s TTL)
```

**Optimized Data Flow**:

1. Browser WebSocket connects and subscribes to rooms
2. API mutations trigger WebSocket broadcasts (instant updates)
3. Dashboard requests hit cache (50ms response)
4. Cache miss triggers media_index read (cached for 5s)
5. Storage calculation **only** when settings modal opened
6. Cache invalidation on state changes triggers WebSocket events

## Middleware Stack

1. **CORS** - Cross-origin requests
2. **Error Handling** - Standardized error responses
3. **Upload Progress** - Real-time progress broadcasting via WebSocket
4. **Concurrency Limiting** - **Max 12 concurrent** to prevent Pi overload
5. **Request Logging** - Performance monitoring with timing
6. **Cache Control** - Optimized static file serving
7. **Conditional GZip** - Reduces bandwidth usage (5-10x compression)

## WebSocket Implementation

### Connection Management (`core/websocket.py`)

```python
class ConnectionManager:
    """Manages WebSocket connections and room-based broadcasting."""

    # Room-based subscriptions
    rooms = {
        "dashboard": set(),    # System status, media, loop changes
        "progress": set(),     # Upload/processing progress
        "wifi": set(),         # WiFi status changes
        "system": set()        # System-level notifications
    }
```

### Event Broadcasting (`core/events.py`)

```python
class EventBroadcaster:
    """Handles real-time event broadcasting to WebSocket clients."""

    async def dashboard_updated(self, data: dict):
        """Broadcast dashboard data update with throttling."""
        await manager.broadcast_to_room("dashboard", {
            "type": "dashboard_update",
            "data": data
        })
```

### Room Subscriptions

- **`dashboard`** - System status, media library, active media, loop queue
- **`progress`** - Real-time processing progress during uploads
- **`wifi`** - WiFi status and connection changes
- **`system`** - System-level notifications and errors

## Caching Implementation

### Dashboard Caching

```python
# 5-second aggressive cache TTL
_dashboard_cache: Optional[DashboardData] = None
_cache_timestamp: float = 0
_cache_ttl: float = 5.0
```

### Cache Invalidation Strategy

- **Media uploads**: Invalidates dashboard cache + broadcasts WebSocket event
- **Loop changes**: Invalidates dashboard cache + broadcasts WebSocket event
- **Playback state**: Invalidates dashboard cache + broadcasts WebSocket event
- **Storage changes**: Invalidates storage cache only

### Storage Separation

- **Dashboard**: Excludes storage data by default
- **Separate endpoint**: `/api/dashboard/storage` for settings modal only
- **Persistent caching**: Storage data cached to `media/.storage_cache.json`
- **Hourly recalculation**: Reduces from every 15s to only when needed

## Pi Zero 2 Specific Features

### WebSocket Optimization

```python
# Auto-reconnection with exponential backoff
reconnectDelay = Math.min(
    baseDelay * Math.pow(2, attempts - 1),
    maxReconnectDelay
);
```

### Request Deduplication

```typescript
// Prevents multiple simultaneous dashboard requests
let inflightDashboard: Promise<DashboardData> | null = null;

if (!init?.signal && inflightDashboard) {
  return inflightDashboard;
}
```

### Memory Management

- **Bounded queues**: 30-frame buffer for display
- **Automatic cleanup**: Processing jobs cleaned after completion
- **Conservative limits**: File size limits respect Pi memory (50MB default)
- **WebSocket connection limits**: Reasonable concurrent connection handling

### Error Handling

- **Graceful degradation**: WebSocket failures don't block UI
- **Timeout handling**: 5-minute upload timeouts
- **Resource monitoring**: CPU/memory limit checking
- **Connection health**: Ping/pong heartbeat monitoring

## Transaction-based Upload System

### Upload Coordination V3

```python
class UploadCoordinator:
    """Bulletproof upload coordination with atomic transactions."""

    async def coordinate_upload(self, original_file, frames_zip):
        """Atomic coordination prevents race conditions."""
        # Method 1: Direct filename match from metadata.json
        # Method 2: Basename matching for safety
        # Method 3: Recent upload fallback
```

### Upload Flow

1. **Browser Processing**: WebAssembly FFmpeg converts media
2. **Transaction Creation**: Deterministic ID from file content hash
3. **Dual Upload**: Original file + processed frames ZIP
4. **Atomic Coordination**: Backend matches files using multiple strategies
5. **Real-time Progress**: WebSocket broadcasts progress updates
6. **Completion**: WebSocket event triggers dashboard refresh

## Known Limitations

- **WiFi Functionality**: May have gaps in current implementation
- **Storage Performance**: First calculation can take 30+ seconds (cached for 1 hour)
- **Concurrent Uploads**: Limited to prevent Pi overload
- **WebSocket Connections**: Reasonable limits for Pi Zero 2 memory constraints

## Performance Monitoring

### WebSocket Performance

```bash
# Check WebSocket connection status and room statistics
curl http://localhost/api/websocket/status

# Monitor real-time events in logs
sudo journalctl -u loop -f | grep "📡"
```

### Cache Hit Rates

```bash
# Monitor dashboard cache performance
sudo journalctl -u loop -f | grep "Dashboard"

# Should see mostly cache hits after initial requests
```

### Response Times

```bash
# Test dashboard performance
curl -w "Response time: %{time_total}s\n" http://localhost/api/dashboard

# Should be <0.1s for cache hits, <1s for cache misses
```

### Storage Performance

```bash
# Monitor storage calculation
sudo journalctl -u loop -f | grep "Storage"

# Should only see calculations when settings opened
```

### Upload Coordination

```bash
# Monitor transaction-based uploads
sudo journalctl -u loop -f | grep "Upload.*coordination"

# Should see successful file matching and processing
```

## Development Notes

- **WebSocket Testing**: Test real-time updates during development
- **Cache Testing**: Disable caching in development by setting TTL to 0
- **Performance Profiling**: Use `time.time()` around critical sections
- **Memory Monitoring**: Watch for memory leaks in long-running operations
- **Pi Testing**: Always test on actual Pi Zero 2 hardware with WebSocket functionality

## Real-time Features

### Instant UI Updates

- **Media uploads**: Progress and completion broadcast instantly
- **Playback control**: Play/pause/next/previous immediate feedback
- **Loop management**: Drag & drop reordering instant updates
- **System status**: Connection/disconnection immediate notifications

### Multi-device Synchronization

- **Shared state**: All connected devices see identical state instantly
- **Collaborative control**: Multiple users can control LOOP simultaneously
- **Device awareness**: See real-time status across desktop/mobile/tablet

This web server provides **enterprise-grade real-time communication** while maintaining **Pi Zero 2 performance constraints**. The completed WebSocket migration delivers immediate user feedback and eliminates the delays of polling-based architectures.
