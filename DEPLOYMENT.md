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

## 🔄 Update Methods

### 1. Quick Update (Recommended)

Already have LOOP? Just run:

```bash
./deployment/scripts/install.sh
```

The script is smart - it'll only update what's needed! ⚡

### 2. GitHub Actions (Automated)

Let LOOP update itself! Add these secrets:

- `PI_HOST`: Your Pi's IP
- `PI_USER`: Username
- `PI_SSH_KEY`: SSH key
- `PI_PATH`: Install path

Push to main or tag a release:

```bash
git push origin main
# or
git tag v1.0.0 && git push --tags
```

### 3. Manual Update

Old school but reliable:

```bash
cd /home/pi/loop
git pull
sudo systemctl restart loop
```

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
