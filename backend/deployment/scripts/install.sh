#!/bin/bash
set -e

# LOOP Installation Script
# This script sets up LOOP on a Raspberry Pi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../../../" && pwd)"
BACKEND_DIR="${PROJECT_DIR}/backend"
SERVICE_NAME="loop"
USER="${USER:-pi}"
VENV_DIR="${BACKEND_DIR}/venv"
CONFIG_FLAG="${HOME}/.loop/setup_complete"

# Ensure we are running from the project root and backend exists
if [ ! -d "$BACKEND_DIR" ]; then
    echo "❌ backend directory not found at $BACKEND_DIR. Please run this script from the project root (where the backend/ folder is)."
    exit 1
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
    if systemctl list-unit-files | grep -q "^${SERVICE_NAME}.service"; then
        echo "✅ Service already installed"
        return 0
    fi
    return 1
}

echo "🤖 LOOP Installation Script"
echo "================================"

# Add cleanup option
if [ "$1" = "cleanup" ] || [ "$1" = "reset" ]; then
    echo "🧹 CLEANING UP LOOP DATA..."
    
    # Stop service if running
    if systemctl is-active --quiet ${SERVICE_NAME}; then
        echo "🛑 Stopping LOOP service..."
        sudo systemctl stop ${SERVICE_NAME}
    fi
    
    # Clean up media files and index
    echo "🗑️  Removing media files and index..."
    rm -rf "${BACKEND_DIR}/media/raw"/*
    rm -rf "${BACKEND_DIR}/media/processed"/*
    rm -f "${BACKEND_DIR}/media/index.json"
    
    # Recreate directories
    mkdir -p "${BACKEND_DIR}/media/raw" "${BACKEND_DIR}/media/processed"
    
    # Create fresh empty index
    cat > "${BACKEND_DIR}/media/index.json" << 'EOF'
{
  "media": {},
  "loop": [],
  "active": null,
  "last_updated": null,
  "processing": {}
}
EOF
    
    # Clean up logs
    echo "📋 Cleaning up logs..."
    rm -f "${BACKEND_DIR}/logs"/*.log
    rm -f ~/.loop/logs/*.log
    
    # Reset flag
    rm -f "$CONFIG_FLAG"
    
    echo "✅ LOOP data cleaned up!"
    
    # If cleanup only, restart and exit
    if [ "$1" = "cleanup" ]; then
        if systemctl list-unit-files | grep -q "^${SERVICE_NAME}.service"; then
            echo "🔄 Restarting service..."
            sudo systemctl start ${SERVICE_NAME}
        fi
        echo "🎉 Cleanup complete!"
        exit 0
    fi
    
    echo "Continuing with fresh installation..."
fi

# For fresh install, continue with full setup...
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
    git \
    ffmpeg \
    hostapd \
    dnsmasq \
    iptables \
    build-essential \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libopenjp2-7 \
    libtiff-dev

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

# Create necessary directories if they don't exist
echo "📁 Checking directories..."
mkdir -p "${BACKEND_DIR}/media/raw" "${BACKEND_DIR}/media/processed"
mkdir -p "${BACKEND_DIR}/logs"
mkdir -p ~/.loop/logs

# Set up configuration
echo "⚙️ Setting up configuration..."
if [ ! -f "${BACKEND_DIR}/config/config.json" ]; then
    echo "❌ config.json missing! Aborting install."
    exit 1
fi

# Create or update systemd service
echo "🔄 Setting up systemd service..."
sudo tee /etc/systemd/system/${SERVICE_NAME}.service > /dev/null << EOF
[Unit]
Description=LOOP - Little Optical Output Pal
After=network.target
Wants=network.target

[Service]
Type=notify
User=${USER}
Group=${USER}
WorkingDirectory=${BACKEND_DIR}
Environment=PYTHONPATH=${BACKEND_DIR}
Environment=LOOP_ENV=production
ExecStart=${VENV_DIR}/bin/python ${BACKEND_DIR}/main.py
Restart=on-failure
RestartSec=10
StartLimitInterval=300
StartLimitBurst=3

# Permissions for GPIO and system control
SupplementaryGroups=gpio spi i2c dialout video audio plugdev netdev
AmbientCapabilities=CAP_NET_ADMIN CAP_NET_RAW CAP_SYS_ADMIN

# Allow sudo for hotspot management (careful with this)
NoNewPrivileges=false

# Systemd integration
WatchdogSec=60
NotifyAccess=main

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=loop

# Security (balanced with functionality)
PrivateTmp=true
ProtectSystem=false
ProtectHome=false

[Install]
WantedBy=multi-user.target
EOF

# Set up log rotation
echo "📋 Setting up log rotation..."
sudo tee /etc/logrotate.d/loop > /dev/null << EOF
/home/${USER}/.loop/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 ${USER} ${USER}
}
EOF

# Set permissions
echo "🔒 Setting file permissions..."
chown -R ${USER}:${USER} "${PROJECT_DIR}"
chmod +x "${PROJECT_DIR}/backend/main.py" 2>/dev/null || true
chmod +x "${BACKEND_DIR}/deployment/scripts/"*.sh 2>/dev/null || true

# Enable and start service
echo "🚀 Managing LOOP service..."
sudo systemctl daemon-reload
sudo systemctl enable ${SERVICE_NAME}
sudo systemctl restart ${SERVICE_NAME}

# Create flag file to mark setup as complete
mkdir -p "$(dirname "$CONFIG_FLAG")"
touch "$CONFIG_FLAG"

# Wait a moment and check status
sleep 2
if sudo systemctl is-active --quiet ${SERVICE_NAME}; then
    echo "✅ LOOP service is running!"
    
    # Get the local IP address
    IP_ADDR=$(hostname -I | awk '{print $1}')
    echo ""
    echo "🌐 LOOP is accessible at:"
    echo "   http://${IP_ADDR}:8080"
    echo ""
    echo "📱 If WiFi setup is needed, connect to:"
    echo "   SSID: LOOP-Setup"
    echo "   Password: loop123"
    echo ""
else
    echo "❌ Failed to start LOOP service"
    echo "Check the logs with: sudo journalctl -u ${SERVICE_NAME} -f"
    exit 1
fi

echo "🎉 Installation complete!"
echo ""
echo "Useful commands:"
echo "  sudo systemctl status loop    # Check service status"
echo "  sudo systemctl restart loop   # Restart service"
echo "  sudo journalctl -u loop -f    # View logs"
echo "  loop-hotspot start           # Start WiFi hotspot"
echo "  loop-hotspot stop            # Stop WiFi hotspot"

# Set up WiFi hotspot configuration (optional)
echo "📡 Setting up hotspot configuration..."
if [ ! -f /etc/hostapd/hostapd.conf.backup ]; then
    sudo cp /etc/hostapd/hostapd.conf /etc/hostapd/hostapd.conf.backup 2>/dev/null || true
fi

sudo tee /etc/hostapd/hostapd.conf.loop > /dev/null << EOF
interface=wlan0
driver=nl80211
ssid=LOOP-Setup
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=loop123
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
EOF

# Create hotspot script
echo "🔧 Creating hotspot management script..."
sudo tee /usr/local/bin/loop-hotspot > /dev/null << 'EOF'
#!/bin/bash
# LOOP Hotspot Management Script

case "$1" in
    start)
        echo "Starting LOOP hotspot..."
        sudo cp /etc/hostapd/hostapd.conf.loop /etc/hostapd/hostapd.conf
        sudo systemctl start hostapd
        sudo systemctl start dnsmasq
        ;;
    stop)
        echo "Stopping LOOP hotspot..."
        sudo systemctl stop hostapd
        sudo systemctl stop dnsmasq
        sudo cp /etc/hostapd/hostapd.conf.backup /etc/hostapd/hostapd.conf 2>/dev/null || true
        ;;
    *)
        echo "Usage: $0 {start|stop}"
        exit 1
        ;;
esac
EOF

sudo chmod +x /usr/local/bin/loop-hotspot

# Import default media if present and no media exists yet
if [ -d "$PROJECT_DIR/assets/default-media" ]; then
    echo "📦 Importing default media from assets/default-media..."
    cp -r "$PROJECT_DIR/assets/default-media"/* "$BACKEND_DIR/media/processed/" 2>/dev/null || true
    
    INDEX_FILE="$BACKEND_DIR/media/index.json"
    if [ ! -f "$INDEX_FILE" ] || [ ! -s "$INDEX_FILE" ]; then
        echo "📝 Generating media index from default media..."
        
        # Create initial empty index in the new clean format
        cat > "$INDEX_FILE" << EOF
{
  "media": {},
  "loop": [],
  "active": null,
  "last_updated": $(date +%s)
}
EOF
        
        # Add any processed media to the index
        for media_dir in "$BACKEND_DIR/media/processed"/*; do
            if [ -d "$media_dir" ]; then
                SLUG_NAME=$(basename "$media_dir")
                META_FILE="$media_dir/metadata.json"
                
                if [ -f "$META_FILE" ]; then
                    echo "📄 Adding $SLUG_NAME to media index..."
                    
                    # Use Python to properly merge the metadata
                    python3 -c "
import json
import sys
from pathlib import Path

# Load current index
with open('$INDEX_FILE', 'r') as f:
    index = json.load(f)

# Load metadata
with open('$META_FILE', 'r') as f:
    metadata = json.load(f)

# Add to media dict and loop
slug = metadata.get('slug', '$SLUG_NAME')
index['media'][slug] = metadata
if slug not in index['loop']:
    index['loop'].append(slug)

# Set as active if it's the first one
if not index['active']:
    index['active'] = slug

# Write back
with open('$INDEX_FILE', 'w') as f:
    json.dump(index, f, indent=2)
" 2>/dev/null || echo "⚠️  Could not add $SLUG_NAME to index (metadata format issue)"
                fi
            fi
        done
        
        echo "✅ Default media index created with $(ls -1d "$BACKEND_DIR/media/processed"/*/ 2>/dev/null | wc -l) items"
    fi
fi

# -----------------------------------------------------------------------------
# Install display dependencies and configure DRM
# -----------------------------------------------------------------------------
echo "📦 Installing display dependencies..."
if ! sudo apt-get install -y libjpeg-dev libopenjp2-7 libtiff6; then
    echo "❌ Failed to install display dependencies."
    exit 1
fi

echo "⚙️ Configuring DRM for ILI9341 display (Bookworm method)..."
CONFIG_FILE="/boot/firmware/config.txt"

# Ensure config file exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ $CONFIG_FILE not found. This script is intended for Raspberry Pi OS."
    exit 1
fi

# Add DRM overlay for the 2.4" screen
# This tells the kernel to drive the SPI display directly.
sudo cat >> "$CONFIG_FILE" <<EOF

# LOOP Display Configuration (ILI9341)
dtoverlay=vc4-kms-v3d
dtoverlay=waveshare24b,speed=48000000,fps=60
EOF

echo "✅ DRM display overlay configured in $CONFIG_FILE."
echo "⚠️  A reboot is required for display changes to take effect."

# -----------------------------------------------------------------------------
# Install Python dependencies
# -----------------------------------------------------------------------------
# Go back to project root
cd "$PROJECT_DIR"

# ... existing code ... 