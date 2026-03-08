<div align="center">

# 📡 CellTower-OSINT

**4G/5G Metadata & GEOINT Mapping for Signal Auditing**

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Platform](https://img.shields.io/badge/Platform-Kali%20Linux-557C94?style=for-the-badge&logo=linux&logoColor=white)](https://kali.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![OSINT](https://img.shields.io/badge/Type-SIGINT%2FGEOINT-red?style=for-the-badge&logo=radar&logoColor=white)]()
[![Version](https://img.shields.io/badge/Version-2.0.0-orange?style=for-the-badge)]()

> ⚠️ **For authorized security auditing and educational use only.**

</div>

---

## 🔍 Overview

**CellTower-OSINT** is an independent SIGINT/GEOINT utility built for **Kali Linux**. It passively extracts 4G LTE and 5G NR cell tower metadata via USB tethering or ADB, maps tower locations using OpenCellID, and flags suspicious signal anomalies — including potential **IMSI catcher (Stingray) activity**.

```
  Phone (USB / ADB)
        │
        ▼
  ┌─────────────────────┐
  │  tower_geo_locator  │
  │  ─────────────────  │
  │  • Cell ID / MCC    │
  │  • Signal (RSRP)    │
  │  • Tower Coords     │
  └────────┬────────────┘
           │
     ┌─────▼──────┐      ┌──────────────┐
     │ OpenCellID │      │  Red Alert   │
     │    API     │      │  Stingray?   │
     └─────┬──────┘      └──────────────┘
           │
     ┌─────▼──────┐
     │  KML / CSV │
     │   Export   │
     └────────────┘
```

---

## ✨ Features

| Feature | Description |
|---|---|
| 📶 **Dual-Stack Support** | Works with both 4G (LTE) and 5G (NR) networks |
| 🗺️ **GEOINT Mapping** | Automated OpenCellID integration with KML/CSV export |
| 🚨 **Signal Auditing** | Real-time RSRP monitoring with Red Alert thresholds |
| 📍 **Tower Geolocation** | Pinpoints physical tower coordinates on a map |
| 🕵️ **IMSI Catcher Detection** | Flags suspicious cell tower behavior (Stingray indicators) |
| 📱 **Dual Connection** | Supports both USB Tethering and ADB (wired & wireless) |
| 🖥️ **Rich Terminal UI** | Live updating table with color-coded alerts |
| 🐧 **Kali Native** | Built for Kali Linux — no extra setup headaches |

---

## ⚙️ Requirements

- **OS:** Kali Linux (or any Debian-based distro)
- **Python:** 3.8+
- **Android:** 8.0+ (Android 12+ requires USB Debugging Security Settings enabled)
- **Hardware:** Android phone with USB debugging or tethering enabled
- **API Key:** [OpenCellID](https://my.opencellid.org/register) (free registration)

### Install Dependencies

**Option A — Virtual Environment (Recommended):**

```bash
# Create venv
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the tool
python3 tower_geo_locator.py

# Deactivate when done
deactivate
```

**Option B — Kali Linux system-wide:**

```bash
pip install -r requirements.txt --break-system-packages
```

**Option C — Manual install:**

```bash
pip install requests rich pyserial --break-system-packages
```

---

## 🚀 Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/rob-OSINT/CellTower-OSINT.git
cd CellTower-OSINT
```

### 2. Get your FREE OpenCellID API Key

> 🔑 Register here → **https://my.opencellid.org/register**

Once registered, copy your API key and either:

- Run the tool and select **option [3] Set OpenCellID API key** from the menu, or
- Edit manually:

```bash
nano tower_geo_locator.py
# Replace: YOUR_API_KEY_HERE
```

### 3. Connect your phone

**Option A — USB Tethering:**
```
Phone → Settings → Hotspot & Tethering → USB Tethering → ON
```
Verify on Kali:
```bash
ip a   # look for usb0 or rndis0 interface
```

**Option B — ADB over USB:**
```
Phone → Settings → Developer Options → USB Debugging → ON
```
Verify on Kali:
```bash
sudo apt install adb -y
adb devices
```

**Option C — ADB over WiFi (wireless):**
```bash
# Connect USB once to enable wireless ADB
adb tcpip 5555

# Find your phone IP
adb shell ip addr show wlan0

# Disconnect USB then connect wirelessly
adb connect 192.168.x.x:5555

# Verify
adb devices
```

### 4. Install dependencies & run

```bash
# Create and activate venv (recommended)
python3 -m venv venv
source venv/bin/activate

# Install
pip install -r requirements.txt

# Run
python3 tower_geo_locator.py
```

---

## 🖥️ Menu Options

```
[1] Start continuous scan      ← Live scanning with auto-refresh table
[2] Single scan                ← One-shot scan and export
[3] Set OpenCellID API key     ← Save your API key
[4] View last output           ← Review previous scan results
[5] Exit
```

**CLI flags (skip menu):**
```bash
python3 tower_geo_locator.py --no-menu          # scan immediately
python3 tower_geo_locator.py --once             # single scan
python3 tower_geo_locator.py --interval 10      # scan every 10s
python3 tower_geo_locator.py --mode adb         # force ADB mode
python3 tower_geo_locator.py --mode usb         # force USB mode
```

---

## 📤 Output

Results are saved to the `./output/` folder:

```
output/
├── celltower_YYYYMMDD_HHMMSS.csv    ← Spreadsheet data
└── celltower_YYYYMMDD_HHMMSS.kml    ← Import into Google Earth
```

**CSV columns:**
`timestamp | mcc | mnc | lac | cid | rat | rsrp | lat | lon | range | alerts`

**KML:**
- 🟢 Green pins = clean towers
- 🔴 Red pins = flagged/suspicious towers

---

## 🚨 Stingray / IMSI Catcher Detection

The tool runs **5 detection rules** in real-time:

| Rule | Severity | Trigger |
|------|----------|---------|
| `WEAK_SIGNAL` | HIGH | RSRP below -110 dBm |
| `GHOST_TOWER` | HIGH | Tower has no OpenCellID entry |
| `CID_CHANGE` | MEDIUM | Cell ID changed while stationary |
| `RAT_DOWNGRADE` | CRITICAL | Forced 4G/5G → 2G/3G downgrade |
| `RSRP_SPIKE` | MEDIUM | Sudden signal jump > 20 dBm |

> Alerts print in **red** to the terminal and are flagged in CSV/KML exports.

---

## 📁 File Structure

```
CellTower-OSINT/
├── tower_geo_locator.py   # Core OSINT engine
├── requirements.txt       # Python dependencies
├── README.md              # You are here
└── SECURITY.md            # Responsible disclosure policy
```

---

## 🤝 Contributing

Contributions are welcome! Please read [SECURITY.md](SECURITY.md) before submitting.

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit: `git commit -m "feat: your feature"`
4. Push: `git push origin feature/your-feature`
5. Open a Pull Request

---

## 🛡️ Legal & Responsible Use

This tool is intended **strictly** for authorized use. See [SECURITY.md](SECURITY.md) for full policy.

---

<div align="center">

Made with 🖤 by [rob-OSINT](https://github.com/rob-OSINT)

*"Signal Intelligence begins with knowing what's listening."*

</div>
