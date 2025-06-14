# VidBox Deployment Guide 🎬

This guide covers all the ways to deploy and update your VidBox system. Because I'm feeling generous, I've given you multiple options!

## 🚀 Initial Installation

### 1. Prerequisites

- Raspberry Pi Zero 2 W (or any Pi really, but Zero 2 W is the target)
- MicroSD card (8GB+) with Raspberry Pi OS Lite
- Waveshare 2.4" LCD (ILI9341)
- Rotary encoder (optional but recommended)
- Internet connection

### 2. Hardware Setup

Wire your Waveshare 2.4" LCD according to the config in `config/config.json`:

```
LCD Pin  -> Pi Pin (BCM)
VCC      -> 3.3V
GND      -> GND
DIN      -> GPIO 10 (MOSI)
CLK      -> GPIO 11 (SCLK)
CS       -> GPIO 8 (CE0)
DC       -> GPIO 25
RST      -> GPIO 27
BL       -> GPIO 18
```

### 3. Software Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/vidbox.git
cd vidbox

# Run the installation script
chmod +x deployment/scripts/install.sh
./deployment/scripts/install.sh
```

The installer will:

- Install system dependencies
- Set up Python virtual environment
- Configure systemd service
- Enable SPI interface
- Set up WiFi hotspot capability
- Start the VidBox service

## 📡 Update Methods

### Method 1: GitHub Actions (Automated) ⭐

This is the slickest option - fully automated CI/CD pipeline.

#### Setup:

1. Fork this repository
2. Add these secrets to your GitHub repository:
   - `PI_HOST`: Your Pi's IP address
   - `PI_USER`: Username (usually `pi`)
   - `PI_SSH_KEY`: Your SSH private key for the Pi
   - `PI_PATH`: Installation path (default: `/home/pi/vidbox`)

#### Usage:

```bash
# Push to main branch triggers automatic deployment
git push origin main

# Or create a tag for versioned releases
git tag v1.1.0
git push origin v1.1.0
```

The workflow will:

- Build and test the code
- Create deployment package
- Deploy directly to your Pi via SSH
- Restart the service
- Create GitHub releases for tags

### Method 2: Simple Git Pull

For the minimalists who like to keep it simple.

#### Setup:

```bash
# On your Pi
cd /home/pi/vidbox
git remote set-url origin https://github.com/yourusername/vidbox.git
```

#### Usage:

```bash
# SSH into your Pi and run:
cd /home/pi/vidbox
git pull
sudo systemctl restart vidbox
```

### Method 3: Remote Update Server

Set up your own update server for over-the-air updates.

#### Setup Update Server:

1. Create a web server that serves:
   - `manifest.json` - Contains version info
   - `vidbox-{version}.tar.gz` - The actual update package

#### Example manifest.json:

```json
{
  "version": "1.1.0",
  "build_date": "2024-01-15T10:30:00Z",
  "archive": "vidbox-1.1.0.tar.gz",
  "restart_required": true
}
```

#### Enable on Pi:

```bash
# Update config.json
{
  "sync": {
    "enabled": true,
    "server_url": "https://your-update-server.com/updates"
  }
}
```

### Method 4: Web Interface Updates

Update directly through the VidBox web interface.

1. Open http://your-pi-ip:8080
2. Go to Settings → Updates
3. Click "Check for Updates"
4. Click "Install Update" if available

### Method 5: Webhook Updates

For integration with other systems.

#### Setup:

Add webhook URL to your GitHub secrets:

- `WEBHOOK_URL`: Your webhook endpoint
- `WEBHOOK_SECRET`: Secret for verification

The webhook receives:

```json
{
  "version": "1.1.0",
  "commit": "abc123...",
  "download_url": "https://github.com/..."
}
```

## 🔧 Development Workflow

### Local Development:

```bash
# Install in development mode
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run with debug mode
export VIDBOX_DEBUG=1
python main.py
```

### Testing Changes:

```bash
# Run tests
python -m pytest tests/ -v

# Test on Pi without full deployment
rsync -av --exclude='.git' . pi@your-pi:/tmp/vidbox-test/
ssh pi@your-pi "cd /tmp/vidbox-test && python3 main.py"
```

## 🐛 Troubleshooting

### Service Issues:

```bash
# Check service status
sudo systemctl status vidbox

# View logs
sudo journalctl -u vidbox -f

# Restart service
sudo systemctl restart vidbox
```

### Display Issues:

```bash
# Check SPI is enabled
lsmod | grep spi

# Test display directly
cd /home/pi/vidbox
source venv/bin/activate
python -c "from display.spiout import ILI9341Driver; from config.schema import get_config; d = ILI9341Driver(get_config().display); d.init(); d.fill_screen(0xF800)"
```

### Update Issues:

```bash
# Check git status
cd /home/pi/vidbox
git status
git log --oneline -5

# Manual rollback
sudo systemctl stop vidbox
cp -r ../vidbox_backup_* .
sudo systemctl start vidbox
```

## 🔐 Security Notes

- Change default hotspot password in `config.json`
- Use SSH keys, not passwords for GitHub Actions
- Keep your Pi updated: `sudo apt update && sudo apt upgrade`
- Consider VPN access instead of exposing the web interface

## 🎯 Production Tips

1. **Use a dedicated update server** for multiple devices
2. **Set up monitoring** with status endpoints
3. **Enable automatic updates** during off-peak hours
4. **Keep backups** of your media and configs
5. **Test updates** on a staging device first

## 📊 Monitoring Your Deployment

The web interface provides:

- System status and uptime
- Update history and logs
- Media library statistics
- Hardware health monitoring

Access it at: `http://your-pi-ip:8080`

---

**Pro Tip**: Set up multiple update methods as backup. GitHub Actions for automation, git pull for quick fixes, and remote updates for OTA convenience. Because redundancy is sexy! 😎
