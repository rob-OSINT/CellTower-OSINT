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
#   BANNER
# ══════════════════════════════════════════════════════════

BANNER = r"""
 ██████╗███████╗██╗     ██╗    ████████╗ ██████╗ ██╗    ██╗███████╗██████╗
██╔════╝██╔════╝██║     ██║       ██║   ██╔═══██╗██║    ██║██╔════╝██╔══██╗
██║     █████╗  ██║     ██║       ██║   ██║   ██║██║ █╗ ██║█████╗  ██████╔╝
██║     ██╔══╝  ██║     ██║       ██║   ██║   ██║██║███╗██║██╔══╝  ██╔══██╗
╚██████╗███████╗███████╗███████╗  ██║   ╚██████╔╝╚███╔███╔╝███████╗██║  ██║
 ╚═════╝╚══════╝╚══════╝╚══════╝  ╚═╝    ╚═════╝  ╚══╝╚══╝╚══════╝╚═╝  ╚═╝
   ██████╗ ███████╗██╗███╗   ██╗████████╗  v{}  |  rob-OSINT
   ██╔══██╗██╔════╝██║████╗  ██║╚══██╔══╝  4G/5G SIGINT/GEOINT Tool
   ██║  ██║███████╗██║██╔██╗ ██║   ██║     Platform: Kali Linux
   ╚═════╝ ╚══════╝╚═╝╚═╝  ╚═══╝   ╚═╝
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

    table.add_column("Time",    style="dim",          width=20)
    table.add_column("RAT",     style="cyan",         width=8)
    table.add_column("MCC/MNC", style="white",        width=10)
    table.add_column("LAC/TAC", style="white",        width=10)
    table.add_column("Cell ID", style="bright_white", width=12)
    table.add_column("RSRP",    style="green",        width=10)
    table.add_column("Coords",  style="yellow",       width=22)
    table.add_column("Status",  style="red",          width=20)

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

        table.add_row(
            str(r.get("timestamp", ""))[:19],
            str(r.get("rat", "N/A")),
            f"{r.get('mcc','?')}/{r.get('mnc','?')}",
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
