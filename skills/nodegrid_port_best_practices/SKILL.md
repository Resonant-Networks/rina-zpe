---
name: nodegrid_port_best_practices
description: Best practices for Nodegrid port control via Hermes.
---

# Nodegrid Best Practices

## Authentication
Always obtain a fresh session ticket before performing any port operations:
```bash
TICKET=$(curl -k -s -X POST https://192.168.72.18/api/v1/Session -H \"Content-Type: application/json\" -d '{\"username\":\"admin\",\"password\":\"<NODEGRID_PASSWORD>\"}' | python3 -c \"import sys,json;print(json.load(sys.stdin)[\"session\"]\")
```
Include the ticket in the `ticket:` header for all subsequent API calls.

## Enabling / Disabling Ports
- Use the dedicated endpoints:
  - `PUT /api/v1/devices/table/{device}/enable`
  - `PUT /api/v1/devices/table/{device}/disable`
- Do **NOT** use `PUT` with `{\"mode\": \"enabled\"}` as it returns empty/400.
- Each enable/disable call takes ~5‑6 s round‑trip.
- Avoid the intermediate `GET /api/v1/devices/table/{device}` unless you need to verify the state; the PUT response already contains the updated device info.

## User Preferences
- **Terse responses**: Reply with the minimal necessary information — one line when possible. Avoid explanations unless asked.
- **Only act on explicit requests**: If the user asks to list or check status, **do not** enable or disable ports. Leave them as‑is.
- **Prioritize MCP first**: When querying Nodegrid status, always use MCP modem tools (e.g., mcp__modem__list_managed_devices, mcp__modem__get_network_interfaces) before falling back to direct API or other methods.

## Status Reporting
- Use MCP modem tools for consistent status:
  - Serial ports: `mcp__modem__list_managed_devices`
  - Network interfaces: `mcp__modem__get_network_interfaces`
  - Cellular detail: `mcp__modem__get_cellular_status` (requires modem_id)
  - Wi‑Fi status: `mcp__modem__get_wifi_status`
- Format output tersely: one line per interface/port with state and key stats (e.g., `eth0: down, rx 4949 tx 4730`).
- Do not change port state unless explicitly asked; reporting is read‑only.

## Dance Scripts
Prefer the optimized scripts that skip per‑port status GETs:
- `/opt/data/nodegrid_fast_dance.py` – implements running, pingpong, wave, snake, random patterns with minimal delay.
- `/opt/data/dance_ripple_final.py` – example custom sequence (P1 > P3 > !P1 > P5 > !P3 > P7 > !P5 > P8 > !P7 > P6 > !P8 > P4 > !P6 > P2 > !P4 > !P2).

Run them via:
```bash
source /opt/hermes/.venv/bin/activate
python3 /opt/data/<script>.py [options]
```

## Pitfalls
- **Unnecessary GETs**: Adding a status check after each enable/disable adds ~1.3‑1.5 s per port, significantly slowing dances.
- **Enabling without request**: Changing port state when the user only asked for a list violates their expectation of terse, action‑only responses.
- **Delay too low**: Setting `delay` below ~0.2 s does not improve speed because the API bottleneck dominates; it just increases load on the box.
- **Session cleanup**: The `DELETE /api/v1/Session` call is optional; omitting it saves one round‑trip (~100‑300 ms). The ticket expires automatically.
- **Missing networking tools**: If `ip` or `ifconfig` not available, use `/proc/net/wireless` for wireless quality, `/proc/net/route` for routing, and `hostname -I` for local IPs.
- **Assuming direct API is only way**: Use MCP modem tools (`mcp__modem__list_managed_devices`, `mcp__modem__get_network_interfaces`, etc.) for consistent status checks via Hermes.
- **Externaddressed Nodegrid API times out from this host, but the box is local**: this Hermes runtime runs ON the Nodegrid (`hostname` = `RS1-ZPE`). Curl/scripts against the marketing LAN IPs (`10.15.235.116`, `192.168.72.18`) hang even after private-network approval, but `https://127.0.0.1` answers `200`. For direct API writes mode `curl`/dance scripts at `https://127.0.0.1` (sed the BASE_URL); for read-only status prefer the MCP modem server (`mcp__modem__*` via `tool_call`, e.g. `query_nodegrid_api`, `get_cellular_status`, `get_wifi_status`). When a connection fails, check whether the IP is right before assuming the API is down.
- **Verbose output in chats**: Suppress reasoning output with `hermes config set display.show_reasoning false` to keep responses terse in group chats.
- **Locating dance scripts**: Use `search_files('*dance*.py', target='files')` to find available dance scripts instead of guessing paths.
- **Discovering MCP tools**: Use `tool_search` with relevant queries (e.g., "modem", "system overview") to list available Nodegrid MCP tools before calling.
- **Do not restart Hermes gateway from inside the agent**: Attempting to restart the gateway via a tool call executed by the agent will fail because the gateway terminates the script. Always restart from an external shell or host.
- **For general Nodegrid monitoring**: Use the `nodegrid-mcp-monitoring` skill for CPU, memory, network status via MCP tools.
- **Nodegrid exposes no user-management in its REST API**: The `/api/v1` surface has no user/admin/account endpoints (probing `Users`, `users`, `System/Users`, `auth/users`, `accounts` all return `404 ResourceNotFound`) and no swagger/openapi spec. Admin-user lifecycle (e.g. creating an admin) is handled in the platform web UI, not the shell (`/etc/passwd` here is the container's own store, root-owned, and container-internal — not the platform auth DB) and not the public API. When asked to *validate* a capability, authenticate a session read-only and probe the endpoint surface; do not implement a workaround or half-create. If validation shows the operation is not reachable, say so plainly instead of hunting indefinitely.
- **When authenticating the Nodegrid API, the header is `ticket:`**: login via `POST /api/v1/Session` and send the returned `session` value as the `ticket:` header. Other conventions — `X-Nodegrid-Session`, `Authorization`, or a session cookie — all return `400/401 Invalid Session`; only `ticket:` succeeds.
- **Admin shell / swap housekeeping**: When swap is exhausted or you need OS-level commands, see `references/admin-shell-and-swap.md` (SSH `shell` escape + `swapoff -a && swapon -a`).
## Verification
After any enable/disable, verify the state with:
```bash
curl -k -s -X GET "https://192.168.72.18/api/v1/devices/table/{device}" -H "ticket: $TICKET" | python3 -m json.tool | grep -A2 -B2 mode
```

---
