# LOOP Deployment Guide 🤖

Your Little Optical Output Pal is ready to display some joy! Here's how to get your tiny friend up and running.

## 🚀 Quick Start

### Prerequisites

- Raspberry Pi Zero 2 W
- MicroSD card (8GB+) with Raspberry Pi OS Lite
- Waveshare 2.4" LCD (ILI9341)
- Rotary encoder (optional but fun!)

### Hardware Setup

Wire up your display (LOOP loves these pins!):

```
LCD Pin  -> Pi Pin (BCM)
VCC      -> 3.3V
GND      -> GND
DIN      -> GPIO 10 (MOSI)
CLK      -> GPIO 11 (SCLK)
CS       -> GPIO 8  (CE0)
DC       -> GPIO 25
RST      -> GPIO 27
BL       -> GPIO 18
```

### Software Installation

```bash
git clone https://github.com/yourusername/loop.git
cd loop
./deployment/scripts/install.sh
```

LOOP will handle the rest! 🎨

## 🔄 Updates

Keep LOOP fresh with a simple git pull:

```bash
cd /home/pi/loop
git pull
sudo systemctl restart loop
```

That's it! Simple and secure. 🔒

## 🔧 Troubleshooting

### Display Issues

```bash
# Test display
source venv/bin/activate
python -c "from display.spiout import ILI9341Driver; d = ILI9341Driver(get_config().display); d.fill_screen(0xF800)"
```

### Service Issues

```bash
sudo systemctl status loop    # Check status
sudo journalctl -u loop -f    # View logs
sudo systemctl restart loop   # Restart
```

### Need to Start Fresh?

```bash
./deployment/scripts/install.sh --force  # Full reinstall
```

## 🔐 Security Tips

1. Change default hotspot password
2. Use SSH keys, not passwords
3. Keep your Pi updated
4. Consider VPN for remote access

## 📱 Web Interface

Access your LOOP at:

```
http://your-pi-ip:8080
```

Features:

- Upload media
- Control playback
- Configure settings
- Check system status

---

Made with 💝 by your friends at LOOP
_"Your pocket-sized animation companion!"_
