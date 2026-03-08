<div align="center">

```
    ████████╗ ██████╗ ██╗    ██╗███████╗██████╗       ██████╗ ███████╗██╗███╗   ██╗████████╗
       ██╔══╝██╔═══██╗██║    ██║██╔════╝██╔══██╗     ██╔═══██╗██╔════╝██║████╗  ██║╚══██╔══╝
       ██║   ██║   ██║██║ █╗ ██║█████╗  ██████╔╝     ██║   ██║███████╗██║██╔██╗ ██║   ██║   
       ██║   ██║   ██║██║███╗██║██╔══╝  ██╔══██╗     ██║   ██║╚════██║██║██║╚██╗██║   ██║   
       ██║   ╚██████╔╝╚███╔███╔╝███████╗██║  ██║     ╚██████╔╝███████║██║██║ ╚████║   ██║   
       ╚═╝    ╚═════╝  ╚══╝╚══╝ ╚══════╝╚═╝  ╚═╝      ╚═════╝ ╚══════╝╚═╝╚═╝  ╚═══╝   ╚═╝  
```

# 📡 CellTower-OSINT

**4G/5G Metadata & GEOINT Mapping for Signal Auditing**

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Platform](https://img.shields.io/badge/Platform-Kali%20Linux-557C94?style=for-the-badge&logo=linux&logoColor=white)](https://kali.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![OSINT](https://img.shields.io/badge/Type-SIGINT%2FGEOINT-red?style=for-the-badge&logo=radar&logoColor=white)]()
[![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=for-the-badge)]()

> ⚠️ **For authorized security auditing and educational use only.**

</div>

---

## 🔍 Overview

**CellTower-OSINT** is an independent SIGINT/GEOINT utility built for **Kali Linux**. It passively extracts 4G LTE and 5G NR cell tower metadata via USB tethering, maps tower locations using OpenCellID, and flags suspicious signal anomalies — including potential **IMSI catcher (Stingray) activity**.

```
  Phone (USB Tethered)
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
| 🐧 **Kali Native** | Built for Kali Linux — no extra setup headaches |

---

## ⚙️ Requirements

- **OS:** Kali Linux (or any Debian-based distro)
- **Python:** 3.8+
- **Hardware:** Android phone with USB tethering enabled
- **API Key:** [OpenCellID](https://opencellid.org/) (free registration)

### Install Dependencies

```bash
pip install requests
```

---

## 🚀 Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/rob-OSINT/CellTower-OSINT.git
cd CellTower-OSINT
```

### 2. Add your OpenCellID API Key

Open `tower_geo_locator.py` and replace the placeholder:

```python
API_KEY = "YOUR_OPENCELLID_API_KEY_HERE"
```

Get a free key at: https://my.opencellid.org/register

### 3. Connect your phone

- Enable **USB Tethering** on your Android device
- Connect via USB to your Kali machine
- Verify with `ip a` — look for `usb0` or `enp*` interface

### 4. Run the tool

```bash
python3 tower_geo_locator.py
```

---

## 📤 Output

The tool generates two export formats:

```
CellTower-OSINT/
├── output.kml       ← Import into Google Earth / Maps
└── output.csv       ← Spreadsheet-ready tower data
```

**CSV columns:**
`MCC | MNC | LAC | CellID | RSRP | Latitude | Longitude | Alert`

---

## 🚨 Red Alert — Stingray Indicators

The tool flags towers that match known IMSI catcher patterns:

- 📉 Sudden significant RSRP drop on a familiar tower
- 🔄 Unexpected Cell ID changes in a stationary location
- 📡 Tower with no matching OpenCellID entry (ghost tower)
- ⚡ Forced 2G/3G downgrade while 4G/5G is available

> Alerts are printed in red to the terminal and flagged in the CSV export.

---

## 📁 File Structure

```
CellTower-OSINT/
├── tower_geo_locator.py   # Core OSINT engine
├── README.md              # You are here
├── CONTRIBUTING.md        # How to contribute
└── SECURITY.md            # Responsible disclosure policy
```

---

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting pull requests.

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m "Add your feature"`
4. Push: `git push origin feature/your-feature`
5. Open a Pull Request

---

## 🛡️ Security & Responsible Use

This tool is intended **strictly** for:
- ✅ Authorized penetration testing
- ✅ Personal network auditing
- ✅ Security research and education

**Do NOT use this tool to:**
- ❌ Monitor individuals without consent
- ❌ Interfere with cellular infrastructure
- ❌ Violate local laws or regulations

See [SECURITY.md](SECURITY.md) for our full disclosure policy.

---

## 📜 License

This project is licensed under the **MIT License** — see [LICENSE](LICENSE) for details.

---

<div align="center">

Made with 🖤 by [rob-OSINT](https://github.com/rob-OSINT)

*"Signal Intelligence begins with knowing what's listening."*

</div>
