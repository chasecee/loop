# Web Server

**Performance-optimized** FastAPI web server designed specifically for Pi Zero 2 constraints. Features aggressive caching, storage separation, and minimal SD card I/O.

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

### **Media Management**

- **Two-phase uploads**: Browser uploads video + ZIP frames separately, server coordinates them
- **Processing jobs**: Tracks upload/conversion progress with real-time updates
- **Storage**: Manages raw videos (`media/raw/`) and processed frames (`media/processed/`)
- **Cache Invalidation**: Automatic dashboard cache invalidation on media changes

### **API Endpoints**

#### Performance-Critical Endpoints

- `/api/dashboard` - **Cached (5s TTL)** system status, excludes storage for performance
- `/api/dashboard/storage` - **Separate endpoint** for storage info, only called when needed

#### Standard Endpoints

- `/api/media/*` - Upload, delete, cleanup media (with cache invalidation)
- `/api/loop/*` - Manage playback queue and ordering (with cache invalidation)
- `/api/playback/*` - Play/pause, next/previous, loop modes (with cache invalidation)
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
| Storage calculation | Every 15s           | Only when needed   | Eliminates 90% of calls |
| Media index reads   | File I/O every time | 5s cache           | Reduces SD card wear    |

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
Browser → FastAPI → media_index → DisplayPlayer → Hardware
   ↓         ↓           ↓           ↓
SPA     Cached API   JSON Cache   Pi Display
        (5s TTL)     (5s TTL)
```

**Optimized Data Flow**:

1. Browser request hits cache (50ms response)
2. Cache miss triggers media_index read (cached for 5s)
3. Storage calculation **only** when settings modal opened
4. Cache invalidation on state changes

## Middleware Stack

1. **CORS** - Cross-origin requests
2. **Error Handling** - Standardized error responses
3. **Concurrency Limiting** - **Max 12 concurrent** to prevent Pi overload
4. **Request Logging** - Performance monitoring with timing
5. **Cache Control** - Optimized static file serving
6. **Response Compression** - Reduces bandwidth usage

## Caching Implementation

### Dashboard Caching

```python
# 5-second aggressive cache TTL
_dashboard_cache: Optional[DashboardData] = None
_cache_timestamp: float = 0
_cache_ttl: float = 5.0
```

### Cache Invalidation Strategy

- **Media uploads**: Invalidates dashboard cache
- **Loop changes**: Invalidates dashboard cache
- **Playback state**: Invalidates dashboard cache
- **Storage changes**: Invalidates storage cache only

### Storage Separation

- **Dashboard**: Excludes storage data by default
- **Separate endpoint**: `/api/dashboard/storage` for settings modal only
- **Persistent caching**: Storage data cached to `media/.storage_cache.json`

## Pi Zero 2 Specific Features

### Request Deduplication

```python
# Prevents multiple simultaneous dashboard requests
if not init?.signal && inflightDashboard:
    return inflightDashboard
```

### Memory Management

- **Bounded queues**: 30-frame buffer for display
- **Automatic cleanup**: Processing jobs cleaned after completion
- **Conservative limits**: File size limits respect Pi memory

### Error Handling

- **Graceful degradation**: Cache misses don't block UI
- **Timeout handling**: 5-minute upload timeouts
- **Resource monitoring**: CPU/memory limit checking

## Known Limitations

- **WiFi Functionality**: May have gaps in current implementation
- **Storage Performance**: First calculation can take 30+ seconds
- **Concurrent Uploads**: Limited to prevent Pi overload
- **Cache Persistence**: Dashboard cache lost on restart (by design)

## Performance Monitoring

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

## Development Notes

- **Cache Testing**: Disable caching in development by setting TTL to 0
- **Performance Profiling**: Use `time.time()` around critical sections
- **Memory Monitoring**: Watch for memory leaks in long-running operations
- **Pi Testing**: Always test on actual Pi Zero 2 hardware

This web server is specifically tuned for **Pi Zero 2 constraints** and prioritizes performance above all else.
