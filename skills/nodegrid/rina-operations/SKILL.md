---
name: rina-operations
description: "RINA runbook: session commands, port control, dances, MCP."
version: 1.0.0
author: Wai Choon Au (hfx), Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [rina, nodegrid, zpe, serial-port, dance, mcp, runbook]
---

# RINA Operations Skill

Operational runbook for RINA (R ~Nets Intelligent Network Assistant) on the
RS1-ZPE ZPE Nodegrid. Covers session commands, serial-port control, light
dances, and the read-only MCP surface.

## When to Use

- User asks for `/status`, `/model`, `/restart`, or any RINA session command
- Enable/disable serial ports, run light-sweep or ripple dances
- Read-only Nodegrid status: system, CPU/memory, network, cellular, Wi-Fi
- Lookup of physical port mapping or dance script paths

Don't use for: write ops to Nodegrid other than port toggles/dances (those go
through the dedicated nodegrid-* skills).

## Session Commands

- `/status` — context usage, model, provider, token budget, platform, uptime
- `/model` — switch model; prefer `deepseek-v4-flash` (choose
  `deepseek-v4-flash-0731` via OpenRouter)
- `/restart` — graceful gateway restart. **Contact admin (@hfx) first** — the
  bot drops briefly and active tasks may die.

## Serial Port Control

Natural language, no API needed: "disable port 1, 2 and 3", "enable port 5 and
7", "disable all serial ports", "status of all ports?".

Physical mapping (2 rows × 4):

```
TOP     P1   P3   P5   P7
BOTTOM  P2   P4   P6   P8
```

✅ = enabled · dark = disabled.

Write ops go through the `nodegrid-port-control` / `nodegrid-serial-control`
skills; base URL `https://10.15.235.116`. MCP does NOT expose write ops
(enable/disable/ripple return 404) — use the skill scripts.

## Dance Patterns

- "do the light-sweep" → `light_sweep_dance.py`
- "do the ripple dance" → `ripple_dance.py`

```bash
python3 /opt/data/skills/devops/nodegrid-port-control/scripts/light_sweep_dance.py [-c cycles] [-d delay]
python3 /opt/data/skills/devops/nodegrid-port-control/scripts/ripple_dance.py
```

Default ~0.2 s per port switch. Patterns `light-sweep` and `ripple` only;
`running / pingpong / wave / snake / random` are gone (the
`nodegrid_fast_dance.py` script carrying them was removed).

Ripple final sequence (mapping in parentheses):
P1>P3>!P1>P5>!P3>P7>!P5>P8>!P7>P6>!P8>P4>!P6>P2>!P4>!P2,
where P1=ttyS1-router1, P2=ttyS2, P3=ttyS3, P4=TestMTC, P5=xmm4-2-1,
P6=EDcore, P7=ttyS7, P8=ttyS8.

## MCP Read-Only Tools

- `get_system_overview` — firmware, model, uptime, licenses
- `get_system_metrics` — CPU, memory, disk
- `get_network_interfaces` — NIC traffic + up/down
- `get_wifi_status` — Wi-Fi connections
- `get_cellular_status` / `get_cellular_detail` — modem state / per-SIM
- `list_managed_devices` / `get_managed_device` — serial/console devices
- `get_device_outlets_status` — power outlets
- `list_users` / `get_user_detail` — accounts
- `get_active_sessions` — current logins
- `query_nodegrid_api` — read-only GET on the API

Natural-language triggers: "show system overview", "CPU / memory usage?",
"network interfaces", "list managed devices / serial ports", "cellular /
Wi-Fi status". Read-only — never toggles ports.

## Pitfalls

- MCP `modem` server may target a stale address (172.16.7.184, SGNOG Wi-Fi)
  and time out — read local `/proc` or the `https://127.0.0.1` API instead.
- REST API uses a self-signed cert; skip verification.
- Always confirm the current base URL/IP before any state-changing call.

## Verification

After a dance or port toggle, list port status and confirm every target port
matches the intended state before reporting done.
