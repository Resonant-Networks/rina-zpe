import os
#!/usr/bin/env python3
"""
Final Ripple dance:
  P1 > P3 > !P1 > P5 > !P3 > P7 > !P5 > P8 > !P7 > P6 > !P8 > P4 > !P6 > P2 > !P4 > !P2

Port mapping:
  P1 -> ttyS1-router1
  P2 -> ttyS2
  P3 -> ttyS3
  P4 -> TestMTC
  P5 -> xmm4-2-1
  P6 -> EDcore
  P7 -> ttyS7
  P8 -> ttyS8
"""

import json
import time
import urllib3
from urllib3.exceptions import InsecureRequestWarning

# Disable SSL warnings (self‑signed certificate)
urllib3.disable_warnings(InsecureRequestWarning)
# HTTP client that does not verify SSL
http = urllib3.PoolManager(cert_reqs='CERT_NONE')

BASE_URL = "https://192.168.72.18"
USERNAME = "admin"
PASSWORD = os.environ.get("NODEGRID_PASSWORD", "")
REQUEST_TIMEOUT = 30.0  # seconds
STEP_DELAY = 0.2        # seconds between each enable/disable action

# Mapping from the dance labels to the actual device IDs used by the Nodegrid API
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

def get_ticket():
    """Log in to the Nodegrid and return the session ticket."""
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
    """Generic PUT helper for enable/disable endpoints."""
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
    """Enable a serial/USB‑serial port."""
    put(ticket, f"/api/v1/devices/table/{device}/enable")

def disable(ticket, device):
    """Disable a serial/USB‑serial port."""
    put(ticket, f"/api/v1/devices/table/{device}/disable")

def main():
    ticket = get_ticket()
    print("Ticket obtained")

    # Define the full sequence as (action, label)
    sequence = [
        ("enable", "P1"),   # P1
        ("enable", "P3"),   # P3
        ("disable", "P1"),  # !P1
        ("enable", "P5"),   # P5
        ("disable", "P3"),  # !P3
        ("enable", "P7"),   # P7
        ("disable", "P5"),  # !P5
        ("enable", "P8"),   # P8
        ("disable", "P7"),  # !P7
        ("enable", "P6"),   # P6
        ("disable", "P8"),  # !P8
        ("enable", "P4"),   # P4
        ("disable", "P6"),  # !P6
        ("enable", "P2"),   # P2
        ("disable", "P4"),  # !P4
        ("disable", "P2"),  # !P2
    ]

    for action, label in sequence:
        device = PORT_MAP[label]
        if action == "enable":
            enable(ticket, device)
            print(f"Enabled {label} ({device})")
        else:  # disable
            disable(ticket, device)
            print(f"Disabled {label} ({device})")
        time.sleep(STEP_DELAY)

    # Optional: clean up the session (omit to save one round‑trip;
    # the ticket will expire automatically after the Nodegrid's idle timeout).
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
    print("Final Ripple dance complete.")

if __name__ == "__main__":
    main()