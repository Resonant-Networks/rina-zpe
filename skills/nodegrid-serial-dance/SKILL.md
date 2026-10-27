---
name: nodegrid-serial-dance
description: ZPE Nodegrid serial port control via REST API.
---

# ZPE Nodegrid Serial Port Dance

## Target
ZPE Nodegrid device at `https://192.168.72.18` with credentials `admin:<NODEGRID_PASSWORD>`

## Authentication
```
POST /api/v1/Session
{"username": "admin", "password": "<NODEGRID_PASSWORD>"}
→ {"session": "<ticket>"}
```
Use `ticket: <session>` header on all subsequent requests.

## Device ID Mapping (physical port → device ID)
Not all physical ports map 1:1 to device IDs:
- ttyS1 → ttyS1-router1
- ttyS2 → ttyS2
- ttyS3 → ttyS3
- ttyS4 → TestMTC
- ttyS5 → xmm4-2-1
- ttyS6 → EDcore
- ttyS7 → ttyS7
- ttyS8 → ttyS8

## Physical Layout
Two rows of four, left → right (confirmed on the box):
```
TOP     ttyS1  ttyS3  ttyS5  ttyS7
BOTTOM  ttyS2  ttyS4  ttyS6  ttyS8
```
An odd port number sits directly above the next even one. Walk patterns in
ROW order, never numeric port order — numeric order (1,2,3,4…) bounces
top/bottom and reads as a column effect instead of a sweep across the box.
Definition order is `SNAKE_PATH`:
`ttyS1 ttyS3 ttyS5 ttyS7 → ttyS8 ttyS6 ttyS4 ttyS2`.

## Enable / Disable Endpoints
```
PUT /api/v1/devices/table/{device}/enable
PUT /api/v1/devices/table/{device}/disable
```
Both return the full device table. Use the dedicated endpoints (NOT PUT with {"mode": "enabled"} which returns empty/400).

## Status Check
```
GET /api/v1/devices/table/{device}
```
Returns full config with `mode` field ("enabled" or "disabled").

## Dance Patterns
The `nodegrid_dance.py` script at `/opt/data/nodegrid_dance.py` implements
(all paths follow the physical serpentine, out then back):
- **running**: single chaser along the serpentine path
- **pingpong**: same route, explicit bounce labels
- **wave**: all on then all off (topology-independent)
- **snake**: neighbour pairs along the serpentine path
- **random**: shuffled chaser

Usage: `source /opt/hermes/.venv/bin/activate && python3 /opt/data/nodegrid_dance.py`

## Performance (measured)
The API is the bottleneck, not the script's `delay`:
- `PUT .../{device}/enable` → ~5.5-6.5s round trip
- `PUT .../{device}/disable` → ~5-6.5s round trip
- `GET .../table/{device}` → ~1.3-1.5s

One chaser step (enable + status + disable) costs ~13s, ~6s of which is the
box actually switching the port. Setting `delay=0` does NOT speed the dance
up — it just removes the intended pause and churns the box (observed ~18s per
port). Keep `delay` at 0.3-0.5; below that it changes nothing visible.
To actually save time, drop the per-port `get_status()` call (it is a third of
the round trips).

## Start state
The script calls `disable_all()` before any pattern runs, so every dance
begins from a dark board. Keep that step — without it a pattern starts from
whatever the previous run left behind.

## Key Notes
- Use `verify=False` (self-signed cert)
- Some ports take longer to disable (active connections) — use 10s+ timeouts
- Session cleanup via DELETE /api/v1/Session reverts ports to original state
- Script handles SIGINT/SIGTERM gracefully
