#!/usr/bin/env python3
# ============================================================
#   CellTower-OSINT — 4G/5G SIGINT/GEOINT Mapping Tool
#   Author  : rob-OSINT
#   Platform: Kali Linux
#   License : MIT
# ============================================================

import os
import sys
import csv
import time
import json
import datetime
import argparse
import subprocess
import threading
import requests
from pathlib import Path

# ── Optional rich UI ──────────────────────────────────────
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.live import Live
    from rich.layout import Layout
    from rich import box
    from rich.text import Text
    from rich.style import Style
    RICH = True
except ImportError:
    RICH = False

console = Console() if RICH else None

# ══════════════════════════════════════════════════════════
#   CONFIG
# ══════════════════════════════════════════════════════════

OPENCELLID_API_KEY  = "YOUR_API_KEY_HERE"
OPENCELLID_URL      = "https://opencellid.org/cell/get"
OUTPUT_DIR          = Path("./output")
SCAN_INTERVAL       = 5
RSRP_RED_ALERT      = -110
RSRP_YELLOW_ALERT   = -95
VERSION             = "2.0.0"

OUTPUT_DIR.mkdir(exist_ok=True)


# ══════════════════════════════════════════════════════════
#   OPERATOR LOOKUP DATABASE (MCC + MNC)
# ══════════════════════════════════════════════════════════

OPERATORS = {
    # ── India ──────────────────────────────────────────────
    ("404", "01"): "Vodafone India", ("404", "02"): "Airtel India",
    ("404", "03"): "Airtel India",   ("404", "04"): "Idea Cellular",
    ("404", "05"): "Vodafone India", ("404", "07"): "BSNL India",
    ("404", "10"): "Airtel India",   ("404", "11"): "Vodafone India",
    ("404", "12"): "Idea Cellular",  ("404", "13"): "Vodafone India",
    ("404", "14"): "Idea Cellular",  ("404", "15"): "Vodafone India",
    ("404", "16"): "Airtel India",   ("404", "17"): "AIRCEL India",
    ("404", "18"): "Reliance India", ("404", "19"): "Idea Cellular",
    ("404", "20"): "Vodafone India", ("404", "21"): "MTNL Mumbai",
    ("404", "22"): "Idea Cellular",  ("404", "24"): "Idea Cellular",
    ("404", "25"): "AIRCEL India",   ("404", "27"): "BSNL India",
    ("404", "28"): "AIRCEL India",   ("404", "29"): "AIRCEL India",
    ("404", "30"): "Vodafone India", ("404", "31"): "Airtel India",
    ("404", "34"): "CellOne India",  ("404", "36"): "Reliance India",
    ("404", "37"): "Aircel India",   ("404", "38"): "BSNL India",
    ("404", "40"): "Airtel India",   ("404", "41"): "Airtel India",
    ("404", "42"): "Airtel India",   ("404", "43"): "Vodafone India",
    ("404", "44"): "Vodafone India", ("404", "45"): "Airtel India",
    ("404", "46"): "Vodafone India", ("404", "49"): "Airtel India",
    ("404", "50"): "Reliance Jio",   ("404", "51"): "BSNL India",
    ("404", "52"): "Reliance India", ("404", "53"): "BSNL India",
    ("404", "54"): "BSNL India",     ("404", "55"): "BSNL India",
    ("404", "56"): "Idea Cellular",  ("404", "57"): "BSNL India",
    ("404", "58"): "BSNL India",     ("404", "59"): "BSNL India",
    ("404", "60"): "Vodafone India", ("404", "62"): "Airtel India",
    ("404", "64"): "Idea Cellular",  ("404", "66"): "Vodafone India",
    ("404", "67"): "Vodafone India", ("404", "68"): "MTNL Delhi",
    ("404", "69"): "MTNL Mumbai",    ("404", "70"): "Airtel India",
    ("404", "71"): "BSNL India",     ("404", "72"): "BSNL India",
    ("404", "73"): "Vodafone India", ("404", "74"): "Idea Cellular",
    ("404", "75"): "Airtel India",   ("404", "76"): "Airtel India",
    ("404", "77"): "Airtel India",   ("404", "78"): "Idea Cellular",
    ("404", "79"): "BSNL India",     ("404", "80"): "Idea Cellular",
    ("404", "81"): "BSNL India",     ("404", "82"): "Idea Cellular",
    ("404", "83"): "Reliance Jio",   ("404", "84"): "Vodafone India",
    ("404", "85"): "Reliance India", ("404", "86"): "Vodafone India",
    ("404", "87"): "Idea Cellular",  ("404", "88"): "Vodafone India",
    ("404", "89"): "Idea Cellular",  ("404", "90"): "Airtel India",
    ("404", "91"): "Airtel India",   ("404", "92"): "Airtel India",
    ("404", "93"): "Airtel India",   ("404", "94"): "Airtel India",
    ("404", "95"): "Airtel India",   ("404", "96"): "Idea Cellular",
    ("404", "97"): "Aircel India",   ("404", "98"): "BSNL India",
    ("405", "01"): "Reliance Jio",   ("405", "025"): "Vodafone India",
    ("405", "027"): "Vodafone India",("405", "030"): "Vodafone India",
    ("405", "031"): "Airtel India",  ("405", "032"): "Airtel India",
    ("405", "033"): "Airtel India",  ("405", "034"): "Airtel India",
    ("405", "035"): "Airtel India",  ("405", "036"): "Airtel India",
    ("405", "037"): "Airtel India",  ("405", "038"): "Airtel India",
    ("405", "039"): "Airtel India",  ("405", "041"): "Airtel India",
    ("405", "042"): "Airtel India",  ("405", "51"): "Airtel India",
    ("405", "52"): "Airtel India",   ("405", "53"): "Airtel India",
    ("405", "54"): "Airtel India",   ("405", "55"): "Airtel India",
    ("405", "56"): "Airtel India",   ("405", "66"): "Vodafone India",
    ("405", "67"): "Vodafone India", ("405", "70"): "Airtel India",
    ("405", "750"): "Reliance Jio",  ("405", "751"): "Reliance Jio",
    ("405", "752"): "Reliance Jio",  ("405", "753"): "Reliance Jio",
    ("405", "754"): "Reliance Jio",  ("405", "755"): "Reliance Jio",
    ("405", "756"): "Reliance Jio",  ("405", "799"): "Reliance Jio",
    ("405", "800"): "Airtel India",  ("405", "801"): "Airtel India",
    ("405", "802"): "Airtel India",  ("405", "803"): "Airtel India",
    ("405", "804"): "Airtel India",  ("405", "805"): "Airtel India",
    ("405", "806"): "Airtel India",  ("405", "807"): "Airtel India",
    ("405", "808"): "Airtel India",  ("405", "809"): "Airtel India",
    ("405", "810"): "Airtel India",  ("405", "811"): "Airtel India",
    ("405", "812"): "Airtel India",  ("405", "813"): "Airtel India",
    ("405", "814"): "Airtel India",  ("405", "815"): "Airtel India",
    ("405", "816"): "Airtel India",  ("405", "817"): "Airtel India",
    ("405", "818"): "Airtel India",  ("405", "819"): "Airtel India",
    ("405", "820"): "Airtel India",  ("405", "821"): "Airtel India",
    ("405", "822"): "Airtel India",  ("405", "845"): "Airtel India",
    ("405", "846"): "Airtel India",  ("405", "847"): "Airtel India",
    ("405", "848"): "Airtel India",  ("405", "849"): "Airtel India",
    ("405", "850"): "Airtel India",  ("405", "851"): "Airtel India",
    ("405", "852"): "Airtel India",  ("405", "853"): "Airtel India",
    ("405", "875"): "Vodafone India",("405", "876"): "Vodafone India",
    ("405", "877"): "Vodafone India",("405", "878"): "Vodafone India",
    ("405", "879"): "Vodafone India",("405", "880"): "Vodafone India",
    ("405", "881"): "Vodafone India",("405", "909"): "Vi (Vodafone-Idea)",
    # ── USA ────────────────────────────────────────────────
    ("310", "010"): "AT&T USA",      ("310", "012"): "Verizon USA",
    ("310", "013"): "MobileOne USA", ("310", "020"): "Union Telephone",
    ("310", "030"): "AT&T USA",      ("310", "032"): "IT&E Overseas",
    ("310", "040"): "T-Mobile USA",  ("310", "060"): "Consolidated Telcom",
    ("310", "070"): "AT&T USA",      ("310", "080"): "AT&T USA",
    ("310", "090"): "AT&T USA",      ("310", "100"): "Plateau Wireless",
    ("310", "110"): "IT&E Overseas", ("310", "120"): "Sprint USA",
    ("310", "150"): "AT&T USA",      ("310", "160"): "T-Mobile USA",
    ("310", "170"): "T-Mobile USA",  ("310", "180"): "T-Mobile USA",
    ("310", "190"): "AT&T USA",      ("310", "200"): "T-Mobile USA",
    ("310", "210"): "T-Mobile USA",  ("310", "220"): "T-Mobile USA",
    ("310", "230"): "T-Mobile USA",  ("310", "240"): "T-Mobile USA",
    ("310", "250"): "T-Mobile USA",  ("310", "260"): "T-Mobile USA",
    ("310", "270"): "T-Mobile USA",  ("310", "280"): "AT&T USA",
    ("310", "290"): "T-Mobile USA",  ("310", "300"): "T-Mobile USA",
    ("310", "310"): "T-Mobile USA",  ("310", "320"): "T-Mobile USA",
    ("310", "330"): "T-Mobile USA",  ("310", "340"): "T-Mobile USA",
    ("310", "350"): "T-Mobile USA",  ("310", "380"): "AT&T USA",
    ("310", "390"): "T-Mobile USA",  ("310", "400"): "T-Mobile USA",
    ("310", "410"): "AT&T USA",      ("310", "420"): "T-Mobile USA",
    ("310", "490"): "T-Mobile USA",  ("310", "560"): "AT&T USA",
    ("310", "580"): "T-Mobile USA",  ("310", "590"): "T-Mobile USA",
    ("310", "660"): "T-Mobile USA",  ("310", "800"): "T-Mobile USA",
    ("310", "890"): "Verizon USA",   ("310", "910"): "T-Mobile USA",
    ("310", "950"): "AT&T USA",      ("311", "480"): "Verizon USA",
    # ── UK ─────────────────────────────────────────────────
    ("234", "10"): "O2 UK",          ("234", "15"): "Vodafone UK",
    ("234", "20"): "3 UK",           ("234", "30"): "EE UK",
    ("234", "50"): "JT Group UK",    ("234", "55"): "Sure UK",
    ("234", "76"): "BT Mobile UK",
    # ── Pakistan ───────────────────────────────────────────
    ("410", "01"): "Mobilink Pakistan", ("410", "03"): "Ufone Pakistan",
    ("410", "06"): "Telenor Pakistan",  ("410", "07"): "Warid Pakistan",
    ("410", "08"): "Zong Pakistan",
    # ── Bangladesh ─────────────────────────────────────────
    ("470", "01"): "Grameenphone",   ("470", "02"): "Robi",
    ("470", "03"): "Banglalink",     ("470", "05"): "Teletalk",
    ("470", "07"): "Airtel Bangladesh",
    # ── China ──────────────────────────────────────────────
    ("460", "00"): "China Mobile",   ("460", "01"): "China Unicom",
    ("460", "02"): "China Mobile",   ("460", "03"): "China Telecom",
    ("460", "05"): "China Telecom",  ("460", "06"): "China Unicom",
    ("460", "07"): "China Mobile",   ("460", "11"): "China Telecom",
    # ── Australia ──────────────────────────────────────────
    ("505", "01"): "Telstra Australia", ("505", "02"): "Optus Australia",
    ("505", "03"): "Vodafone Australia",("505", "06"): "Telstra Australia",
    # ── Canada ─────────────────────────────────────────────
    ("302", "220"): "Telus Canada",  ("302", "320"): "Rogers Canada",
    ("302", "370"): "Fido Canada",   ("302", "490"): "WIND Canada",
    ("302", "610"): "Bell Canada",   ("302", "720"): "Rogers Canada",
    # ── Germany ────────────────────────────────────────────
    ("262", "01"): "T-Mobile Germany", ("262", "02"): "Vodafone Germany",
    ("262", "03"): "O2 Germany",       ("262", "07"): "O2 Germany",
    # ── France ─────────────────────────────────────────────
    ("208", "01"): "Orange France",  ("208", "10"): "SFR France",
    ("208", "15"): "Free Mobile France",("208", "20"): "Bouygues France",
    # ── UAE ────────────────────────────────────────────────
    ("424", "02"): "Etisalat UAE",   ("424", "03"): "du UAE",
    # ── Saudi Arabia ───────────────────────────────────────
    ("420", "01"): "STC Saudi",      ("420", "03"): "Mobily Saudi",
    ("420", "04"): "Zain Saudi",
    # ── Nigeria ────────────────────────────────────────────
    ("621", "20"): "Airtel Nigeria", ("621", "30"): "MTN Nigeria",
    ("621", "50"): "Glo Nigeria",    ("621", "60"): "9mobile Nigeria",
    # ── South Africa ───────────────────────────────────────
    ("655", "01"): "Vodacom SA",     ("655", "07"): "Cell C SA",
    ("655", "10"): "MTN SA",         ("655", "21"): "Neotel SA",
    # ── Brazil ─────────────────────────────────────────────
    ("724", "05"): "Claro Brazil",   ("724", "06"): "Vivo Brazil",
    ("724", "10"): "TIM Brazil",     ("724", "11"): "Vivo Brazil",
    # ── Japan ──────────────────────────────────────────────
    ("440", "10"): "NTT Docomo",     ("440", "20"): "SoftBank Japan",
    ("440", "50"): "KDDI Japan",     ("440", "51"): "KDDI Japan",
    # ── South Korea ────────────────────────────────────────
    ("450", "05"): "SKT Korea",      ("450", "08"): "KT Korea",
    ("450", "11"): "LG U+ Korea",
    # ── Singapore ──────────────────────────────────────────
    ("525", "01"): "Singtel",        ("525", "03"): "StarHub",
    ("525", "05"): "M1 Singapore",
    # ── Malaysia ───────────────────────────────────────────
    ("502", "12"): "Maxis Malaysia", ("502", "13"): "Celcom Malaysia",
    ("502", "16"): "Digi Malaysia",  ("502", "19"): "Celcom Malaysia",
}


def get_operator(mcc, mnc):
    """Lookup operator name from MCC/MNC."""
    if not mcc or not mnc:
        return "Unknown"
    # Try with leading zeros stripped and with padding
    key = (str(mcc), str(mnc))
    return OPERATORS.get(key, OPERATORS.get((str(mcc), str(mnc).zfill(2)), "Unknown Operator"))


# ══════════════════════════════════════════════════════════
#   BANNER
# ══════════════════════════════════════════════════════════

BANNER = r"""
 ██████╗███████╗██╗     ██╗    ████████╗ ██████╗ ██╗    ██╗███████╗██████╗
██╔════╝██╔════╝██║     ██║       ██║   ██╔═══██╗██║    ██║██╔════╝██╔══██╗
██║     █████╗  ██║     ██║       ██║   ██║   ██║██║ █╗ ██║█████╗  ██████╔╝
██║     ██╔══╝  ██║     ██║       ██║   ██║   ██║██║███╗██║██╔══╝  ██╔══██╗
╚██████╗███████╗███████╗███████╗  ██║   ╚██████╔╝╚███╔███╔╝███████╗██║  ██║
 ╚═════╝╚══════╝╚══════╝╚══════╝  ╚═╝    ╚═════╝  ╚══╝╚══╝╚══════╝╚═╝  ╚═╝
  ██████╗ ███████╗██╗███╗   ██╗████████╗
 ██╔═══██╗██╔════╝██║████╗  ██║╚══██╔══╝
 ██║   ██║███████╗██║██╔██╗ ██║   ██║
 ██║   ██║╚════██║██║██║╚██╗██║   ██║
 ╚██████╔╝███████║██║██║ ╚████║   ██║
  ╚═════╝ ╚══════╝╚═╝╚═╝  ╚═══╝   ╚═╝
        [ 4G/5G SIGINT/GEOINT Mapping Tool v{} ]
        [ Author: rob-OSINT | Platform: Kali  ]
""".format(VERSION)


# ══════════════════════════════════════════════════════════
#   HELPERS
# ══════════════════════════════════════════════════════════

def print_banner():
    if RICH:
        console.print(Panel(BANNER, style="bold cyan", border_style="bright_blue"))
    else:
        print(BANNER)


def cprint(msg, style="white", prefix=""):
    if RICH:
        console.print(f"{prefix} {msg}", style=style)
    else:
        print(f"{prefix} {msg}")


def alert(msg, level="info"):
    icons   = {"info": "[*]", "warn": "[!]", "crit": "[!!!]", "ok": "[+]", "err": "[-]"}
    styles  = {"info": "cyan", "warn": "yellow", "crit": "bold red", "ok": "green", "err": "red"}
    icon    = icons.get(level, "[*]")
    style   = styles.get(level, "white")
    cprint(msg, style=style, prefix=icon)


def timestamp():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ══════════════════════════════════════════════════════════
#   CONNECTION MODE DETECTION
# ══════════════════════════════════════════════════════════

def detect_usb_interface():
    try:
        result = subprocess.run(["ip", "link", "show"], capture_output=True, text=True)
        for line in result.stdout.split("\n"):
            for iface in ["usb0", "usb1", "rndis0", "enp0s20u1"]:
                if iface in line:
                    alert(f"USB tethering detected: {iface}", "ok")
                    return iface
    except Exception:
        pass
    return None


def detect_adb_device():
    try:
        result = subprocess.run(["adb", "devices"], capture_output=True, text=True)
        lines = [l for l in result.stdout.strip().split("\n")[1:] if l.strip() and "offline" not in l]
        if lines:
            device_id = lines[0].split("\t")[0]
            alert(f"ADB device detected: {device_id}", "ok")
            return device_id
    except FileNotFoundError:
        alert("ADB not found. Install with: sudo apt install adb", "warn")
    except Exception:
        pass
    return None


def get_connection_mode():
    alert("Scanning for connected devices...", "info")
    usb = detect_usb_interface()
    adb = detect_adb_device()

    if not usb and not adb:
        alert("No device found! Connect phone via USB with tethering or ADB enabled.", "err")
        return None, None

    if usb and adb:
        alert("Both USB tethering and ADB available.", "ok")
        if RICH:
            mode = Prompt.ask("Select mode", choices=["usb", "adb"], default="adb")
        else:
            mode = input("Select mode [usb/adb] (default: adb): ").strip() or "adb"
        return mode, adb if mode == "adb" else usb

    if adb:
        return "adb", adb
    return "usb", usb


# ══════════════════════════════════════════════════════════
#   CELL DATA EXTRACTION
# ══════════════════════════════════════════════════════════

def get_cell_info_adb(device_id):
    try:
        cmd = ["adb", "-s", device_id, "shell", "dumpsys", "telephony.registry"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return parse_telephony_dump(result.stdout)
    except subprocess.TimeoutExpired:
        alert("ADB command timed out.", "warn")
    except Exception as e:
        alert(f"ADB error: {e}", "err")
    return None


def parse_telephony_dump(dump):
    import re
    info = {
        "mcc": None, "mnc": None, "lac": None,
        "cid": None,  "rsrp": None, "rat": "Unknown",
        "timestamp": timestamp()
    }

    def extract_val(pattern, text):
        m = re.search(pattern, text)
        return m.group(1) if m else None

    info["mcc"]  = extract_val(r'mMcc=(\d+)', dump)
    info["mnc"]  = extract_val(r'mMnc=(\d+)', dump)

    tac = extract_val(r'mTac=(\d+)', dump)
    lac = extract_val(r'mLac=(\d+)', dump)
    info["lac"]  = tac or lac

    cid = extract_val(r'mCi=(\d+)', dump)
    if not cid:
        cid = extract_val(r'mCid=(\d+)', dump)
    if not cid:
        cid = extract_val(r'cellId=(\d+)', dump)
    info["cid"] = cid

    rsrp = extract_val(r'mRsrp=(-?\d+)', dump)
    if rsrp:
        try:
            info["rsrp"] = int(rsrp)
        except ValueError:
            pass

    if "NR" in dump or "5G" in dump:
        info["rat"] = "5G-NR"
    elif "LTE" in dump:
        info["rat"] = "4G-LTE"
    elif "UMTS" in dump or "WCDMA" in dump:
        info["rat"] = "3G"
    elif "EDGE" in dump or "GPRS" in dump:
        info["rat"] = "2G"

    return info if info["mcc"] else None


def _extract(line, key):
    try:
        part = line.split(key)[1]
        return part.split()[0].strip(",;")
    except (IndexError, AttributeError):
        return None


def get_cell_info_usb(interface):
    info = {
        "mcc": None, "mnc": None, "lac": None,
        "cid": None,  "rsrp": None, "rat": "Unknown",
        "timestamp": timestamp()
    }

    serial_ports = ["/dev/ttyUSB0", "/dev/ttyUSB1", "/dev/ttyACM0", "/dev/ttyACM1"]
    for port in serial_ports:
        if Path(port).exists():
            try:
                import serial
                with serial.Serial(port, 115200, timeout=2) as ser:
                    ser.write(b"AT+CREG?\r")
                    time.sleep(0.5)
                    response = ser.read(ser.in_waiting).decode(errors="ignore")
                    if "+CREG" in response:
                        alert(f"AT interface active on {port}", "ok")
                        info["rat"] = "4G-LTE"
                        return info
            except Exception:
                continue

    alert("USB mode: limited data available without AT interface.", "warn")
    return info


# ══════════════════════════════════════════════════════════
#   OPENCELLID LOOKUP
# ══════════════════════════════════════════════════════════

def lookup_opencellid(mcc, mnc, lac, cid, rat="LTE"):
    if OPENCELLID_API_KEY == "YOUR_API_KEY_HERE":
        alert("OpenCellID API key not set. Select option [3] from the menu.", "warn")
        return None

    radio = "NR" if "5G" in str(rat) else "LTE"
    params = {
        "key":    OPENCELLID_API_KEY,
        "mcc":    mcc,
        "mnc":    mnc,
        "lac":    lac,
        "cellid": cid,
        "radio":  radio,
        "format": "json"
    }

    try:
        r = requests.get(OPENCELLID_URL, params=params, timeout=8)
        data = r.json()
        if "lat" in data and "lon" in data:
            return {"lat": data["lat"], "lon": data["lon"], "range": data.get("range", 0)}
    except requests.RequestException as e:
        alert(f"OpenCellID lookup failed: {e}", "warn")
    except json.JSONDecodeError:
        alert("OpenCellID returned invalid response.", "warn")

    return None


# ══════════════════════════════════════════════════════════
#   STINGRAY / IMSI CATCHER DETECTION
# ══════════════════════════════════════════════════════════

class StingrayDetector:
    def __init__(self):
        self.history      = []
        self.known_towers = {}
        self.alerts       = []

    def analyze(self, cell_info, geo_info=None):
        findings = []

        rsrp = cell_info.get("rsrp")
        cid  = cell_info.get("cid")
        mcc  = cell_info.get("mcc")
        mnc  = cell_info.get("mnc")
        rat  = cell_info.get("rat", "Unknown")

        # Rule 1: Signal too weak
        if rsrp and rsrp < RSRP_RED_ALERT:
            findings.append({
                "rule": "WEAK_SIGNAL",
                "severity": "HIGH",
                "detail": f"RSRP {rsrp} dBm is critically weak — possible forced downgrade"
            })
        elif rsrp and rsrp < RSRP_YELLOW_ALERT:
            findings.append({
                "rule": "LOW_SIGNAL",
                "severity": "MEDIUM",
                "detail": f"RSRP {rsrp} dBm is below normal threshold"
            })

        # Rule 2: Ghost tower
        if geo_info is None and cid:
            findings.append({
                "rule": "GHOST_TOWER",
                "severity": "HIGH",
                "detail": f"Cell ID {cid} has no OpenCellID entry — possible rogue tower"
            })

        # Rule 3: Cell ID changed
        if len(self.history) >= 2:
            prev = self.history[-1]
            if prev.get("cid") != cid and prev.get("mcc") == mcc and prev.get("mnc") == mnc:
                findings.append({
                    "rule": "CID_CHANGE",
                    "severity": "MEDIUM",
                    "detail": f"Cell ID changed: {prev.get('cid')} → {cid}"
                })

        # Rule 4: Forced downgrade
        if len(self.history) >= 1:
            prev_rat = self.history[-1].get("rat", "")
            if ("4G" in prev_rat or "5G" in prev_rat) and ("2G" in rat or "3G" in rat):
                findings.append({
                    "rule": "RAT_DOWNGRADE",
                    "severity": "CRITICAL",
                    "detail": f"Network downgraded: {prev_rat} → {rat} — classic IMSI catcher signature"
                })

        # Rule 5: Signal spike
        if rsrp and len(self.history) >= 1:
            prev_rsrp = self.history[-1].get("rsrp")
            if prev_rsrp and (rsrp - prev_rsrp) > 20:
                findings.append({
                    "rule": "RSRP_SPIKE",
                    "severity": "MEDIUM",
                    "detail": f"Sudden signal spike: {prev_rsrp} → {rsrp} dBm"
                })

        self.history.append(cell_info)
        if len(self.history) > 50:
            self.history.pop(0)

        return findings


# ══════════════════════════════════════════════════════════
#   EXPORT — CSV & KML
# ══════════════════════════════════════════════════════════

class Exporter:
    def __init__(self):
        ts            = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.csv_path = OUTPUT_DIR / f"celltower_{ts}.csv"
        self.kml_path = OUTPUT_DIR / f"celltower_{ts}.kml"
        self.records  = []
        self._init_csv()
        self._init_kml()

    def _init_csv(self):
        with open(self.csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "timestamp","mcc","mnc","lac","cid","rat",
                "rsrp","lat","lon","range","alerts"
            ])
            writer.writeheader()

    def _init_kml(self):
        with open(self.kml_path, "w") as f:
            f.write("""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document>
  <n>CellTower-OSINT Scan</n>
  <Style id="normal"><IconStyle><color>ff00ff00</color></IconStyle></Style>
  <Style id="alert"><IconStyle><color>ff0000ff</color></IconStyle></Style>
""")

    def write(self, cell_info, geo_info, findings):
        lat    = geo_info["lat"]   if geo_info else ""
        lon    = geo_info["lon"]   if geo_info else ""
        rng    = geo_info["range"] if geo_info else ""
        alerts = "|".join([f["rule"] for f in findings]) if findings else "NONE"

        row = {**cell_info, "lat": lat, "lon": lon, "range": rng, "alerts": alerts}
        with open(self.csv_path, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "timestamp","mcc","mnc","lac","cid","rat",
                "rsrp","lat","lon","range","alerts"
            ])
            writer.writerow(row)

        if lat and lon:
            style = "#alert" if findings else "#normal"
            desc  = f"MCC:{cell_info.get('mcc')} MNC:{cell_info.get('mnc')} " \
                    f"CID:{cell_info.get('cid')} RSRP:{cell_info.get('rsrp')}dBm"
            with open(self.kml_path, "a") as f:
                f.write(f"""  <Placemark>
    <n>Cell {cell_info.get('cid')}</n>
    <description>{desc}</description>
    <styleUrl>{style}</styleUrl>
    <Point><coordinates>{lon},{lat},0</coordinates></Point>
  </Placemark>\n""")

        self.records.append(row)

    def close_kml(self):
        with open(self.kml_path, "a") as f:
            f.write("</Document>\n</kml>\n")


# ══════════════════════════════════════════════════════════
#   DISPLAY — RICH TABLE
# ══════════════════════════════════════════════════════════

def build_table(records, detector):
    if not RICH:
        return

    table = Table(
        title="📡 CellTower-OSINT — Live Scan",
        box=box.DOUBLE_EDGE,
        border_style="bright_blue",
        header_style="bold magenta"
    )

    table.add_column("Time",     style="dim",          width=20)
    table.add_column("RAT",      style="cyan",         width=8)
    table.add_column("MCC/MNC",  style="white",        width=10)
    table.add_column("Operator", style="bright_cyan",  width=18)
    table.add_column("LAC/TAC",  style="white",        width=10)
    table.add_column("Cell ID",  style="bright_white", width=12)
    table.add_column("RSRP",     style="green",        width=10)
    table.add_column("Coords",   style="yellow",       width=22)
    table.add_column("Status",   style="red",          width=20)

    for r in records[-15:]:
        rsrp_val = r.get("rsrp", None)
        if rsrp_val is not None and isinstance(rsrp_val, int):
            if rsrp_val < RSRP_RED_ALERT:
                rsrp_str = f"[bold red]{rsrp_val} dBm[/bold red]"
            elif rsrp_val < RSRP_YELLOW_ALERT:
                rsrp_str = f"[yellow]{rsrp_val} dBm[/yellow]"
            else:
                rsrp_str = f"[green]{rsrp_val} dBm[/green]"
        else:
            rsrp_str = "N/A"

        alerts = r.get("alerts", "NONE")
        status = f"[bold red]⚠ {alerts}[/bold red]" if alerts != "NONE" else "[green]✓ CLEAN[/green]"
        coords = f"{r.get('lat', '')}, {r.get('lon', '')}" if r.get("lat") else "Not resolved"
        operator = get_operator(r.get("mcc"), r.get("mnc"))

        table.add_row(
            str(r.get("timestamp", ""))[:19],
            str(r.get("rat", "N/A")),
            f"{r.get('mcc','?')}/{r.get('mnc','?')}",
            operator,
            str(r.get("lac", "N/A")),
            str(r.get("cid", "N/A")),
            rsrp_str,
            coords,
            status
        )

    return table


# ══════════════════════════════════════════════════════════
#   MAIN SCAN LOOP
# ══════════════════════════════════════════════════════════

def scan_loop(mode, device, continuous=True):
    detector = StingrayDetector()
    exporter = Exporter()

    alert(f"Output CSV : {exporter.csv_path}", "ok")
    alert(f"Output KML : {exporter.kml_path}", "ok")
    alert(f"Mode       : {mode.upper()}", "ok")
    alert(f"Interval   : {SCAN_INTERVAL}s", "ok")
    print()

    scan_count = 0

    try:
        while True:
            scan_count += 1
            alert(f"Scan #{scan_count} — {timestamp()}", "info")

            if mode == "adb":
                cell_info = get_cell_info_adb(device)
            else:
                cell_info = get_cell_info_usb(device)

            if not cell_info:
                alert("No cell data retrieved. Retrying...", "warn")
                time.sleep(SCAN_INTERVAL)
                continue

            geo_info = None
            if all([cell_info.get(k) for k in ["mcc","mnc","lac","cid"]]):
                alert(f"Looking up CID {cell_info['cid']} on OpenCellID...", "info")
                geo_info = lookup_opencellid(
                    cell_info["mcc"], cell_info["mnc"],
                    cell_info["lac"], cell_info["cid"],
                    cell_info.get("rat","LTE")
                )
                if geo_info:
                    alert(f"Tower located: {geo_info['lat']}, {geo_info['lon']}", "ok")
                else:
                    alert("Tower not found in OpenCellID database.", "warn")

            findings = detector.analyze(cell_info, geo_info)
            if findings:
                for f in findings:
                    sev = f["severity"]
                    lvl = "crit" if sev == "CRITICAL" else "warn"
                    alert(f"[{sev}] {f['rule']}: {f['detail']}", lvl)
            else:
                alert("No anomalies detected.", "ok")

            exporter.write(cell_info, geo_info, findings)

            if RICH:
                console.clear()
                print_banner()
                tbl = build_table(exporter.records, detector)
                console.print(tbl)
                console.print(f"\n[dim]Scanning every {SCAN_INTERVAL}s | Press Ctrl+C to stop[/dim]")

            if not continuous:
                break

            time.sleep(SCAN_INTERVAL)

    except KeyboardInterrupt:
        print()
        alert("Scan stopped by user.", "warn")
    finally:
        exporter.close_kml()
        alert(f"Results saved to {OUTPUT_DIR}/", "ok")
        alert(f"Total scans: {scan_count}", "ok")


# ══════════════════════════════════════════════════════════
#   INTERACTIVE MENU
# ══════════════════════════════════════════════════════════

def show_menu():
    if RICH:
        console.print(Panel.fit(
            "[1] Start continuous scan\n"
            "[2] Single scan\n"
            "[3] Set OpenCellID API key\n"
            "[4] View last output\n"
            "[5] Exit",
            title="[bold cyan]Main Menu[/bold cyan]",
            border_style="blue"
        ))
        choice = Prompt.ask("Select option", choices=["1","2","3","4","5"])
    else:
        print("\n[1] Start continuous scan")
        print("[2] Single scan")
        print("[3] Set OpenCellID API key")
        print("[4] View last output")
        print("[5] Exit")
        choice = input("\nSelect option [1-5]: ").strip()

    return choice


def view_last_output():
    files = sorted(OUTPUT_DIR.glob("celltower_*.csv"), reverse=True)
    if not files:
        alert("No output files found yet.", "warn")
        return

    latest = files[0]
    alert(f"Showing: {latest}", "ok")

    with open(latest) as f:
        reader = csv.DictReader(f)
        rows   = list(reader)

    if RICH:
        table = Table(title=str(latest), box=box.SIMPLE, border_style="blue")
        for field in reader.fieldnames or []:
            table.add_column(field, style="cyan")
        for row in rows[-20:]:
            table.add_row(*[str(row.get(k,"")) for k in reader.fieldnames])
        console.print(table)
    else:
        for row in rows[-20:]:
            print(row)


def set_api_key():
    global OPENCELLID_API_KEY
    if RICH:
        key = Prompt.ask("Enter your OpenCellID API key")
    else:
        key = input("Enter your OpenCellID API key: ").strip()

    if key:
        OPENCELLID_API_KEY = key
        src     = Path(__file__)
        content = src.read_text()
        content = content.replace('YOUR_API_KEY_HERE', key)
        src.write_text(content)
        alert("API key saved successfully!", "ok")


# ══════════════════════════════════════════════════════════
#   ENTRY POINT
# ══════════════════════════════════════════════════════════

def main():
    global SCAN_INTERVAL

    parser = argparse.ArgumentParser(
        description="CellTower-OSINT — 4G/5G SIGINT/GEOINT Tool"
    )
    parser.add_argument("--mode",     choices=["usb","adb","auto"], default="auto")
    parser.add_argument("--once",     action="store_true", help="Single scan then exit")
    parser.add_argument("--interval", type=int, default=SCAN_INTERVAL)
    parser.add_argument("--no-menu",  action="store_true", help="Skip menu, scan immediately")
    args = parser.parse_args()

    SCAN_INTERVAL = args.interval

    print_banner()

    if not RICH:
        alert("Tip: Install 'rich' for full UI → pip install rich", "info")

    if args.mode == "auto" or not args.no_menu:
        mode, device = get_connection_mode()
        if not mode:
            sys.exit(1)
    else:
        mode   = args.mode
        device = None

    if args.no_menu:
        scan_loop(mode, device, continuous=not args.once)
        return

    while True:
        choice = show_menu()

        if choice == "1":
            scan_loop(mode, device, continuous=True)
        elif choice == "2":
            scan_loop(mode, device, continuous=False)
        elif choice == "3":
            set_api_key()
        elif choice == "4":
            view_last_output()
        elif choice == "5":
            alert("Goodbye.", "ok")
            sys.exit(0)


if __name__ == "__main__":
    main()
