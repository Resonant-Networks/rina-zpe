#!/usr/bin/env python3
"""
Light sweep dance for ZPE Nodegrid.
Turn on ports in order: 1,3,5,7,2,4,6,8 (top row left->right, then bottom row left->right)
Turn off ports in reverse order: 8,6,4,2,7,5,3,1
Each port stays on after being turned on until its turn to turn off.
"""

import json
import sys
import time
import urllib.request
import urllib.error
import ssl

def make_request(method, url, data=None, ticket=None):
    """Make HTTP request with optional ticket header and JSON data."""
    context = ssl._create_unverified_context()
    headers = {}
    if ticket:
        headers["ticket"] = ticket
    if data is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(req, context=context, timeout=15)
        return resp
    except urllib.error.URLError as e:
        raise RuntimeError(f"Request failed: {e}")

def get_ticket(base, username, password):
    """Authenticate and return the session ticket."""
    url = f"{base}/api/v1/Session"
    resp = make_request("POST", url,
                        data={"username": username, "password": password})
    resp_data = json.load(resp)
    return resp_data.get("session")

def put(ticket, base, endpoint, payload=None):
    """Generic PUT helper."""
    url = f"{base}{endpoint}"
    resp = make_request("PUT", url,
                        data=payload, ticket=ticket)
    try:
        resp.read()
    except Exception:
        pass
    return resp

def enable(ticket, base, device):
    put(ticket, base, f"/api/v1/devices/table/{device}/enable")

def disable(ticket, base, device):
    put(ticket, base, f"/api/v1/devices/table/{device}/disable")

def light_sweep(delay=0.2, cycles=1):
    base = "https://10.15.235.116"
    username = "admin"
    password = ""
    # Physical order for a serpentine (snake) walk: top row left→right, then bottom row right→left
    SNAKE_PATH = [
        "ttyS1-router1",  # ttyS1
        "ttyS3",          # ttyS3
        "ttyS5-42",       # ttyS5
        "ttyS7",          # ttyS7
        "ttyS8",          # ttyS8
        "ttyS6-EDcore",   # ttyS6
        "ttyS4",          # ttyS4
        "ttyS2",          # ttyS2
    ]
    # Mapping from port label to device ID used in the script
    PORT_MAP = {
        "P1": "ttyS1-router1",
        "P2": "ttyS2",
        "P3": "ttyS3",
        "P4": "ttyS4",
        "P5": "ttyS5-42",
        "P6": "ttyS6-EDcore",
        "P7": "ttyS7",
        "P8": "ttyS8",
    }
    # Desired sequences
    ON_SEQUENCE = ["P1", "P3", "P5", "P7", "P2", "P4", "P6", "P8"]
    OFF_SEQUENCE = ["P8", "P6", "P4", "P2", "P7", "P5", "P3", "P1"]

    ticket = get_ticket(base, username, password)
    try:
        # Ensure all ports start disabled
        for dev in SNAKE_PATH:
            disable(ticket, base, dev)

        for c in range(cycles):
            print(f"[*] Cycle {c+1}/{cycles} – light sweep")
            # Turn on ports in ON_SEQUENCE, leaving previous ones on
            for label in ON_SEQUENCE:
                device = PORT_MAP[label]
                enable(ticket, base, device)
                print(f"  [ON]  {label} ({device})")
                time.sleep(delay)
            # Turn off ports in OFF_SEQUENCE
            for label in OFF_SEQUENCE:
                device = PORT_MAP[label]
                disable(ticket, base, device)
                print(f"  [OFF] {label} ({device})")
                time.sleep(delay)
            print("[*] Dance complete!")
    finally:
        # Cleanup: restore to disabled state (best‑effort)
        for dev in SNAKE_PATH:
            try:
                disable(ticket, base, dev)
            except Exception:
                pass
        # End session
        try:
            make_request("DELETE", f"{base}/api/v1/Session", ticket=ticket)
        except Exception:
            pass
        print("[*] Session ended.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Light sweep dance")
    parser.add_argument("-d", "--delay", type=float, default=0.2, help="Delay between enable/disable (seconds)")
    parser.add_argument("-c", "--cycles", type=int, default=1, help="Number of cycles")
    args = parser.parse_args()
    light_sweep(delay=args.delay, cycles=args.cycles)
