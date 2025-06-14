#!/bin/bash
set -e

# LOOP Installation Script
# This script sets up LOOP on a Raspberry Pi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
SERVICE_NAME="loop"
USER="${USER:-pi}"
VENV_DIR="${PROJECT_DIR}/venv"
CONFIG_FLAG="${HOME}/.loop/setup_complete"

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

# Function to check if SPI is enabled
check_spi() {
    if grep -q "^dtparam=spi=on" /boot/config.txt || lsmod | grep -q "^spi_"; then
        echo "✅ SPI already enabled"
        return 0
    fi
    return 1
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

# Check if this is a reinstall
if [ -f "$CONFIG_FLAG" ]; then
    echo "🔄 Detected previous installation"
    echo "Performing quick update..."
    
    # Just update Python packages and restart service
    if [ -f "${PROJECT_DIR}/requirements.txt" ]; then
        echo "📚 Updating Python dependencies..."
        source "${VENV_DIR}/bin/activate"
        pip install -r "${PROJECT_DIR}/requirements.txt"
    fi
    
    # Restart service if it exists
    if check_service; then
        echo "🔄 Restarting service..."
        sudo systemctl restart ${SERVICE_NAME}
        
        # Show IP and exit
        IP_ADDR=$(hostname -I | awk '{print $1}')
        echo ""
        echo "🌐 LOOP is accessible at:"
        echo "   http://${IP_ADDR}:8080"
    fi
    
    echo "✨ Quick update complete!"
    exit 0
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

# Update package list (but don't upgrade everything)
echo "📦 Updating package list..."
sudo apt update

# Install system dependencies only if missing
echo "🔧 Checking system dependencies..."
install_missing_packages \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    python3-opencv \
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

# Enable SPI interface if needed
if ! check_spi; then
    echo "🔌 Enabling SPI interface..."
    sudo raspi-config nonint do_spi 0
fi

# Create virtual environment if needed
if ! check_venv; then
    echo "🐍 Setting up Python virtual environment..."
    cd "$PROJECT_DIR"
    python3 -m venv venv
fi

# Always update Python dependencies
echo "📚 Installing Python dependencies..."
cd "$PROJECT_DIR"
source venv/bin/activate
pip install --upgrade pip

# First install system-level OpenCV to avoid building from source
echo "🔧 Installing OpenCV from system packages..."
sudo apt-get install -y python3-opencv

# Use binary packages where possible and avoid building from source
echo "📦 Installing remaining Python packages..."
export PIP_PREFER_BINARY=1
export PIP_ONLY_BINARY=numpy,opencv-python
pip install --no-cache-dir -r requirements.txt

# Create necessary directories if they don't exist
echo "📁 Checking directories..."
mkdir -p media/raw media/processed
mkdir -p logs
mkdir -p ~/.loop/logs

# Set up configuration
echo "⚙️  Setting up configuration..."
if [ ! -f config/config.json ]; then
    echo "Creating default configuration..."
    cp config/config.json.example config/config.json 2>/dev/null || true
fi

# Create systemd service if needed
if ! check_service; then
    echo "🔄 Creating systemd service..."
    sudo tee /etc/systemd/system/${SERVICE_NAME}.service > /dev/null << EOF
[Unit]
Description=LOOP - Little Optical Output Pal
After=network.target

[Service]
Type=simple
User=${USER}
Group=${USER}
WorkingDirectory=${PROJECT_DIR}
Environment=PYTHONPATH=${PROJECT_DIR}
ExecStart=${VENV_DIR}/bin/python ${PROJECT_DIR}/main.py
Restart=always
RestartSec=3

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
fi

# Set permissions
echo "🔒 Setting file permissions..."
chown -R ${USER}:${USER} "${PROJECT_DIR}"
chmod +x "${PROJECT_DIR}/main.py" 2>/dev/null || true
chmod +x "${PROJECT_DIR}/deployment/scripts/"*.sh 2>/dev/null || true

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