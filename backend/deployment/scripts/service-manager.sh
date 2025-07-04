#!/bin/bash
set -e

# LOOP Service Manager
# Handles installation and management of systemd services

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../../../" && pwd)"
BACKEND_DIR="${PROJECT_DIR}/backend"

# Function to check if service is installed
check_service() {
    local service_name="$1"
    if systemctl list-unit-files | grep -q "^${service_name}.service"; then
        echo "${service_name} service already installed"
        return 0
    fi
    return 1
}

# Function to install and manage system services
install_services() {
    local services=(
        "boot/boot-display:boot-display"
        "loop:loop"
        "system-management:system-management"
    )
    
    echo "Installing system services..."
    
    for service_pair in "${services[@]}"; do
        local service_file="${service_pair%%:*}"
        local service_name="${service_pair##*:}"
        local service_path="${BACKEND_DIR}/${service_file}.service"
        
        if [ -f "$service_path" ]; then
            echo "Installing ${service_name}.service..."
            # Substitute placeholders with actual values
            sed -e "s|__USER__|$(whoami)|g" \
                -e "s|__PROJECT_DIR__|${PROJECT_DIR}|g" \
                "$service_path" | sudo tee "/etc/systemd/system/${service_name}.service" > /dev/null
        else
            echo "Warning: ${service_path} not found, skipping..."
        fi
    done
    
    # WiFi setup is now handled by this script's setup-wifi command
    
    # Reload systemd and manage services
    sudo systemctl daemon-reload
    
    # Enable boot display service (but don't start - it runs at boot)
    if [ -f "/etc/systemd/system/boot-display.service" ]; then
        sudo systemctl enable boot-display
        echo "Boot display service enabled - will run at next boot"
    fi
    
    # Enable and start main loop service
    sudo systemctl enable loop
    sudo systemctl restart loop
    
    # Enable system management service (but don't restart - it's oneshot)
    if [ -f "/etc/systemd/system/system-management.service" ]; then
        sudo systemctl enable system-management
        echo "System management service enabled"
    fi
}

# Function to get WiFi interface name
get_wifi_interface() {
    # Try common interface names
    for iface in wlan0 wlp0s1 wlx*; do
        if [ -d "/sys/class/net/$iface" ] && [ -d "/sys/class/net/$iface/wireless" ]; then
            echo "$iface"
            return 0
        fi
    done
    
    # Fallback: use iw to find wireless interfaces
    if command -v iw >/dev/null 2>&1; then
        iw dev | grep Interface | head -1 | awk '{print $2}'
    else
        echo "wlan0"  # Default fallback
    fi
}

# Function to setup WiFi power management and permissions
setup_wifi_power_management() {
    local wifi_iface
    wifi_iface=$(get_wifi_interface)
    
    echo "Setting up WiFi power management for interface: $wifi_iface" | logger -t loop-wifi-setup
    
    # Create NetworkManager configuration directory
    sudo mkdir -p /etc/NetworkManager/conf.d
    
    # Create NetworkManager configuration to disable WiFi power saving
    local nm_config="/etc/NetworkManager/conf.d/default-wifi-powersave-off.conf"
    if [ -f "$nm_config" ] && grep -q "wifi.powersave = 2" "$nm_config" 2>/dev/null; then
        echo "NetworkManager power save configuration already exists and is correct" | logger -t loop-wifi-setup
    else
        echo "Creating/updating NetworkManager power save configuration" | logger -t loop-wifi-setup
        sudo tee "$nm_config" > /dev/null << EOF
[connection]
wifi.powersave = 2
EOF
        echo "Created NetworkManager power save configuration" | logger -t loop-wifi-setup
    fi
    
    # Setup NetworkManager permissions for LOOP service
    echo "Setting up NetworkManager permissions for LOOP..." | logger -t loop-wifi-setup
    
    # Create polkit rule for NetworkManager access (Pi Zero 2 Bookworm tested)
    sudo mkdir -p /etc/polkit-1/localauthority/50-local.d
    local polkit_file="/etc/polkit-1/localauthority/50-local.d/org.freedesktop.NetworkManager.pkla"
    
    if [ -f "$polkit_file" ] && grep -q "Identity=unix-user:pi" "$polkit_file" 2>/dev/null && grep -q "NetworkManager.settings.modify.system" "$polkit_file" 2>/dev/null; then
        echo "NetworkManager polkit rules already exist and are correct" | logger -t loop-wifi-setup
    else
        echo "Creating/updating NetworkManager polkit rules" | logger -t loop-wifi-setup
        sudo tee "$polkit_file" > /dev/null << 'EOF'
[Allow NetworkManager for pi user]
Identity=unix-user:pi
Action=org.freedesktop.NetworkManager.settings.modify.system;org.freedesktop.NetworkManager.settings.modify.own;org.freedesktop.NetworkManager.settings.modify.hostname;org.freedesktop.NetworkManager.enable-disable-network;org.freedesktop.NetworkManager.enable-disable-wifi;org.freedesktop.NetworkManager.sleep-wake;org.freedesktop.NetworkManager.network-control;org.freedesktop.NetworkManager.wifi.share.protected;org.freedesktop.NetworkManager.wifi.share.open
ResultAny=yes
ResultInactive=yes
ResultActive=yes
EOF
        echo "Created polkit rules for NetworkManager access" | logger -t loop-wifi-setup
    fi
    
    # Restart polkit to apply new rules
    if sudo systemctl restart polkit 2>/dev/null; then
        echo "Polkit restarted successfully" | logger -t loop-wifi-setup
    else
        echo "Failed to restart polkit - rules will apply on next boot" | logger -t loop-wifi-setup
    fi
    
    # Reload NetworkManager to apply changes
    if sudo systemctl reload NetworkManager 2>/dev/null; then
        echo "NetworkManager reloaded successfully" | logger -t loop-wifi-setup
    else
        echo "Failed to reload NetworkManager" | logger -t loop-wifi-setup
    fi
    
    # Wait for NetworkManager to apply changes
    sleep 3
    
    # Check final power management status
    if command -v iwconfig >/dev/null 2>&1; then
        iwconfig "$wifi_iface" 2>/dev/null | grep -i power | logger -t loop-wifi-setup || true
    fi
    
    if command -v iw >/dev/null 2>&1; then
        POWER_STATUS=$(iw dev "$wifi_iface" get power_save 2>/dev/null || echo "unknown")
        echo "Final power save status on $wifi_iface: $POWER_STATUS" | logger -t loop-wifi-setup
    fi
    
    echo "WiFi power management and permissions setup completed for $wifi_iface" | logger -t loop-wifi-setup
}

# Function to verify WiFi power management and permissions
check_wifi_power_management() {
    local wifi_iface
    wifi_iface=$(get_wifi_interface)
    
    if [ -z "$wifi_iface" ]; then
        echo "No WiFi interface found"
        return 1
    fi
    
    # Check power management
    if command -v iw >/dev/null 2>&1; then
        echo "Checking WiFi power management on $wifi_iface..."
        POWER_SAVE=$(iw dev "$wifi_iface" get power_save 2>/dev/null | cut -d: -f2 | tr -d ' ')
        if [ "$POWER_SAVE" = "off" ]; then
            echo "✅ WiFi power save disabled on $wifi_iface - mDNS should work properly"
        else
            echo "⚠️  WiFi power save still enabled on $wifi_iface - may affect mDNS discovery"
        fi
    else
        echo "iw command not available, cannot check WiFi power management"
    fi
    
    # Check NetworkManager permissions
    if [ -f "/etc/polkit-1/localauthority/50-local.d/org.freedesktop.NetworkManager.pkla" ]; then
        echo "✅ NetworkManager permissions configured"
    else
        echo "❌ NetworkManager permissions not configured"
        return 1
    fi
    
    # Test NetworkManager access (non-destructive)
    if command -v nmcli >/dev/null 2>&1; then
        if nmcli device status >/dev/null 2>&1; then
            echo "✅ NetworkManager access working"
            return 0
        else
            echo "❌ NetworkManager access failed - insufficient privileges"
            return 1
        fi
    else
        echo "nmcli command not available"
        return 1
    fi
}

# Main function
main() {
    case "${1:-install}" in
        install)
            install_services
            setup_wifi_power_management
            check_wifi_power_management
            ;;
        check)
            check_service "boot-display"
            check_service "loop"
            check_service "system-management" 
            check_wifi_power_management
            ;;
        setup-wifi)
            setup_wifi_power_management
            ;;
        *)
            echo "Usage: $0 {install|check|setup-wifi}"
            echo "  install    - Install and enable all LOOP services"
            echo "  check      - Check status of all LOOP services"  
            echo "  setup-wifi - Configure WiFi power management (called by systemd)"
            exit 1
            ;;
    esac
}

# Only run main if script is executed directly (not sourced)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi 