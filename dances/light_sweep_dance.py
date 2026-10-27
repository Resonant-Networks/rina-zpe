import os
#!/usr/bin/env python3
"""
Light sweep dance for ZPE Nodegrid.
Turn on ports in order: 1,3,5,7,2,4,6,8 (top row left->right, then bottom row left->right)
Turn off ports in reverse order: 8,6,4,2,7,5,3,1
Each port stays on after being turned on until its turn to turn off.
Usage: source /opt/hermes/.venv/bin/activate && python3 /opt/data/light_sweep_dance.py
"""

import json
import sys
import time
import urllib3
from urllib3.exceptions import InsecureRequestWarning

# Suppress only the single warning from urllib3 needed.
urllib3.disable_warnings(InsecureRequestWarning)
# Create a pool manager that disables SSL verification (self-signed cert)
http = urllib3.PoolManager(cert_reqs='CERT_NONE')

BASE_URL = "https://192.168.72.18"
USERNAME = "admin"
PASSWORD = os.environ.get("NODEGRID_PASSWORD", "")
REQUEST_TIMEOUT = 15.0  # seconds

# Physical order for a serpentine (snake) walk: top row left→right, then bottom row right→left
SNAKE_PATH = [
    "ttyS1-router1",  # ttyS1
    "ttyS3",          # ttyS3
    "xmm4-2-1",       # ttyS5
    "ttyS7",          # ttyS7
    "ttyS8",          # ttyS8
    "EDcore",         # ttyS6
    "TestMTC",        # ttyS4
    "ttyS2",          # ttyS2
]

# Mapping from port label to device ID used in the script
PORT_MAP = {
    "P1": "ttyS1-router1",
    "P2": "ttyS2",
    "P3": "ttyS3",
    "P4": "TestMTC",
    "P5": "xmm4-2-1",
    "P6": "EDcore",
    "P7": "ttyS7",
    "P8": "ttyS8",
}

# Desired sequences
ON_SEQUENCE = ["P1", "P3", "P5", "P7", "P2", "P4", "P6", "P8"]
OFF_SEQUENCE = ["P8", "P6", "P4", "P2", "P7", "P5", "P3", "P1"]

def get_ticket():
    """Authenticate and return the session ticket."""
    url = f"{BASE_URL}/api/v1/Session"
    resp = http.request(
        "POST",
        url,
        headers={"Content-Type": "application/json"},
        body=json.dumps({"username": USERNAME, "password": PASSWORD}),
        retries=False,
        timeout=REQUEST_TIMEOUT,
    )
    if resp.status != 200:
        raise RuntimeError(f"Login failed: {resp.status} {resp.data}")
    data = json.loads(resp.data.decode("utf-8"))
    return data["session"]

def put(ticket, endpoint, payload=None):
    """Generic PUT helper."""
    url = f"{BASE_URL}{endpoint}"
    headers = {"ticket": ticket, "Content-Type": "application/json"}
    body = json.dumps(payload) if payload is not None else None
    resp = http.request(
        "PUT",
        url,
        headers=headers,
        body=body,
        retries=False,
        timeout=REQUEST_TIMEOUT,
    )
    if resp.status not in (200, 204):
        raise RuntimeError(f"PUT {endpoint} failed: {resp.status} {resp.data}")
    return resp

def enable(ticket, device):
    put(ticket, f"/api/v1/devices/table/{device}/enable")

def disable(ticket, device):
    put(ticket, f"/api/v1/devices/table/{device}/disable")

def light_sweep(delay=0.2, cycles=1):
    ticket = get_ticket()
    try:
        # Ensure all ports start disabled
        for dev in SNAKE_PATH:
            disable(ticket, dev)

        for c in range(cycles):
            print(f"[*] Cycle {c+1}/{cycles} – light sweep")
            # Turn on ports in ON_SEQUENCE, leaving previous ones on
            for label in ON_SEQUENCE:
                device = PORT_MAP[label]
                enable(ticket, device)
                print(f"  [ON]  {label} ({device})")
                time.sleep(delay)
            # Turn off ports in OFF_SEQUENCE
            for label in OFF_SEQUENCE:
                device = PORT_MAP[label]
                disable(ticket, device)
                print(f"  [OFF] {label} ({device})")
                time.sleep(delay)
            print("[*] Dance complete!")
    finally:
        # Cleanup: restore to disabled state (best‑effort)
        for dev in SNAKE_PATH:
            try:
                disable(ticket, dev)
            except Exception:
                pass
        # End session
        try:
            http.request(
                "DELETE",
                f"{BASE_URL}/api/v1/Session",
                headers={"ticket": ticket},
                retries=False,
                timeout=REQUEST_TIMEOUT,
            )
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