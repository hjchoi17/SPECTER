"""SPECTER transmitter.

Encodes a bit string through host-side USB power-management (Linux sysfs)
or device-state (Windows DevCon) operations. The payload is never placed in
USB data transfers. These operations do not by themselves guarantee that
VBUS is physically disconnected; the observable effect depends on the host
controller, hub, driver, and connected device.

Requires root on Linux and administrator privileges on Windows.
"""

import argparse
import math
import os
import platform
import subprocess
import sys
import time

SYSFS_DEVICES = "/sys/bus/usb/devices/"
SYSFS_DRIVER = "/sys/bus/usb/drivers/usb/"

# Values written for the active (bit 1) and inactive (bit 0) control states.
# (attribute, value, required). level and autosuspend are legacy attributes
# that may not exist on newer kernels, so they are written only if present.
ACTIVE = [("level", "on", False), ("autosuspend_delay_ms", "2000", True),
          ("autosuspend", "2", False), ("control", "on", True)]
INACTIVE = [("level", "auto", False), ("autosuspend_delay_ms", "0", True),
            ("autosuspend", "0", False), ("control", "auto", True)]


def sysfs_write(path, value, required):
    if not os.path.exists(path):
        if required:
            sys.exit(f"Required attribute not found: {path}")
        return
    # Issued through sudo tee, as in the original implementation.
    r = subprocess.run(["sudo", "tee", "-a", path], input=(value + "\n").encode(),
                       stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    if r.returncode != 0:
        msg = f"Write failed: {value} -> {path}: {r.stderr.decode().strip()}"
        if required:
            sys.exit(msg)
        print("warning:", msg, file=sys.stderr)


def linux_apply(port, bases, settings):
    for base in bases:
        for attr, value, required in settings:
            sysfs_write(base + port + "/power/" + attr, value, required)
    with open(SYSFS_DEVICES + port + "/power/runtime_status") as f:
        print("runtime_status:", f.read().strip())


def send_linux(msg, port, interval):
    try:
        with open(SYSFS_DEVICES + port + "/manufacturer") as f:
            manufacturer = f.read().strip()
    except OSError as e:
        sys.exit(f"Cannot read manufacturer for port {port!r}: {e}")

    if manufacturer == "SAMSUNG":
        # Writes through both paths. They may resolve to the same device.
        bases = [SYSFS_DRIVER, SYSFS_DEVICES]
    elif manufacturer == "Apple Inc.":
        bases = [SYSFS_DEVICES]
    else:
        sys.exit(f"Unsupported device manufacturer {manufacturer!r}. "
                 "Only the tested Samsung and Apple branches are implemented.")

    for bit in msg:
        print("bit", bit)
        linux_apply(port, bases, ACTIVE if bit == "1" else INACTIVE)
        time.sleep(interval)


def devcon(action, hwid):
    try:
        r = subprocess.run(["devcon", action, hwid], capture_output=True, text=True)
    except FileNotFoundError:
        sys.exit("devcon not found. Install DevCon and add it to PATH.")
    if r.returncode != 0:
        sys.exit(f"devcon {action} {hwid} failed (exit {r.returncode}): "
                 f"{(r.stdout + r.stderr).strip()}")


def enable(hwid):
    # A single enable call did not consistently restore the observable
    # device state in our setup, so it is issued twice.
    devcon("enable", hwid)
    devcon("enable", hwid)


def send_windows(msg, hwid, interval, rf):
    # Initialization sequence used in the experiments.
    enable(hwid)
    devcon("disable", hwid)
    enable(hwid)

    if not rf:
        # State-based encoding: 1 = enabled, 0 = disabled.
        for bit in msg:
            print("bit", bit)
            if bit == "1":
                enable(hwid)
            else:
                devcon("disable", hwid)
            time.sleep(interval)
    else:
        # Event-based encoding: 1 = one state change at the start of the
        # symbol, 0 = no change. devcon() exits on failure, so the tracked
        # state only changes after a successful command.
        enabled = True
        for bit in msg:
            print("bit", bit)
            if bit == "1":
                if enabled:
                    devcon("disable", hwid)
                else:
                    enable(hwid)
                enabled = not enabled
            time.sleep(interval)


def positive_float(s):
    try:
        v = float(s)
    except ValueError:
        raise argparse.ArgumentTypeError(f"not a number: {s!r}")
    if not math.isfinite(v) or v <= 0:
        raise argparse.ArgumentTypeError("must be a finite positive number")
    return v


def main():
    p = argparse.ArgumentParser(description="SPECTER transmitter")
    p.add_argument("-i", "--input", required=True,
                   help="bit string to send, e.g. 101011...")
    p.add_argument("--port",
                   help="Linux: USB device path under /sys/bus/usb/devices, e.g. 1-1")
    p.add_argument("--hwid",
                   help="Windows: hardware ID (or @instance ID) passed to devcon")
    p.add_argument("--interval", type=positive_float,
                   help="software waiting period after each symbol's control "
                        "operations, in seconds (default 5 on Linux, 1 on Windows). "
                        "Command execution time is added on top of this.")
    p.add_argument("--rf", action="store_true",
                   help="Windows: use event-based encoding for the RF receiver")
    args = p.parse_args()

    msg = args.input
    if not msg or set(msg) - {"0", "1"}:
        p.error("input must consist of 0 and 1 only")

    os_name = platform.system()
    if os_name == "Linux":
        if not args.port:
            p.error("--port is required on Linux")
        if args.rf:
            p.error("--rf is implemented for Windows only")
        send_linux(msg, args.port, args.interval if args.interval is not None else 5.0)
    elif os_name == "Windows":
        if not args.hwid:
            p.error("--hwid is required on Windows")
        send_windows(msg, args.hwid,
                     args.interval if args.interval is not None else 1.0, args.rf)
    else:
        sys.exit(f"Unsupported OS: {os_name}")


if __name__ == "__main__":
    main()
