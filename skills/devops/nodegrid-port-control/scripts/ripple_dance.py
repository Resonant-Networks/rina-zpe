#!/usr/bin/env python3
"""
Final Ripple dance:
  P1 > P3 > !P1 > P5 > !P3 > P7 > !P5 > P8 > !P7 > P6 > !P8 > P4 > !P6 > P2 > !P4 > !P2

Port mapping:
  P1 -> ttyS1-router1
  P2 -> ttyS2
  P3 -> ttyS3
  P4 -> ttyS4
  P5 -> ttyS5-42
  P6 -> ttyS6-EDcore
  P7 -> ttyS7
  P8 -> ttyS8
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
        resp = urllib.request.urlopen(req, context=context, timeout=30)
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

def main():
    base = "https://10.15.235.116"
    username = "admin"
    password = ""
    # Mapping from the dance labels to the actual device IDs used by the Nodegrid API
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

    ticket = get_ticket(base, username, password)
    print("Ticket obtained")

    for action, label in sequence:
        device = PORT_MAP[label]
        if action == "enable":
            enable(ticket, base, device)
            print(f"Enabled {label} ({device})")
        else:  # disable
            disable(ticket, base, device)
            print(f"Disabled {label} ({device})")
        time.sleep(0.2)

    # Optional: clean up the session (omit to save one round‑trip;
    # the ticket will expire automatically after the Nodegrid's idle timeout).
    try:
        make_request("DELETE", f"{base}/api/v1/Session", ticket=ticket)
    except Exception:
        pass
    print("Final Ripple dance complete.")

if __name__ == "__main__":
    main()
