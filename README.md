# DewDash - S24 Dew Point Monitor

[![Version](https://img.shields.io/badge/version-1.0.16-blue.svg)](https://github.com/JorgeS15/DewDash)
[![Python](https://img.shields.io/badge/python-3.7+-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

**Lightning-fast dew point monitoring at 10Hz**

Real-time web dashboard for monitoring Banner S24 Dew Point Sensor via DXMR90-X1 Modbus gateway. Features automatic network configuration, bilingual interface (Portuguese/English), and ultra-fast 10Hz data updates.

![DewDash Dashboard](https://via.placeholder.com/800x400?text=DewDash+Dashboard)

## ✨ Features

- 🌐 **Real-time Monitoring** - Updates at 10Hz (10 times per second)
- 🇵🇹 **Bilingual Interface** - Portuguese (default) and English with single-click toggle
- 🔧 **Auto Network Config** - Automatically sets PC IP to 192.168.0.2
- 🔐 **Auto Admin Rights** - Requests administrator privileges automatically
- 🚀 **Auto Browser Launch** - Opens dashboard when data is ready
- 📊 **Live Console Display** - Real-time readings in terminal (1Hz)
- 💻 **Responsive Design** - Works on desktop, tablet, and mobile
- 🎨 **Modern UI** - Clean, professional interface with color-coded alerts
- 📡 **Modbus TCP/RTU** - Communicates with DXMR90-X1 via Modbus TCP

## 📋 Table of Contents

- [Hardware Requirements](#hardware-requirements)
- [Software Requirements](#software-requirements)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Usage](#usage)
- [Dashboard Overview](#dashboard-overview)
- [Troubleshooting](#troubleshooting)
- [Technical Details](#technical-details)
- [Version History](#version-history)
- [Contributing](#contributing)
- [License](#license)

## 🔧 Hardware Requirements

### Required Equipment

1. **Banner S24 Dew Point Sensor**
   - Model: S24-series
   - Measures: Temperature, Humidity, Dew Point
   - Interface: Modbus RTU (RS-485)
   - Default Address: 1
   - Baud Rate: 19200

2. **DXMR90-X1 Modbus Gateway**
   - Manufacturer: Banner Engineering
   - Function: Modbus RTU to Modbus TCP gateway
   - IP Address: 192.168.0.1 (default)
   - Modbus ID: 199 (for Local Registers)

3. **PC/Laptop**
   - Windows 10/11 (64-bit)
   - Ethernet port
   - Administrator access

4. **Ethernet Cable**
   - Standard Cat5e/Cat6
   - Connects PC to DXMR90-X1

### Physical Connections

```
┌─────────────────┐     RS-485      ┌──────────────┐     Ethernet     ┌──────────┐
│  S24 Sensor     │ ←──────────────→ │  DXMR90-X1   │ ←──────────────→ │    PC    │
│  (Modbus RTU)   │   19200 baud     │   Gateway    │  192.168.0.x     │          │
└─────────────────┘   Address: 1     └──────────────┘  Port 502        └──────────┘
```

## 💾 Software Requirements

### Python
- **Version:** Python 3.7 or higher
- **Download:** [python.org](https://www.python.org/downloads/)

### Python Libraries
- `flask` - Web server framework
- `pymodbus` - Modbus communication library

## 📦 Installation

### Step 1: Install Python

1. Download Python from [python.org](https://www.python.org/downloads/)
2. Run installer
3. ✅ Check **"Add Python to PATH"**
4. Click **"Install Now"**

### Step 2: Install Required Libraries

Open **Command Prompt** and run:

```bash
pip install flask pymodbus --break-system-packages
```

Expected output:
```
Successfully installed flask-3.x.x pymodbus-3.11.4
```

### Step 3: Download Dashboard Script

Download `s24_web_dashboard.py` and save to a folder, e.g.:
```
C:\DewDash\s24_web_dashboard.py
```

## 🚀 Quick Start

### 1. Connect Hardware

```
S24 Sensor → DXMR90-X1 → PC
   (RS-485)    (Ethernet)
```

### 2. Run the Script

**Option A: Double-click**
- Simply double-click `s24_web_dashboard.py`
- Click **"Yes"** when UAC prompt appears

**Option B: Command Prompt**
```bash
cd C:\DewDash
python s24_web_dashboard.py
```

### 3. Use the Dashboard

The browser will open automatically showing live sensor data!

```
http://localhost:5000
```

## ⚙️ Configuration

### Default Settings

Edit these values at the top of `s24_web_dashboard.py`:

```python
# DXMR90-X1 Settings
DXM_IP = "192.168.0.1"          # DXMR90-X1 IP address
DXM_PORT = 502                   # Modbus TCP port
MODBUS_ID = 199                  # Local Registers device ID

# Web Server Settings
WEB_PORT = 5000                  # Web dashboard port

# Network Configuration
TARGET_IP = "192.168.0.2"        # PC IP address (auto-configured)
TARGET_SUBNET = "255.255.255.0"  # Subnet mask
```

### Custom IP Address

If your DXMR90-X1 has a different IP:

```python
DXM_IP = "192.168.1.100"         # Your custom IP
TARGET_IP = "192.168.1.50"       # PC IP in same subnet
```

### Change Web Port

If port 5000 is already in use:

```python
WEB_PORT = 8080                  # Use different port
```

Then access: `http://localhost:8080`

## 📖 Usage

### Starting the Dashboard

1. **Run as Administrator** (automatic)
   ```bash
   python s24_web_dashboard.py
   ```

2. **Wait for startup**
   ```
   ✓ Network configured: 192.168.0.2
   ✓ Web server ready
   ✓ Connected to DXMR90-X1
   ✓ First reading: 76.9% RH, 23.5°C
   🌐 Opening browser...
   ```

3. **Dashboard opens automatically** showing live data

### Console Display

The terminal shows live readings updating every second:

```
======================================================================
LIVE SENSOR READINGS (updating every second)
======================================================================
[10:30:45] ● Temp:  23.5°C | RH:  76.9% | Dew Point:  19.8°C
```

**Status Indicators:**
- `●` = Online (connected)
- `○` = Offline (disconnected)

### Stopping the Dashboard

Press `Ctrl+C` in the terminal window:

```
^C
Shutting down...
```

## 🎨 Dashboard Overview

### Main Display

The web dashboard shows 3 main cards:

#### 💧 Relative Humidity (Humidade Relativa)
- Current humidity percentage
- Updates 10 times per second
- Yellow warning if > 80% or < 20%

#### 🌡️ Temperature (Temperatura)
- Current temperature in °C
- Also shows °F
- Updates 10 times per second

#### 💦 Dew Point (Ponto de Orvalho)
- Current dew point in °C
- Also shows °F
- Updates 10 times per second

### System Information Panel

Located at the bottom:
- **DXMR90-X1 Address** - Gateway IP and port
- **Last Update** - Timestamp of last reading
- **Raw Values** - Modbus register values [1-5]
- **Connection Status** - Online/Offline
- **Version** - Software version

### Language Toggle

Click the **"English"** or **"Português"** button in top-right corner to switch languages.

**Portuguese (Default):**
- Humidade Relativa
- Temperatura
- Ponto de Orvalho

**English:**
- Relative Humidity
- Temperature
- Dew Point

### Mobile Access

Access from phone/tablet on same network:

1. Find your PC's IP address:
   ```bash
   ipconfig
   ```
   Look for: `IPv4 Address: 192.168.1.100`

2. Open browser on mobile:
   ```
   http://192.168.1.100:5000
   ```

## 🔍 Troubleshooting

### Connection Issues

#### Problem: "Cannot connect to DXMR90-X1"

**Check:**
1. ✅ DXMR90-X1 is powered on
2. ✅ Ethernet cable is connected
3. ✅ PC IP is 192.168.0.2 (check with `ipconfig`)
4. ✅ Can ping DXMR90-X1:
   ```bash
   ping 192.168.0.1
   ```

**Solution:**
- Verify DXMR90-X1 IP address (may not be default)
- Check network adapter settings
- Disable firewall temporarily to test

#### Problem: "Browser shows 'Not Found'"

**This should not happen in v1.0.14+**, but if it does:

**Solution:**
- Wait 10 seconds and refresh browser
- Manually open: `http://localhost:5000`

### Network Configuration Issues

#### Problem: Network config fails

**Check:**
1. ✅ Running as Administrator
2. ✅ Ethernet adapter name is "Ethernet"

**Solution:**
- Right-click script → "Run as Administrator"
- Or manually set IP to 192.168.0.2 in Windows Network Settings

#### Problem: "Address already in use"

**Solution:**
- Change `WEB_PORT` to different number (e.g., 8080)
- Or stop other service using port 5000

### Data Display Issues

#### Problem: All values show zero

**Check:**
1. ✅ DXMR90-X1 RTU Read Rules are configured
2. ✅ S24 sensor is powered on
3. ✅ RS-485 wiring is correct

**Solution:**
- Use DXM Configuration Software to verify RTU Read Rules
- Check S24 sensor status LED
- Verify Modbus communication with Register View Utility

#### Problem: Values update slowly

**Check:**
- DXMR90-X1 RTU Read Rule frequency (should be 60 seconds or less)
- Dashboard updates at 10Hz, but DXMR90-X1 reads sensor at configured frequency

### Browser Issues

#### Problem: Browser doesn't open automatically

**Solution:**
- Manually open: `http://localhost:5000`
- Check if DXMR90-X1 connection succeeded (browser only opens if connected)

#### Problem: Language won't switch

**Solution:**
- Clear browser cache
- Hard refresh: `Ctrl+Shift+R`

## 🔬 Technical Details

### Update Rates

**Backend (Python):**
- Modbus polling: **10Hz** (100ms interval)
- Reads 5 registers per request
- ~10 requests/second to DXMR90-X1

**Frontend (Web):**
- API polling: **10Hz** (100ms interval)
- Display updates: **10Hz**
- Console display: **1Hz** (1 second)

### Network Architecture

```
┌──────────────┐
│  S24 Sensor  │ Modbus RTU (19200 baud)
│  Address: 1  │
└──────┬───────┘
       │
       ↓
┌──────────────────────┐
│  DXMR90-X1 Gateway   │
│  IP: 192.168.0.1     │
│  Port: 502 (TCP)     │
│  Modbus ID: 199      │
└──────┬───────────────┘
       │
       ↓ Modbus TCP
┌──────────────────────┐
│  Python Backend      │
│  Reads every 100ms   │
│  Flask API Server    │
└──────┬───────────────┘
       │
       ↓ HTTP/JSON
┌──────────────────────┐
│  Web Browser         │
│  Polls every 100ms   │
│  Displays at 10Hz    │
└──────────────────────┘
```

### Register Mapping

**S24 Sensor Registers (Modbus RTU):**
- 40001: Humidity (÷100 = %RH)
- 40002: Temperature °C (÷20 = °C)
- 40003: Temperature °F (÷20 = °F)
- 40004: Dew Point °C (÷100 = °C)
- 40005: Dew Point °F (÷100 = °F)

**DXMR90-X1 Local Registers (Modbus TCP):**
- Registers 1-5: S24 data (copied by RTU Read Rules)
- Modbus ID: 199

**Python reads:** Local Registers 1-5 via Modbus TCP from DXMR90-X1

### Data Flow

```
1. S24 Sensor measures environment
2. DXMR90-X1 reads S24 via Modbus RTU (every 60s)
3. DXMR90-X1 stores data in Local Registers 1-5
4. Python reads Local Registers via Modbus TCP (every 100ms)
5. Python serves data via Flask API
6. Browser polls API (every 100ms)
7. Display updates (10Hz)
```

### Performance

**CPU Usage:** ~5-10% (10Hz updates)
**RAM Usage:** ~50 MB
**Network Traffic:** ~1 KB/s (Modbus) + minimal HTTP

### File Structure

```
DewDash/
│
├── s24_web_dashboard.py      # Main application (900+ lines)
├── README.md                  # This file
└── requirements.txt           # Python dependencies (optional)
```

## 📚 DXMR90-X1 Configuration

### Required RTU Read Rules

Configure in DXM Configuration Software:

```
Rule 1: S24_Humidity
- Port: 1
- Server ID: 1
- Read 1 register starting at 40001
- To local registers: 1 through 1
- Scale: 0.01 (÷100)
- Frequency: 00:01:00.000

Rule 2: S24_Temperature
- Port: 1
- Server ID: 1
- Read 2 registers starting at 40002
- To local registers: 2 through 3
- Scale: 0.05 (÷20)
- Frequency: 00:01:00.000

Rule 3: S24_DewPoint
- Port: 1
- Server ID: 1
- Read 2 registers starting at 40004
- To local registers: 4 through 5
- Scale: 0.01 (÷100)
- Frequency: 00:01:00.000
```

### Verify Configuration

Use **Register View Utility** in DXM Configuration Software:
1. Connect to DXMR90-X1
2. Read Local Registers 1-5 (Modbus ID 199)
3. Should see actual sensor values

## 📝 Version History

### v1.0.16 (Current)
- Updated webpage header: "DewDash" as title, subtitle in Portuguese/English
- Removed thermometer icon from header

### v1.0.15
- Moved version number to System Information panel

### v1.0.14
- Flask server starts before connecting to DXM (fixes "Not Found")

### v1.0.13
- Added version number to webpage
- Browser opens immediately after first reading

### v1.0.12
- Increased browser open delay to 5 seconds

### v1.0.11
- **Major:** Increased update rate to 10Hz (100ms)

### v1.1.0
- Removed dew point spread (simplified interface)

### v1.0.9
- Removed spread from console display

### v1.0.8
- Suppressed pymodbus timeout messages
- Console display at 1Hz

### v1.0.7
- Added live console display

### v1.0.6
- Fixed connection status logic

### v1.0.5
- Simplified network configuration

### v1.0.4
- Fixed Unicode encoding for Portuguese Windows

### v1.0.3
- Disabled Flask HTTP logging

### v1.0.2
- Auto-request administrator privileges

### v1.0.1
- Added Portuguese/English bilingual support
- Auto-open browser
- Auto network configuration

### v1.0.0
- Initial release

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

### Development Setup

```bash
git clone https://github.com/yourusername/dewdash.git
cd dewdash
pip install -r requirements.txt
python s24_web_dashboard.py
```

### Reporting Bugs

Please include:
- Operating System version
- Python version
- Full error message
- Steps to reproduce

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Banner Engineering for S24 sensor and DXMR90-X1 gateway
- Flask framework for web server
- pymodbus library for Modbus communication
- All contributors and users

## 📞 Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Email: support@example.com

## 🔗 Related Links

- [Banner Engineering S24 Sensor](https://www.bannerengineering.com)
- [DXMR90 Gateway Documentation](https://www.bannerengineering.com)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [pymodbus Documentation](https://pymodbus.readthedocs.io/)

---

**Made with ❤️ for industrial monitoring**

**Version:** 1.0.16 | **Last Updated:** December 2024
