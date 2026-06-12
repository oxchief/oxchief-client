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
  - Dual-antenna heading is ENABLED BY DEFAULT on the UM982, so no heading-
    enable command is needed. Optionally tune it for your install with
    --baseline-cm (measured antenna spacing) and/or --heading-offset (when the
    antenna line is not along the vehicle's forward axis).

Wiring assumption: the UM982's own USB port is connected to this machine. Generic
UM982 boards show up as a CH340 (USB vendor id 1a86); the Holybro H-RTK Unicore
UM982 presents its USB-C config port as an FTDI device (0403). Both are
auto-detected. COM1 TX goes to the Cube's GPS1 port for navigation; that link is
separate from this USB config link.

Run it during setup, BEFORE starting the OxChief client (the client opens the
GPS serial port, so stop the container first if it is already running).

Usage:
    python3 scripts/configure_um982.py                 # auto-detect + configure
    python3 scripts/configure_um982.py --verify-only   # read-only check
    python3 scripts/configure_um982.py --baseline-cm 100   # tell it the 1.0 m baseline
    python3 scripts/configure_um982.py --heading-offset 90 # antennas mounted left-right
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

# USB vendor IDs the UM982 config port shows up as. Generic UM982 boards use a
# CH340 (1a86); the Holybro H-RTK Unicore UM982 presents its USB-C config port as
# an FTDI device (0403, e.g. 0403:6015). Accept both.
UM982_USB_VENDOR_IDS = ("1a86", "0403")

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


def _port_vendor_id(port):
    """Return the USB idVendor (lowercase hex string) for a /dev/ttyUSB* port, or None."""
    usb_num = port.replace("/dev/ttyUSB", "")
    for pattern in (
        f"/sys/class/tty/ttyUSB{usb_num}/device/../idVendor",
        f"/sys/class/tty/ttyUSB{usb_num}/device/../../idVendor",
    ):
        try:
            with open(pattern) as f:
                return f.read().strip().lower()
        except (IOError, OSError):
            continue
    return None


def find_um982_ports():
    """Auto-detect candidate UM982 USB ports.

    Matches the CH340 (1a86, generic UM982 boards) and FTDI (0403, Holybro H-RTK
    Unicore UM982) USB vendor IDs. Returns a list of matching /dev/ttyUSB* paths
    (there may be more than one when other USB-serial adapters share a vendor).
    """
    return [
        port
        for port in sorted(glob.glob("/dev/ttyUSB*"))
        if _port_vendor_id(port) in UM982_USB_VENDOR_IDS
    ]


def find_um982_port(baud=UM982_BAUD):
    """Return the single UM982 port, probing candidates if more than one matches.

    With one candidate, return it directly (the UM982() constructor verifies it
    can actually talk before doing anything). With several, probe each at the
    UM982 baud rates rather than guessing, and return the first that responds.
    """
    candidates = find_um982_ports()
    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0]
    for port in candidates:
        try:
            UM982(port, baud=baud).close()
            return port
        except Exception:
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

    def configure(self, heading_offset=None, baseline_cm=None, baseline_tol_cm=5):
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

        # Dual-antenna heading is ON BY DEFAULT (Unicore N4 ref manual). We do not
        # need to "enable" it -- only optionally tune it for this install.
        if baseline_cm is not None:
            self._send_ok("CONFIG HEADING FIXLENGTH")
            ok = self._send_ok(f"CONFIG HEADING LENGTH {baseline_cm} {baseline_tol_cm}")
            print(f"[head] CONFIG HEADING LENGTH {baseline_cm} {baseline_tol_cm} "
                  f"(baseline cm / tol cm) ... {'OK' if ok else 'FAILED'}")
        if heading_offset is not None:
            ok = self._send_ok(f"CONFIG HEADING OFFSET {heading_offset} 0")
            print(f"[head] CONFIG HEADING OFFSET {heading_offset} 0 "
                  f"(deg from forward axis) ... {'OK' if ok else 'FAILED'}")
        if baseline_cm is None and heading_offset is None:
            existing = [v for k, v in self.get_config().items() if "HEADING" in k.upper()]
            if existing:
                print("[head] existing CONFIG HEADING (left as-is):")
                for h in existing:
                    print(f"       {h}")
            else:
                print("[head] no explicit CONFIG HEADING -- using the receiver default "
                      "(auto baseline). Heading still works; pass --baseline-cm / "
                      "--heading-offset to tune for your mount.")

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
    p.add_argument("--baseline-cm", type=int, metavar="CM",
                   help="measured ANT1<->ANT2 spacing in cm (rigid mount); sets "
                        "CONFIG HEADING LENGTH to speed/stabilize the heading fix. "
                        "Omit to let the receiver auto-estimate.")
    p.add_argument("--baseline-tol-cm", type=int, default=5, metavar="CM",
                   help="tolerance for --baseline-cm (default 5)")
    p.add_argument("--heading-offset", type=float, metavar="DEG",
                   help="degrees from the vehicle forward axis to the ANT1->ANT2 line "
                        "(e.g. 90 if antennas are mounted left-right, ANT1 on the right); "
                        "sets CONFIG HEADING OFFSET. Omit if ANT1 is forward of ANT2.")
    args = p.parse_args()

    port = args.port or find_um982_port(baud=args.baud)
    if not port:
        print("ERROR: could not find a UM982 (CH340 / USB 1a86, or FTDI / USB 0403) "
              "on /dev/ttyUSB*.")
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
        if args.verify_only:
            ok = um.verify()
        else:
            ok = um.configure(
                heading_offset=args.heading_offset,
                baseline_cm=args.baseline_cm,
                baseline_tol_cm=args.baseline_tol_cm,
            )
    finally:
        um.close()
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
