# VidBox Quick Start Guide 🚀

Get your VidBox up and running in 5 minutes! (Well, maybe 15 if you're wiring things up...)

## 🎯 TL;DR

```bash
# Clone and install
git clone https://github.com/yourusername/vidbox.git
cd vidbox
./deployment/scripts/install.sh

# Access the web interface
# Go to http://your-pi-ip:8080
```

## 🔌 Hardware Setup (5 minutes)

Connect your Waveshare 2.4" LCD to your Pi Zero 2W:

| LCD Pin | Pi Pin (BCM) | Pi Pin (Physical) |
| ------- | ------------ | ----------------- |
| VCC     | 3.3V         | Pin 1             |
| GND     | GND          | Pin 6             |
| DIN     | GPIO 10      | Pin 19            |
| CLK     | GPIO 11      | Pin 23            |
| CS      | GPIO 8       | Pin 24            |
| DC      | GPIO 25      | Pin 22            |
| RST     | GPIO 27      | Pin 13            |
| BL      | GPIO 18      | Pin 12            |

**Optional**: Connect a rotary encoder for physical controls:

- Pin A → GPIO 2
- Pin B → GPIO 3
- Button → GPIO 4

## 📦 Software Setup

### Option 1: Auto Install (Recommended)

```bash
# SSH into your Pi
ssh pi@your-pi-ip

# Clone the repo
git clone https://github.com/yourusername/vidbox.git
cd vidbox

# Run the magic installer
chmod +x deployment/scripts/install.sh
./deployment/scripts/install.sh
```

### Option 2: Manual Install

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3 python3-pip python3-venv git ffmpeg

# Enable SPI
sudo raspi-config nonint do_spi 0

# Set up the project
cd vidbox
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start it up
python main.py
```

## 🎬 First Run

1. **Connect to WiFi**:

   - If no WiFi configured, it creates hotspot "VidBox-Setup" (password: vidbox123)
   - Connect and go to any website to configure WiFi

2. **Access Web Interface**:

   ```
   http://your-pi-ip:8080
   ```

3. **Upload Your First GIF**:
   - Click "Upload Media"
   - Drop a GIF file
   - Watch it process and display!

## 🎮 Controls

### Web Interface:

- Upload GIFs, videos, images
- Select active media
- Configure settings
- Check for updates

### Physical Controls (if encoder connected):

- **Rotate CW**: Next media
- **Rotate CCW**: Previous media
- **Press**: Pause/resume

## 🔧 Common Issues

### Display Not Working?

```bash
# Check SPI is enabled
lsmod | grep spi

# Test display
cd /home/pi/vidbox
source venv/bin/activate
python -c "from display.spiout import ILI9341Driver; from config.schema import get_config; d = ILI9341Driver(get_config().display); d.init(); d.fill_screen(0xF800)"
```

### Service Not Starting?

```bash
# Check status
sudo systemctl status vidbox

# View logs
sudo journalctl -u vidbox -f

# Restart
sudo systemctl restart vidbox
```

### WiFi Issues?

```bash
# Check WiFi status
iwconfig

# Restart WiFi
sudo systemctl restart wpa_supplicant

# Force hotspot mode
vidbox-hotspot start
```

## 🚀 Next Steps

1. **Set up automatic updates** (see DEPLOYMENT.md)
2. **Upload more media** via web interface
3. **Configure custom settings** in config.json
4. **Set up remote sync** for multiple devices

## 📱 Default Access Points

- **Web Interface**: http://your-pi-ip:8080
- **SSH**: ssh pi@your-pi-ip
- **Hotspot**: VidBox-Setup / vidbox123

## 🆘 Need Help?

- Check the logs: `sudo journalctl -u vidbox -f`
- Read DEPLOYMENT.md for advanced setup
- File an issue on GitHub

**Enjoy your new GIF display! 🎉**
