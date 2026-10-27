---
name: nodegrid-fast-wave
description: Fast wave dance for ZPE Nodegrid via concurrent requests.
---

# Nodegrid Fast Wave Dance

This skill describes the fastest way to perform a wave pattern (all ports on, then all off) on a ZPE Nodegrid serial console device, minimizing API round‑trips by:
- Skipping per‑port status GET calls.
- Using parallel enable/disable requests (thread pool).
- Reusing a single authentication ticket.

## User Preferences
- Terse output: Only essential information, no extra explanations
- Manual verification: User prefers to verify port states themselves
- Minimal API calls: Avoid unnecessary GETs and DELETEs
- Action-focused: Give the command, don't over-explain

## Optimized Concurrent Patterns
For any port operation (enable/disable), use these patterns to minimize delay:

1. **Parallel Execution**
   - Use `ThreadPoolExecutor` with `max_workers=len(ports)`
   - Submit all operations concurrently
   - Wait for all futures to complete

2. **HTTP Client Optimization**
   - Increase urllib3 pool size: `maxsize=10`
   - Reuse single `PoolManager` instance
   - Disable SSL warnings for self-signed certs

3. **Timeout Adjustment**
   - Set timeout to 30+ seconds (disable operations can be slower)
   - This accommodates ports with active connections

4. **Eliminate Unnecessary Calls**
   - Skip verification GETs after enable/disable (PUT returns 200/204 on success)
   - Omit session cleanup DELETE (ticket expires automatically)
   - Trust the PUT response status instead of making extra GET calls

## Preferred Script Template

```python
#!/usr/bin/env python3
"""
Generic concurrent port operations for ZPE Nodegrid.
Follows user preferences for terseness and minimal API calls.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import urllib3
from urllib3.exceptions import InsecureRequestWarning

urllib3.disable_warnings(InsecureRequestWarning)
http = urllib3.PoolManager(cert_reqs='CERT_NONE', maxsize=10)

BASE_URL = "https://192.168.72.18"
USERNAME = "admin"
PASSWORD = "<NODEGRID_PASSWORD>"
REQUEST_TIMEOUT = 30.0

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

def operate_device(ticket, device, operation):
    """Enable or disable a single device."""
    url = f"{BASE_URL}/api/v1/devices/table/{device}/{operation}"
    headers = {"ticket": ticket, "Content-Type": "application/json"}
    resp = http.request(
        "PUT",
        url,
        headers=headers,
        retries=False,
        timeout=REQUEST_TIMEOUT,
    )
    if resp.status not in (200, 204):
        return device, False, f"Failed with status {resp.status}"
    return device, True, f"{operation.capitalize()}d"

def main(ports, operation):
    """Perform enable/disable on multiple ports concurrently."""
    ticket = get_ticket()
    print("Ticket obtained")
    
    with ThreadPoolExecutor(max_workers=len(ports)) as executor:
        futures = {
            executor.submit(operate_device, ticket, PORT_MAP[p], operation): p
            for p in ports
        }
        for future in as_completed(futures):
            port, success, msg = future.result()
            print(f"  {port}: {msg}")
    
    # No verification or session cleanup - saves round-trips
    print(f"{operation.capitalize()} operation complete.")

if __name__ == "__main__":
    # Example usage:
    # python3 script.py enable P1 P3 P5
    # python3 script.py disable P2 P4 P6 P8
    import sys
    if len(sys.argv) < 3:
        print("Usage: python3 script.py <enable|disable> <port1> [port2...]")
        sys.exit(1)
    
    operation = sys.argv[1].lower()
    ports = sys.argv[2:]
    main(ports, operation)
```

## Pitfalls
- **Do not call GET …/table/{device}** for status – it adds ~1.3‑1.5 s per port and defeats the speed gain.
- **Timeouts**: If you set too many workers, the Nodegrid may start returning read timeouts. Start with 4 workers and increase only if you observe success.
- **Ticket reuse**: Fetch the ticket once and reuse it for all requests; re‑authenticating each cycle adds unnecessary latency.
- **Self‑signed certificate**: Disable SSL verification (`verify=False` or `CERT_NONE`) or install the CA cert.
- **User preference for terse output**: Respect the user's preference for minimal, action-only responses

## Related
- See `nodegrid-serial-dance` for the basic device mapping, physical layout, and original dance patterns.
- See `nodegrid-serial-control` for basic port control operations.

## MCP / Modem Tools (local `modem` server at 127.0.0.1:8000)
- Tools: `get_cellular_status`, `get_cellular_detail`, `list_managed_devices`, `get_managed_device`, `get_device_outlets_status`, `get_system_overview`, `get_system_metrics`, `query_nodegrid_api`, `list_prompts`, `get_prompt`, `list_resources`, `read_resource`, `get_wifi_status`, `get_active_sessions`.
- Access: local-only; Telegram bot invokes on message — not a public endpoint.
- Verify: `/opt/hermes/bin/hermes mcp list`; list tools via `tool_search(query="modem")`.

## User Preferences (always-on for this hardware session)
- Terse (emoji + linespace), action-first, no narration.
- Verify on device/API; do not invent states.
- Skip unnecessary GET verification after PUT success.

- Nodegrid at `https://192.168.72.18` with credentials `admin:<NODEGRID_PASSWORD>`
- Access to the scripts in `/opt/data/` (see below).

## Procedure
1. **Obtain a session ticket**
   ```bash
   curl -k -s -X POST https://192.168.72.18/api/v1/Session \
        -H "Content-Type: application/json" \
        -d '{"username":"admin","password":"<NODEGRID_PASSWORD>"}' | \
        python3 -c "import sys,json;print(json.load(sys.stdin)['session'])"
   ```
   Store the ticket in `$TICKET`.

2. **Enable all ports in parallel**
   Using a thread pool (e.g., Python’s `ThreadPoolExecutor`), submit a `PUT …/enable` request for each port in the serpentine order:
   ```
   ttyS1‑router1, ttyS3, xmm4‑2‑1, ttyS7, ttyS8, EDcore, TestMTC, ttyS2
   ```
   Wait for all futures to complete.

3. **Lights‑on delay**
   `sleep <delay>` (default 0.2 s). This is the time the ports stay enabled.

4. **Disable all ports in parallel**
   Submit a `PUT …/disable` request for each port, again in parallel, and wait for completion.

5. **Repeat** for the desired number of cycles.

6. **Cleanup**
   - Disable all ports (best effort).
   - Delete the session with `DELETE /api/v1/Session`.

## Scripts (ready‑to‑run)
- `/opt/data/nodegrid_wave_fast.py`
  Sequential enable/disable with a tiny gap between individual port requests; good balance of speed and reliability.
  Usage: `source /opt/hermes/.venv/bin/activate && python3 /opt/data/nodegrid_wave_fast.py -c <cycles> -d <delay> -g <gap>`

- `/opt/data/nodegrid_wave_parallel.py`
  Fully parallel enable/disable using a worker pool.
  Usage: `source /opt/hermes/.venv/bin/activate && python3 /opt/data/nodegrid_wave_parallel.py -c <cycles> -d <delay> -w <workers>`

## Pitfalls
- **Do not call GET …/table/{device}** for status – it adds ~1.3‑1.5 s per port and defeats the speed gain.
- **Timeouts**: If you set too many workers, the Nodegrid may start returning read timeouts. Start with 4 workers and increase only if you observe success.
- **Ticket reuse**: Fetch the ticket once and reuse it for all requests; re‑authenticating each cycle adds unnecessary latency.
- **Self‑signed certificate**: Disable SSL verification (`verify=False` or `CERT_NONE`) or install the CA cert.

## Related
- See `nodegrid-serial-dance` for the basic device mapping, physical layout, and original dance patterns.
