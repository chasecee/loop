# LOOP Quick Start Guide 🤖

Get your Little Optical Output Pal up and running in 5 minutes! (Well, maybe 15 if you're wiring things up...)

## 🎯 TL;DR

```bash
# Clone and install
git clone https://github.com/yourusername/loop.git
cd loop
./deployment/scripts/install.sh

# Access the web interface
# Go to http://your-pi-ip:8080
```

## 🔌 Hardware Setup (5 minutes)

Connect LOOP's display (Waveshare 2.4" LCD) to your Pi Zero 2W:

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

**Optional**: Give LOOP some physical controls with a rotary encoder:

- Pin A → GPIO 2
- Pin B → GPIO 3
- Button → GPIO 4

## 📦 Software Setup

### Option 1: Auto Install (Recommended)

```bash
# SSH into your Pi
ssh pi@your-pi-ip

# Clone LOOP
git clone https://github.com/yourusername/loop.git
cd loop

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

# Set up LOOP
cd loop
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start LOOP
python main.py
```

## 🎬 First Run

1. **Connect to WiFi**:

   - If no WiFi configured, LOOP creates its own network "LOOP-Setup" (password: loop123)
   - Connect and go to any website to configure WiFi

2. **Access Web Interface**:

   ```
   http://your-pi-ip:8080
   ```

3. **Upload Your First GIF**:
   - Click "Upload Media"
   - Drop a GIF file
   - Watch LOOP bring it to life!

## 🎮 Controls

### Web Interface:

- Upload GIFs, videos, images
- Select active media
- Configure settings
- Check for updates

### Physical Controls (if encoder connected):

- **Rotate Right**: Next animation
- **Rotate Left**: Previous animation
- **Press**: Pause/resume

## 🔧 Need Help?

### Display Not Working?

```bash
# Check SPI is enabled
lsmod | grep spi

# Test LOOP's display
cd /home/pi/loop
source venv/bin/activate
python -c "from display.spiout import ILI9341Driver; from config.schema import get_config; d = ILI9341Driver(get_config().display); d.init(); d.fill_screen(0xF800)"
```

### Service Not Starting?

```bash
# Check status
sudo systemctl status loop

# View logs
sudo journalctl -u loop -f

# Restart
sudo systemctl restart loop
```

### WiFi Issues?

```bash
# Check WiFi status
iwconfig

# Restart WiFi
sudo systemctl restart wpa_supplicant

# Start LOOP's hotspot
loop-hotspot start
```

## 🚀 Next Steps

1. **Set up automatic updates** (see DEPLOYMENT.md)
2. **Upload your favorite GIFs** via web interface
3. **Make LOOP your own** by tweaking config.json
4. **Set up remote sync** if you have multiple LOOPs

## 📱 Quick Reference

- **Web Interface**: http://your-pi-ip:8080
- **SSH**: ssh pi@your-pi-ip
- **WiFi Setup**: LOOP-Setup / loop123

## 🆘 Still Stuck?

- Check LOOP's logs: `sudo journalctl -u loop -f`
- Read DEPLOYMENT.md for advanced setup
- File an issue on GitHub

**Enjoy your new animation companion! 🤖✨**
