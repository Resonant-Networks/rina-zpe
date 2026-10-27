---
name: nodegrid-memory-info
description: Get ZPE Nodegrid memory usage via REST API.
---

# ZPE Nodegrid Memory Usage Info

## Target
ZPE Nodegrid device at `https://192.168.72.18` with credentials `admin:<NODEGRID_PASSWORD>`

## Authentication
```
POST /api/v1/Session
{"username": "admin", "password": "<NODEGRID_PASSWORD>"}
→ {"session": "<ticket>"}
```
Use `ticket: <session>` header on all subsequent requests.

## Endpoint
```
GET /api/v1/tracking/system/memory
```
Returns JSON with memory usage statistics.

## Example Script
```python
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

NODEGRID_IP = "192.168.72.18"
BASE_URL = f"https://{NODEGRID_IP}/api/v1"
USERNAME = "admin"
PASSWORD = "<NODEGRID_PASSWORD>"

def auth():
    resp = requests.post(
        f"{BASE_URL}/Session",
        json={"username": USERNAME, "password": PASSWORD},
        verify=False, timeout=10
    )
    resp.raise_for_status()
    return resp.json()["session"]

def get_memory_usage(ticket):
    resp = requests.get(
        f"{BASE_URL}/tracking/system/memory",
        headers={"ticket": ticket, "accept": "application/json"},
        verify=False, timeout=10
    )
    resp.raise_for_status()
    return resp.json()

if __name__ == "__main__":
    ticket = auth()
    print(get_memory_usage(ticket))
```

## Notes
- Use `verify=False` (self-signed cert)
- Session cleanup via DELETE /api/v1/Session
- The endpoint returns memory usage details (total, used, free, etc.)
