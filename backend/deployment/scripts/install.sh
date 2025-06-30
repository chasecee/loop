#!/bin/bash
set -e

# LOOP Installation Script
# This script sets up LOOP on a Raspberry Pi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../../../" && pwd)"
BACKEND_DIR="${PROJECT_DIR}/backend"
SERVICE_NAME="loop"
# Get the real user even when running under sudo
REAL_USER="${SUDO_USER:-${USER:-pi}}"
USER="$REAL_USER"
VENV_DIR="${BACKEND_DIR}/venv"
CONFIG_FLAG="/home/${REAL_USER}/.loop/setup_complete"

# Ensure we are running from the project root and backend exists
if [ ! -d "$BACKEND_DIR" ]; then
    echo "❌ backend directory not found at $BACKEND_DIR. Please run this script from the project root (where the backend/ folder is)."
    exit 1
fi

# Fix ownership issues from previous sudo runs - do this early
echo "🔧 Fixing any ownership issues from previous installs..."
if [ "$EUID" -ne 0 ]; then
    # Running as non-root user, try to fix ownership with sudo
    if command -v sudo >/dev/null 2>&1; then
        sudo chown -R "${REAL_USER}:${REAL_USER}" "${PROJECT_DIR}" 2>/dev/null || {
            echo "⚠️  Could not fix ownership automatically. If you get permission errors, run:"
            echo "   sudo chown -R ${REAL_USER}:${REAL_USER} ${PROJECT_DIR}"
            echo "   Then re-run this script."
        }
    fi
else
    # Running as root, fix ownership directly
    chown -R "${REAL_USER}:${REAL_USER}" "${PROJECT_DIR}" 2>/dev/null || true
fi

# Function to check if a package is installed
check_package() {
    dpkg -l "$1" &> /dev/null
    return $?
}

# Function to install missing packages
install_missing_packages() {
    local missing_pkgs=()
    
    # Check each package
    for pkg in "$@"; do
        if ! check_package "$pkg"; then
            missing_pkgs+=("$pkg")
        fi
    done
    
    # Install only missing packages
    if [ ${#missing_pkgs[@]} -ne 0 ]; then
        echo "📦 Installing missing packages: ${missing_pkgs[*]}"
        sudo apt install -y "${missing_pkgs[@]}"
    else
        echo "✅ All required packages already installed"
    fi
}

# Function to check Python venv
check_venv() {
    if [ -f "${VENV_DIR}/bin/python" ] && [ -f "${VENV_DIR}/bin/pip" ]; then
        echo "✅ Python virtual environment exists"
        return 0
    fi
    return 1
}

# Function to check if service is installed
check_service() {
    local service_name="$1"
    if systemctl list-unit-files | grep -q "^${service_name}.service"; then
        echo "✅ ${service_name} service already installed"
        return 0
    fi
    return 1
}

echo "🤖 LOOP Installation Script"
echo "================================"

# Installation script continues...

# Add cleanup option
if [ "$1" = "cleanup" ] || [ "$1" = "reset" ]; then
    echo "🧹 CLEANING UP LOOP DATA..."
    
    # Stop service if running
    if systemctl is-active --quiet ${SERVICE_NAME}; then
        echo "🛑 Stopping LOOP service..."
        sudo systemctl stop ${SERVICE_NAME}
    fi
    
    # Clean up media files and databases
    echo "🗑️  Removing media files and databases..."
    rm -rf "${BACKEND_DIR}/media/raw"/*
    rm -rf "${BACKEND_DIR}/media/processed"/*
    rm -f "${BACKEND_DIR}/media/index.json"  # Remove legacy JSON file
    rm -f "${BACKEND_DIR}/media/media.db"    # Remove SQLite database
    rm -f "${BACKEND_DIR}/media/media.db-wal"  # Remove WAL file
    rm -f "${BACKEND_DIR}/media/media.db-shm"  # Remove shared memory file
    
    # Recreate directories (SQLite database will be created automatically on first run)
    mkdir -p "${BACKEND_DIR}/media/raw" "${BACKEND_DIR}/media/processed"
    
    # Clean up logs
    echo "📋 Cleaning up logs..."
    rm -f "${BACKEND_DIR}/logs"/*.log
    rm -f "/home/${REAL_USER}/.loop/logs"/*.log
    
    # Reset flag
    rm -f "$CONFIG_FLAG"
    
    echo "✅ LOOP data cleaned up!"
    
    # If cleanup only, restart and exit
    if [ "$1" = "cleanup" ]; then
        if check_service "${SERVICE_NAME}"; then
            echo "🔄 Restarting service..."
            sudo systemctl start ${SERVICE_NAME}
        fi
        echo "🎉 Cleanup complete!"
        exit 0
    fi
    
    echo "Continuing with fresh installation..."
fi

# For fresh install, continue with full setup...
# Stop service if it is running to ensure clean installation
if check_service "${SERVICE_NAME}"; then
    if systemctl is-active --quiet ${SERVICE_NAME}; then
        echo "🛑 Stopping running LOOP service before installation..."
        sudo systemctl stop ${SERVICE_NAME}
        echo "✅ Service stopped."
    fi
fi

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo "⚠️  Warning: This doesn't appear to be a Raspberry Pi"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Update and upgrade system
echo "🔄 Updating system packages..."
sudo apt update
sudo apt upgrade -y

# Install system dependencies only if missing
echo "🔧 Checking system dependencies..."
install_missing_packages \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    python3-rpi.gpio \
    python3-gpiozero \
    git \
    ffmpeg \
    network-manager \
    build-essential \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libopenjp2-7 \
    libtiff-dev \
    libopenblas0 \
    libopenblas-dev \
    liblapack-dev \
    iw \
    wireless-tools \
    avahi-utils

# Set Boot Config path based on OS version
if [ -f /boot/firmware/config.txt ]; then
    BOOT_CONFIG_FILE="/boot/firmware/config.txt"
else
    BOOT_CONFIG_FILE="/boot/config.txt"
fi

# Enable SPI interface if needed
echo "🔌 Checking SPI interface..."
if ! grep -q -E "^dtparam=spi=on" "$BOOT_CONFIG_FILE"; then
    echo "   SPI not enabled. Enabling now..."
    echo "# Enable SPI for LOOP hardware" | sudo tee -a "$BOOT_CONFIG_FILE"
    echo "dtparam=spi=on" | sudo tee -a "$BOOT_CONFIG_FILE"
    echo "✅ SPI enabled. A reboot will be required."
else
    echo "✅ SPI is already enabled in $BOOT_CONFIG_FILE."
fi

# Create virtual environment if needed
if ! check_venv; then
    echo "🐍 Setting up Python virtual environment..."
    cd "$BACKEND_DIR"
    python3 -m venv venv --system-site-packages
fi

# Always update Python dependencies
echo "📚 Installing Python dependencies..."
cd "$BACKEND_DIR"
source venv/bin/activate
pip install --upgrade pip

# Use binary packages where possible and avoid building from source
echo "📦 Installing Python packages..."
export PIP_PREFER_BINARY=1
export PIP_ONLY_BINARY=numpy
pip install --no-cache-dir -r requirements.txt

# Install additional required packages that might not be in requirements.txt
echo "📦 Installing additional web dependencies..."
pip install --no-cache-dir python-multipart

# Create necessary directories if they don't exist
echo "📁 Checking directories..."
mkdir -p "${BACKEND_DIR}/media/raw" "${BACKEND_DIR}/media/processed"
mkdir -p "${BACKEND_DIR}/logs"
mkdir -p "/home/${REAL_USER}/.loop/logs"

# Set ownership immediately to prevent permission issues
chown -R "${REAL_USER}:${REAL_USER}" "${BACKEND_DIR}/media" "${BACKEND_DIR}/logs" "/home/${REAL_USER}/.loop" 2>/dev/null || true

# Set up configuration
echo "⚙️ Setting up configuration..."
if [ ! -f "${BACKEND_DIR}/config/config.json" ]; then
    echo "❌ config.json missing! Aborting install."
    exit 1
fi

# Configure minimal WiFi management permissions  
echo "🔐 Configuring minimal WiFi permissions..."

# Add user ONLY to groups actually needed by LOOP hardware
echo "👥 Adding user ${REAL_USER} to minimal required groups..."
sudo usermod -a -G gpio,spi "${REAL_USER}"

# Create SCOPED NetworkManager PolicyKit rule - WiFi ONLY
POLKIT_FILE="/etc/polkit-1/localauthority/50-local.d/50-loop-wifi-only.pkla"
sudo tee "$POLKIT_FILE" > /dev/null << EOF
[Allow ${REAL_USER} to manage WiFi only]
Identity=unix-user:${REAL_USER}
Action=org.freedesktop.NetworkManager.wifi.*;org.freedesktop.NetworkManager.settings.modify.own;org.freedesktop.NetworkManager.network-control
ResultAny=yes
ResultInactive=yes
ResultActive=yes
EOF

# PolicyKit file created - user can remove manually if needed

echo "✅ Minimal WiFi permissions configured for user ${REAL_USER}"

# Generate service files using safe envsubst substitution
echo "📝 Generating service files with safe substitution..."

# Check if envsubst is available (part of gettext-base package)
if ! command -v envsubst >/dev/null 2>&1; then
    echo "📦 Installing envsubst for safe template substitution..."
    sudo apt install -y gettext-base
fi

# Export variables for envsubst (escapes special characters automatically)
export LOOP_USER="${REAL_USER}"
export LOOP_PROJECT_DIR="${PROJECT_DIR}"

# Generate loop.service using envsubst (safe substitution)
if [ -f "${BACKEND_DIR}/loop.service" ]; then
    # Create backup first
    cp "${BACKEND_DIR}/loop.service" "${BACKEND_DIR}/loop.service.backup"
    
    # Use envsubst for safe variable substitution
    envsubst '$LOOP_USER $LOOP_PROJECT_DIR' < "${BACKEND_DIR}/loop.service.backup" > "${BACKEND_DIR}/loop.service"
    echo "✅ Generated loop.service for user ${REAL_USER} using safe envsubst"
else
    echo "❌ loop.service not found!"
    exit 1
fi

# Generate system-management.service using envsubst
if [ -f "${BACKEND_DIR}/system-management.service" ]; then
    # Create backup first
    cp "${BACKEND_DIR}/system-management.service" "${BACKEND_DIR}/system-management.service.backup"
    
    # Use envsubst for safe variable substitution
    envsubst '$LOOP_PROJECT_DIR' < "${BACKEND_DIR}/system-management.service.backup" > "${BACKEND_DIR}/system-management.service"
    echo "✅ Generated system-management.service with safe paths"
fi

# Clean up environment variables
unset LOOP_USER LOOP_PROJECT_DIR

# Install system services using dedicated service manager
echo "🚀 Installing system services..."
"${SCRIPT_DIR}/service-manager.sh" install

# Set up log rotation
echo "📋 Setting up log rotation..."
sudo tee /etc/logrotate.d/loop > /dev/null << EOF
/home/${REAL_USER}/.loop/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 ${REAL_USER} ${REAL_USER}
}
EOF

# Set permissions
echo "🔒 Setting file permissions..."
chown -R ${REAL_USER}:${REAL_USER} "${PROJECT_DIR}"
chmod +x "${PROJECT_DIR}/backend/main.py" 2>/dev/null || true
chmod +x "${BACKEND_DIR}/deployment/scripts/"*.sh 2>/dev/null || true
chmod +x "${BACKEND_DIR}/boot/boot-display.py" 2>/dev/null || true

# Bookworm-specific: Ensure proper systemd user session configuration
echo "🎛️ Configuring systemd user session for Bookworm..."
sudo loginctl enable-linger "${REAL_USER}" 2>/dev/null || true

# Bookworm-specific: Minimal GPIO permissions (only if needed)
echo "🔧 Checking GPIO permissions for Pi Zero 2 W + Bookworm..."

# Check if LOOP-specific udev rules are needed
if [ ! -f /etc/udev/rules.d/99-gpio.rules ] && [ ! -f /etc/udev/rules.d/99-spi.rules ]; then
    echo "   Creating minimal LOOP GPIO permissions..."
    sudo tee /etc/udev/rules.d/99-loop-spi-only.rules > /dev/null << EOF
# Minimal SPI access for LOOP display only
KERNEL=="spidev0.0", GROUP="spi", MODE="0664"
EOF
    
    # Reload udev rules
    sudo udevadm control --reload-rules
    sudo udevadm trigger
    
    echo "✅ Minimal SPI permissions configured"
else
    echo "✅ System GPIO rules already exist - skipping to avoid conflicts"
fi

# Services already installed and started by install_services function

# Create flag file to mark setup as complete
mkdir -p "$(dirname "$CONFIG_FLAG")"
touch "$CONFIG_FLAG"
chown "${REAL_USER}:${REAL_USER}" "$CONFIG_FLAG" "$(dirname "$CONFIG_FLAG")" 2>/dev/null || true

# Test the application can start with all dependencies
echo "🧪 Testing application startup..."
cd "$BACKEND_DIR"
if timeout 10s "${VENV_DIR}/bin/python" -c "
import psutil
import sys
sys.path.insert(0, '.')
try:
    from web.server import create_app
    print('✅ All dependencies available')
except ImportError as e:
    print(f'❌ Missing dependency: {e}')
    exit(1)
" 2>/dev/null; then
    echo "✅ Application dependencies verified"
else
    echo "❌ Application dependency test failed - installing missing packages..."
    source venv/bin/activate
    pip install --no-cache-dir python-multipart
fi

# Check if user has required groups (more reliable check)
echo "🔍 Verifying group memberships..."
MISSING_GROUPS=()

# Check each required group individually (more reliable than string matching)
if ! getent group gpio | grep -q "\b${REAL_USER}\b"; then
    MISSING_GROUPS+=("gpio")
fi

if ! getent group spi | grep -q "\b${REAL_USER}\b"; then
    MISSING_GROUPS+=("spi")
fi

if [ ${#MISSING_GROUPS[@]} -ne 0 ]; then
    echo ""
    echo "⚠️  IMPORTANT: New group memberships require logout/login to activate"
    echo "   Missing groups for ${REAL_USER}: ${MISSING_GROUPS[*]}"
    echo "   Current active groups: $(groups)"
    echo ""
    echo "   To activate changes:"
    echo "   1. Logout and login again, OR"
    echo "   2. Reboot the Pi"
    echo "   3. Then restart service: sudo systemctl restart ${SERVICE_NAME}"
    echo ""
else
    echo "✅ All required group memberships are active"
fi

# Wait a moment and check status
sleep 2
if sudo systemctl is-active --quiet ${SERVICE_NAME}; then
    echo "✅ LOOP service is running!"
    
    # Wait for a valid IP address
    echo "⌛ Waiting for network connection..."
    IP_ADDR=""
    for i in {1..15}; do
        IP_ADDR=$(hostname -I | awk '{print $1}')
        if [[ -n "$IP_ADDR" && "$IP_ADDR" != "192.168.24.1" ]]; then
            echo "✅ Network connected."
            break
        fi
        sleep 1
    done

    echo ""
    if [[ -n "$IP_ADDR" && "$IP_ADDR" != "192.168.24.1" ]]; then
        echo "🌐 LOOP is accessible at: http://${IP_ADDR}"
    else
        echo "⚠️  Could not determine IP address. Please check your network or connect to the hotspot if enabled."
        echo "   Default Hotspot SSID: LOOP-Setup"
    fi
    echo ""
else
    echo "❌ Failed to start LOOP service"
    echo "Check the logs with: sudo journalctl -u ${SERVICE_NAME} -f"
    exit 1
fi

# Installation completed successfully

echo "🎉 Installation complete!"
echo ""
echo "Useful commands:"
echo "  sudo systemctl status loop              # Check main service status"
echo "  sudo systemctl restart loop             # Restart main service"
echo "  sudo journalctl -u loop -f              # View main service logs"
echo "  sudo systemctl status boot-display      # Check boot display service"
echo "  ${SCRIPT_DIR}/service-manager.sh check  # Check all LOOP services"
echo "  # WiFi/hotspot managed via web interface at http://IP"
echo ""
echo "🔧 Diagnostic commands:"
echo "  # Check Python dependencies"
echo "  ${BACKEND_DIR}/venv/bin/pip list | grep -E '(fastapi|uvicorn|pillow|multipart)'"
echo ""
echo "  # Test polling endpoints"
echo "  curl -s http://localhost/api/poll/health | jq ."
echo ""
echo "  # Monitor system status"
echo "  curl -s http://localhost/api/poll/status | jq .data.player"
echo ""
echo "  # Check WiFi power management status (replace wlan0 with your interface)"
echo "  iw dev wlan0 get power_save"
echo "  iwconfig wlan0 | grep 'Power Management'"
echo ""
echo "  # Check mDNS resolution (should resolve to loop.local)"
echo "  getent hosts loop.local"
echo "  avahi-resolve -n loop.local"

# WiFi management is now handled by NetworkManager through the web interface
echo "WiFi and hotspot management is handled through the web interface"

# SQLite database will be created automatically on first application startup
echo "📝 SQLite database will be initialized automatically on first run at: media/media.db"

# -----------------------------------------------------------------------------
# Install display dependencies and configure DRM
# -----------------------------------------------------------------------------
# This entire section is now obsolete and has been removed.
# The application now uses a self-contained, user-space Python driver from the 
# 'waveshare' directory that communicates directly with the hardware via SPI.
# This approach removes the need for a kernel framebuffer driver (DRM/dtoverlay)
# and resolves issues related to the missing 'waveshare24b.dtbo' overlay file.

# -----------------------------------------------------------------------------
# Install Python dependencies
# -----------------------------------------------------------------------------
# Go back to project root
cd "$PROJECT_DIR"

# ... existing code ... 