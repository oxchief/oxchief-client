#!/usr/bin/env python3
"""
Configure a Unicore UM982 GNSS receiver for use with OxChief.

This talks ONLY to the UM982 over its USB/serial port -- it does NOT touch the
flight controller. (The ArduPilot side is handled by loading the
`cfg/OxChief_Cube_Orange_Bad_Boy_UM982.param` file in Mission Planner.)

What it does:
  - Puts the receiver in MODE ROVER  (the #1 misconfiguration: a UM982 left in
    BASE mode reports GGA quality=7 / a 3D-but-not-RTK fix and never works as a
    rover).
  - Sets COM1/COM2/COM3 to 230400 baud (must match ArduPilot SERIAL3_BAUD=230).
  - Sets NMEA V4.10 and enables the NMEA sentences ArduPilot needs on COM1,
    including UNIHEADINGA/GPHDT which carry the dual-antenna heading.
  - SAVECONFIG so the settings survive a power cycle.
  - Leaves the antenna-specific `CONFIG HEADING` alone (it is calibrated per
    unit and must not be overwritten).

Wiring assumption: the UM982's own USB port is connected to this machine (the
receiver shows up as a CH340 device, USB vendor id 1a86). COM1 TX goes to the
Cube's GPS1 port for navigation; that link is separate from this USB config link.

Run it during setup, BEFORE starting the OxChief client (the client opens the
GPS serial port, so stop the container first if it is already running).

Usage:
    python3 scripts/configure_um982.py                 # auto-detect + configure
    python3 scripts/configure_um982.py --verify-only   # read-only check
    python3 scripts/configure_um982.py --port /dev/ttyUSB0
    python3 scripts/configure_um982.py --baud 230400

Requires pyserial:  pip3 install pyserial
"""

import argparse
import glob
import sys
import time

# COM baud rate the UM982 should use (must match ArduPilot SERIAL3_BAUD=230 -> 230400).
UM982_BAUD = 230400

# NMEA sentences to enable on COM1 (the port wired to the flight controller's GPS1).
# UNIHEADINGA + GPHDT carry the dual-antenna heading; the rest are position/quality.
UM982_NMEA_COMMANDS = [
    "GNGGA COM1 5",
    "GNGSV COM1 5",
    "GNGSA COM1 5",
    "UNIHEADINGA COM1 5",
    "GNRMC COM1 5",
    "GPHDT COM1 5",
]


def find_um982_port():
    """Auto-detect the UM982 USB port by looking for a CH340 (USB vendor 1a86) device."""
    for port in sorted(glob.glob("/dev/ttyUSB*")):
        usb_num = port.replace("/dev/ttyUSB", "")
        for pattern in (
            f"/sys/class/tty/ttyUSB{usb_num}/device/../idVendor",
            f"/sys/class/tty/ttyUSB{usb_num}/device/../../idVendor",
        ):
            try:
                with open(pattern) as f:
                    if f.read().strip() == "1a86":
                        return port
            except (IOError, OSError):
                continue
    return None


class UM982:
    """Minimal serial conversation with a Unicore UM982 receiver."""

    def __init__(self, port, baud=UM982_BAUD):
        import serial
        self.port = port
        self.ser = None
        # The UM982 may currently be at a different baud; probe the common ones.
        for try_baud in (baud, 115200, 9600):
            try:
                self.ser = serial.Serial(port, try_baud, timeout=1)
                time.sleep(0.3)
                self.ser.reset_input_buffer()
                if "MODE" in self._send("MODE").upper():
                    if try_baud != baud:
                        print(f"  note: UM982 currently at {try_baud} baud")
                    return
                self.ser.close()
            except Exception:
                if self.ser:
                    self.ser.close()
        raise RuntimeError(f"Could not talk to a UM982 on {port} at any baud rate")

    def close(self):
        if self.ser and self.ser.is_open:
            self.ser.close()

    def _send(self, cmd, timeout=2):
        self.ser.reset_input_buffer()
        self.ser.write((cmd + "\r\n").encode())
        time.sleep(0.5)
        data, start = b"", time.time()
        while time.time() - start < timeout:
            chunk = self.ser.read(4096)
            if chunk:
                data += chunk
            elif data:
                break
        return data.decode("ascii", errors="replace")

    def _send_ok(self, cmd):
        return "OK" in self._send(cmd)

    def get_mode(self):
        for line in self._send("MODE").split("\n"):
            if line.strip().startswith("#MODE"):
                parts = line.split(";")
                if len(parts) >= 2:
                    return parts[1].split(",")[0].strip()
        return "UNKNOWN"

    def get_config(self):
        cfg = {}
        for line in self._send("CONFIG", timeout=3).split("\n"):
            line = line.strip()
            if line.startswith("$CONFIG,"):
                parts = line.split(",", 2)
                if len(parts) >= 3:
                    cfg[parts[1]] = parts[2].split("*")[0].strip()
        return cfg

    def configure(self):
        print(f"\n=== Configuring UM982 on {self.port} ===")

        mode = self.get_mode()
        if "ROVER" in mode.upper():
            print(f"[mode] {mode} ... already ROVER")
        else:
            print(f"[mode] currently {mode} -- switching to ROVER")
            if not self._send_ok("MODE ROVER"):
                print("[mode] FAILED to set MODE ROVER")
                return False

        for com in ("COM1", "COM2", "COM3"):
            ok = self._send_ok(f"CONFIG {com} {UM982_BAUD}")
            print(f"[baud] CONFIG {com} {UM982_BAUD} ... {'OK' if ok else 'FAILED'}")

        ok = self._send_ok("CONFIG NMEAVERSION V410")
        print(f"[nmea] CONFIG NMEAVERSION V410 ... {'OK' if ok else 'FAILED'}")

        # Heading config is antenna-specific and calibrated per unit -- read, never write.
        heading = [v for k, v in self.get_config().items() if "HEADING" in k.upper()]
        if heading:
            print("[head] existing CONFIG HEADING preserved:")
            for h in heading:
                print(f"       {h}")
        else:
            print("[head] WARNING: no CONFIG HEADING found -- dual-antenna heading "
                  "needs a one-time CONFIG HEADING setup (see UM982_GPS_SETUP.md)")

        print("[out ] enabling NMEA output on COM1:")
        for cmd in UM982_NMEA_COMMANDS:
            ok = self._send_ok(cmd)
            print(f"       {cmd} ... {'OK' if ok else 'FAILED'}")

        if not self._send_ok("SAVECONFIG"):
            print("[save] SAVECONFIG ... FAILED")
            return False
        print("[save] SAVECONFIG ... OK")

        if "ROVER" not in self.get_mode().upper():
            print("[verify] ERROR: not in ROVER mode after configuration")
            return False
        print("\nUM982 configuration complete.")
        return True

    def verify(self):
        print(f"\n=== Verifying UM982 on {self.port} ===")
        ok = True

        mode = self.get_mode()
        rover = "ROVER" in mode.upper()
        print(f"[mode] {mode} ... {'OK' if rover else 'MISMATCH (expected ROVER)'}")
        ok &= rover

        cfg = self.get_config()
        for com in ("COM1", "COM2", "COM3"):
            match = str(UM982_BAUD) in cfg.get(com, "")
            print(f"[baud] {com}: {cfg.get(com, '?')} ... {'OK' if match else 'MISMATCH'}")
            ok &= match

        has_heading = any("HEADING" in k.upper() for k in cfg)
        print(f"[head] CONFIG HEADING ... {'present' if has_heading else 'MISSING'}")
        ok &= has_heading

        return ok


def main():
    p = argparse.ArgumentParser(description="Configure a Unicore UM982 for OxChief")
    p.add_argument("--port", help="UM982 serial port (auto-detected if omitted)")
    p.add_argument("--baud", type=int, default=UM982_BAUD, help="probe baud (default 230400)")
    p.add_argument("--verify-only", action="store_true", help="read-only check, no changes")
    args = p.parse_args()

    port = args.port or find_um982_port()
    if not port:
        print("ERROR: could not find a UM982 (CH340 / USB 1a86) on /dev/ttyUSB*.")
        avail = sorted(glob.glob("/dev/ttyUSB*") + glob.glob("/dev/ttyACM*"))
        if avail:
            print(f"       available ports: {', '.join(avail)}")
        print("       connect the UM982's USB to this machine, or pass --port.")
        return 1

    try:
        um = UM982(port, baud=args.baud)
    except Exception as e:
        print(f"ERROR: {e}")
        return 1

    try:
        ok = um.verify() if args.verify_only else um.configure()
    finally:
        um.close()
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
