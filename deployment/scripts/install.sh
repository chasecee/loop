#!/bin/bash
set -e

# VidBox Installation Script
# This script sets up VidBox on a Raspberry Pi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
SERVICE_NAME="vidbox"
USER="${USER:-pi}"

echo "🎬 VidBox Installation Script"
echo "================================"

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo "⚠️  Warning: This doesn't appear to be a Raspberry Pi"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Update system packages
echo "📦 Updating system packages..."
sudo apt update
sudo apt upgrade -y

# Install system dependencies
echo "🔧 Installing system dependencies..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
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
    libtiff5

# Enable SPI interface
echo "🔌 Enabling SPI interface..."
sudo raspi-config nonint do_spi 0

# Create virtual environment
echo "🐍 Setting up Python virtual environment..."
cd "$PROJECT_DIR"
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "📚 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p media/raw media/processed
mkdir -p logs
mkdir -p ~/.vidbox/logs

# Set up configuration
echo "⚙️  Setting up configuration..."
if [ ! -f config/config.json ]; then
    echo "Creating default configuration..."
    cp config/config.json config/config.json.backup 2>/dev/null || true
fi

# Create systemd service
echo "🔄 Creating systemd service..."
sudo tee /etc/systemd/system/${SERVICE_NAME}.service > /dev/null << EOF
[Unit]
Description=VidBox GIF Player & Uploader
After=network.target
Wants=network.target

[Service]
Type=forking
User=${USER}
Group=${USER}
WorkingDirectory=${PROJECT_DIR}
Environment=PYTHONPATH=${PROJECT_DIR}
ExecStart=${PROJECT_DIR}/venv/bin/python ${PROJECT_DIR}/main.py
ExecReload=/bin/kill -HUP \$MAINPID
KillMode=process
Restart=on-failure
RestartSec=10

# Logging
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=vidbox

[Install]
WantedBy=multi-user.target
EOF

# Set up log rotation
echo "📋 Setting up log rotation..."
sudo tee /etc/logrotate.d/vidbox > /dev/null << EOF
/home/${USER}/.vidbox/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 ${USER} ${USER}
}
EOF

# Set up WiFi hotspot configuration (optional)
echo "📡 Setting up hotspot configuration..."
if [ ! -f /etc/hostapd/hostapd.conf.backup ]; then
    sudo cp /etc/hostapd/hostapd.conf /etc/hostapd/hostapd.conf.backup 2>/dev/null || true
fi

sudo tee /etc/hostapd/hostapd.conf.vidbox > /dev/null << EOF
interface=wlan0
driver=nl80211
ssid=VidBox-Setup
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=vidbox123
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
EOF

# Create hotspot script
echo "🔧 Creating hotspot management script..."
sudo tee /usr/local/bin/vidbox-hotspot > /dev/null << 'EOF'
#!/bin/bash
# VidBox Hotspot Management Script

case "$1" in
    start)
        echo "Starting VidBox hotspot..."
        sudo cp /etc/hostapd/hostapd.conf.vidbox /etc/hostapd/hostapd.conf
        sudo systemctl start hostapd
        sudo systemctl start dnsmasq
        ;;
    stop)
        echo "Stopping VidBox hotspot..."
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

sudo chmod +x /usr/local/bin/vidbox-hotspot

# Set permissions
echo "🔒 Setting file permissions..."
chown -R ${USER}:${USER} "${PROJECT_DIR}"
chmod +x "${PROJECT_DIR}/main.py" 2>/dev/null || true
chmod +x "${PROJECT_DIR}/deployment/scripts/"*.sh 2>/dev/null || true

# Enable and start service
echo "🚀 Enabling and starting VidBox service..."
sudo systemctl daemon-reload
sudo systemctl enable ${SERVICE_NAME}

# Test configuration
echo "🧪 Testing configuration..."
cd "$PROJECT_DIR"
source venv/bin/activate
python -c "from config.schema import Config; print('✅ Configuration test passed')"

# Start the service
echo "▶️  Starting VidBox..."
sudo systemctl start ${SERVICE_NAME}

# Wait a moment and check status
sleep 3
if sudo systemctl is-active --quiet ${SERVICE_NAME}; then
    echo "✅ VidBox service is running!"
    
    # Get the local IP address
    IP_ADDR=$(hostname -I | awk '{print $1}')
    echo ""
    echo "🌐 VidBox is accessible at:"
    echo "   http://${IP_ADDR}:8080"
    echo ""
    echo "📱 If WiFi setup is needed, connect to:"
    echo "   SSID: VidBox-Setup"
    echo "   Password: vidbox123"
    echo ""
else
    echo "❌ Failed to start VidBox service"
    echo "Check the logs with: sudo journalctl -u ${SERVICE_NAME} -f"
    exit 1
fi

echo "🎉 Installation complete!"
echo ""
echo "Useful commands:"
echo "  sudo systemctl status vidbox    # Check service status"
echo "  sudo systemctl restart vidbox   # Restart service"
echo "  sudo journalctl -u vidbox -f    # View logs"
echo "  vidbox-hotspot start            # Start WiFi hotspot"
echo "  vidbox-hotspot stop             # Stop WiFi hotspot"
echo "" 