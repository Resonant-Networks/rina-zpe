---
name: nodegrid-port-control
description: "Control Nodegrid serial ports (enable/disable)."
version: 1.0.0
author: Hermes Agent
category: devops
---
# Nodegrid Port Control Skill

This skill provides tools to enable/disable serial ports on a ZPE Nodegrid device and run predefined dance patterns (lightsweep, ripple, etc.) using REST API.

## Prerequisites

- Nodegrid reachable at https://10.15.235.116 (adjust BASE_URL in scripts if needed).
- Credentials: username=`admin`, password=`<NODEGRID_PASSWORD>` (stored in the scripts; update if changed).
- Python 3.x and `urllib` (standard library).

## Provided Scripts

All scripts are located in `~/./skills/nodegrid-port-control/scripts/` after installation.

- `enable_port.py <device_id>` – Enable a serial port.
- `disable_port.py <device_id>` – Disable a serial port.

## Usage

### Enable a port

```bash
python3 /opt/data/skills/nodegrid-port-control/scripts/enable_port.py ttyS1-router1
```

### Disable a port

```bash
python3 /opt/data/skills/nodegrid-port-control/scripts/disable_port.py ttyS2
```

## Under the Hood

Each script performs:
1. **Login** – POST to `/api/v1/Session` to obtain a session ticket.
2. **Operation** – PUT to `/api/v1/devices/table/<device_id>/enable` or `/disable` with the ticket header.
3. **Logout** – DELETE `/api/v1/Session` (best‑effort).

The dance scripts implement the sequences defined in the existing `.py` files.

## Notes

- **Read‑only operations** (listing ports, interfaces, wireless, cellular status) should be performed via the native MCP tools (`mcp__modem__list_managed_devices`, `mcp__modem__get_network_interfaces`, etc.).
- **Write operations** (enable/disable, dance) must use this skill to avoid MCP‑endpoint 404 errors.

## Installation

The skill is installed via `skill_manage`. After installation, the scripts are available under the skill’s directory.

---
