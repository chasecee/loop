# Web Server

FastAPI web server (`server.py`) that powers LOOP's web interface and API.

## Core Functions

### **Media Management**

- **Two-phase uploads**: Browser uploads video + ZIP frames separately, server coordinates them
- **Processing jobs**: Tracks upload/conversion progress with real-time updates
- **Storage**: Manages raw videos (`media/raw/`) and processed frames (`media/processed/`)

### **API Endpoints**

- `/api/dashboard` - Consolidated system status (media, playback, WiFi, storage)
- `/api/media/*` - Upload, delete, cleanup media
- `/api/loop/*` - Manage playback queue and ordering
- `/api/playback/*` - Play/pause, next/previous, loop modes
- `/api/wifi/*` - Network scanning and connection
- `/api/updates/*` - System update management

### **Frontend Serving**

- Serves Next.js SPA from `spa/` directory
- Static file serving for media previews
- Cache headers and request optimization

## Key Integrations

| Component                   | Purpose                                          |
| --------------------------- | ------------------------------------------------ |
| **`media_index.py`**        | Authoritative data storage and state management  |
| **`display/player.py`**     | Hardware display control and processing progress |
| **`boot/wifi.py`**          | WiFi network management                          |
| **`deployment/updater.py`** | System update coordination                       |
| **`config/schema.py`**      | Configuration validation                         |

## Architecture

```
Browser → FastAPI → media_index → DisplayPlayer → Hardware
   ↓         ↓           ↓           ↓
SPA     API Routes   JSON File   Pi Display
```

**Data Flow**: Browser converts media → uploads to API → media_index stores metadata → DisplayPlayer reads frames → Pi display shows content

## Middleware Stack

1. **CORS** - Cross-origin requests
2. **Error Handling** - Standardized error responses
3. **Concurrency Limiting** - Prevents Pi overload
4. **Request Logging** - Performance monitoring
5. **Cache Control** - Optimized static file serving
