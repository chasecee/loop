#!/bin/bash

# LOOP WiFi Hotspot Management Script
# This script manages the WiFi hotspot functionality

set -e

HOSTAPD_CONF="/etc/hostapd/hostapd.conf"
HOSTAPD_CONF_LOOP="/etc/hostapd/hostapd.conf.loop"
HOSTAPD_CONF_BACKUP="/etc/hostapd/hostapd.conf.backup"
DNSMASQ_CONF="/etc/dnsmasq.conf"
DNSMASQ_CONF_LOOP="/etc/dnsmasq.conf.loop"
DNSMASQ_CONF_BACKUP="/etc/dnsmasq.conf.backup"

# Default hotspot configuration
DEFAULT_SSID="LOOP-Setup"
DEFAULT_PASSWORD="loop123"
DEFAULT_CHANNEL="7"
HOTSPOT_IP="192.168.4.1"
DHCP_RANGE="192.168.4.2,192.168.4.20"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

create_hostapd_config() {
    local ssid="${1:-$DEFAULT_SSID}"
    local password="${2:-$DEFAULT_PASSWORD}"
    local channel="${3:-$DEFAULT_CHANNEL}"
    
    log "Creating hostapd configuration for $ssid"
    
    cat > "$HOSTAPD_CONF_LOOP" << EOF
interface=wlan0
driver=nl80211
ssid=$ssid
hw_mode=g
channel=$channel
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=$password
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
EOF
}

create_dnsmasq_config() {
    log "Creating dnsmasq configuration"
    
    cat > "$DNSMASQ_CONF_LOOP" << EOF
# LOOP hotspot configuration
interface=wlan0
dhcp-range=$DHCP_RANGE,255.255.255.0,24h
domain=loop.local
address=/#/$HOTSPOT_IP
EOF
}

backup_configs() {
    log "Backing up existing configurations"
    
    if [ -f "$HOSTAPD_CONF" ] && [ ! -f "$HOSTAPD_CONF_BACKUP" ]; then
        cp "$HOSTAPD_CONF" "$HOSTAPD_CONF_BACKUP"
    fi
    
    if [ -f "$DNSMASQ_CONF" ] && [ ! -f "$DNSMASQ_CONF_BACKUP" ]; then
        cp "$DNSMASQ_CONF" "$DNSMASQ_CONF_BACKUP"
    fi
}

restore_configs() {
    log "Restoring original configurations"
    
    if [ -f "$HOSTAPD_CONF_BACKUP" ]; then
        cp "$HOSTAPD_CONF_BACKUP" "$HOSTAPD_CONF"
    fi
    
    if [ -f "$DNSMASQ_CONF_BACKUP" ]; then
        cp "$DNSMASQ_CONF_BACKUP" "$DNSMASQ_CONF"
    fi
}

start_hotspot() {
    local ssid="${1:-$DEFAULT_SSID}"
    local password="${2:-$DEFAULT_PASSWORD}"
    
    log "Starting LOOP WiFi hotspot: $ssid"
    
    # Stop any existing WiFi connections
    systemctl stop wpa_supplicant 2>/dev/null || true
    
    # Backup original configurations
    backup_configs
    
    # Create LOOP configurations
    create_hostapd_config "$ssid" "$password"
    create_dnsmasq_config
    
    # Apply configurations
    cp "$HOSTAPD_CONF_LOOP" "$HOSTAPD_CONF"
    cp "$DNSMASQ_CONF_LOOP" "$DNSMASQ_CONF"
    
    # Configure network interface
    ip addr flush dev wlan0 2>/dev/null || true
    ip addr add ${HOTSPOT_IP}/24 dev wlan0
    ip link set wlan0 up
    
    # Enable IP forwarding
    echo 1 > /proc/sys/net/ipv4/ip_forward
    
    # Set up iptables for captive portal (optional)
    iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE 2>/dev/null || true
    iptables -A FORWARD -i eth0 -o wlan0 -m state --state RELATED,ESTABLISHED -j ACCEPT 2>/dev/null || true
    iptables -A FORWARD -i wlan0 -o eth0 -j ACCEPT 2>/dev/null || true
    
    # Start services
    systemctl start hostapd
    systemctl start dnsmasq
    
    # Wait a moment for services to start
    sleep 2
    
    # Check if services are running
    if systemctl is-active --quiet hostapd && systemctl is-active --quiet dnsmasq; then
        log "✅ Hotspot started successfully!"
        log "   SSID: $ssid"
        log "   Password: $password"
        log "   IP Address: $HOTSPOT_IP"
        log "   Connect to configure WiFi via web interface"
    else
        log "❌ Failed to start hotspot services"
        return 1
    fi
}

stop_hotspot() {
    log "Stopping LOOP WiFi hotspot"
    
    # Stop services
    systemctl stop hostapd 2>/dev/null || true
    systemctl stop dnsmasq 2>/dev/null || true
    
    # Clear iptables rules (best effort)
    iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE 2>/dev/null || true
    iptables -D FORWARD -i eth0 -o wlan0 -m state --state RELATED,ESTABLISHED -j ACCEPT 2>/dev/null || true
    iptables -D FORWARD -i wlan0 -o eth0 -j ACCEPT 2>/dev/null || true
    
    # Reset network interface
    ip addr flush dev wlan0 2>/dev/null || true
    
    # Restore original configurations
    restore_configs
    
    # Restart networking services
    systemctl restart dhcpcd 2>/dev/null || true
    
    log "✅ Hotspot stopped"
}

status() {
    echo "=== LOOP Hotspot Status ==="
    
    # Check service status
    if systemctl is-active --quiet hostapd; then
        echo "📡 hostapd: RUNNING"
    else
        echo "📡 hostapd: STOPPED"
    fi
    
    if systemctl is-active --quiet dnsmasq; then
        echo "🌐 dnsmasq: RUNNING"
    else
        echo "🌐 dnsmasq: STOPPED"
    fi
    
    # Check network interface
    if ip addr show wlan0 | grep -q "$HOTSPOT_IP"; then
        echo "🔌 Interface: wlan0 configured ($HOTSPOT_IP)"
    else
        echo "🔌 Interface: wlan0 not configured for hotspot"
    fi
    
    # Show current SSID if any
    current_ssid=$(grep "ssid=" "$HOSTAPD_CONF" 2>/dev/null | cut -d'=' -f2 || echo "None")
    echo "📶 Current SSID: $current_ssid"
    
    # Show connected clients
    if [ -f /var/lib/dhcp/dhcpd.leases ]; then
        client_count=$(grep -c "binding state active" /var/lib/dhcp/dhcpd.leases 2>/dev/null || echo "0")
        echo "👥 Connected clients: $client_count"
    fi
}

usage() {
    echo "Usage: $0 {start|stop|status|restart} [ssid] [password]"
    echo ""
    echo "Commands:"
    echo "  start [ssid] [password]  - Start hotspot (default: $DEFAULT_SSID)"
    echo "  stop                     - Stop hotspot and restore WiFi"
    echo "  status                   - Show hotspot status"
    echo "  restart [ssid] [pass]    - Restart hotspot"
    echo ""
    echo "Examples:"
    echo "  $0 start                          # Start with default settings"
    echo "  $0 start MyLOOP mypass123         # Start with custom SSID/password"
    echo "  $0 stop                           # Stop hotspot"
    echo "  $0 status                         # Check status"
}

# Main script logic
case "$1" in
    start)
        if [ $EUID -ne 0 ]; then
            echo "❌ This script must be run as root (use sudo)"
            exit 1
        fi
        start_hotspot "$2" "$3"
        ;;
    stop)
        if [ $EUID -ne 0 ]; then
            echo "❌ This script must be run as root (use sudo)"
            exit 1
        fi
        stop_hotspot
        ;;
    restart)
        if [ $EUID -ne 0 ]; then
            echo "❌ This script must be run as root (use sudo)"
            exit 1
        fi
        stop_hotspot
        sleep 2
        start_hotspot "$2" "$3"
        ;;
    status)
        status
        ;;
    *)
        usage
        exit 1
        ;;
esac

exit 0 