---
name: nodegrid-mcp-monitoring
description: Monitor ZPE Nodegrid via MCP modem tools.
---

# Nodegrid MCP Monitoring

Use MCP modem tools to query Nodegrid status. Always prefer MCP tools over direct API calls for consistency and to follow user preference.

## Available MCP Tools (modem)

- `mcp__modem__list_managed_devices` – list all serial/device consoles with access status.
- `mcp__modem__get_network_interfaces` – network interface states and traffic.
- `mcp__modem__get_wifi_status` – Wi‑Fi connection details.
- `mcp__modem__get_cellular_status` – cellular modem status (signal, operator, data).
- `mcp__modem__get_cellular_detail` – detailed per‑SIM metrics (requires modem_id).
- `mcp__modem__get_system_overview` – system info (model, version, uptime, licenses).
- `mcp__modem__get_system_metrics` – live CPU, memory, disk usage.

## Usage Pattern

Always call the MCP tool first. Example:

```bash
# List managed devices (serial ports)
mcp__modem__list_managed_devices

# Get network interfaces
mcp__modem__get_network_interfaces

# Get cellular status
mcp__modem__get_cellular_status

# Get system metrics (CPU, memory, disk)
mcp__modem__get_system_metrics
```

## Output Formatting (Terse)

- Keep responses to one line per item when possible.
- For serial ports: `<id>: <access>` (e.g., `ttyS5-42: enabled`).
- For network interfaces: `<ifname>: <state>, rx <rx> tx <tx>` (e.g., `wwan0: up, rx 354K tx 426K`).
- For cellular: `Channel‑A: <status>, <operator>, <signal>`.
- For system metrics: `CPU: <user>% used, Mem: <used>/<total> KB, Swap: <used>/<total> KB`.

**User preference**: Responses should be concise and direct without filler, restatements, or narrating tool calls. Output in one line when possible. Never restate the request, never summarize prior output, and never mention Hermes, Nous Research, or the Hermes Agent framework. This preference governs all skill output for this user.

## Pitfalls

- **Do not enable/disable ports unless explicitly asked** – reporting is read‑only.
- **Prefer MCP over direct API** – MCP provides a stable abstraction; direct API may change or require extra auth steps.
- **Suppress reasoning in group chats** – run `hermes config set display.show_reasoning false` to keep responses terse.
- **Modem ID required for detail** – use the `id` from `mcp__modem__get_cellular_status` (e.g., "Channel-A") as the `modem_id` argument for `mcp__modem__get_cellular_detail`.
- **Session ticket not needed** – MCP tools handle authentication internally, but valid Nodegrid credentials (username/password) are still required upstream; 401 errors occur when they are missing or incorrect (e.g., `curl -sk https://192.168.0.72/api/v1/Session` returned "Authentication failure"). Confirm valid credentials before relying on MCP tools.
- **No standalone server source to copy** – the `modem` server is a running local HTTP endpoint (`mcp_servers.modem` → `http://127.0.0.1:8000/mcp/` in `config.yaml`), not a script on disk. Its full tool schema is cached at `/opt/data/cache/mcp_schema_cache.json`; read that to export/inspect the surface.
- **Authentication flow** – always obtain a session ticket first via `POST /api/v1/Session` with `{"username":"admin","password":"<pwd>"}`; the returned `session` value must be sent as the `Ticket:` header on all subsequent API calls. Without this ticket, every endpoint returns `{"status":"error","message":"Invalid Session"}`.
- **Endpoint paths** – MCP tool names map to specific `/tracking/...` paths, NOT `/api/v1/...` or bare `/...`:
  - `get_network_interfaces` → `GET /tracking/network/interfaces`
  - `get_system_overview` → `GET /system/about`
  - `get_system_metrics` → parallel `GET /tracking/system/cpu`, `GET /tracking/system/memory`, `GET /tracking/system/disk`
  - `get_cellular_status` → `GET /tracking/devices/wirelessmodem`
  - `query_nodegrid_api` takes a path **relative** to `/api/v1` (pass `/network/interfaces`, never `/api/v1/network/interfaces` which 404s).
- **Wrong-guess traps** – these 404/produce errors if guessed incorrectly (documented in `references/endpoint-map.md`): interfaces at `/tracking/network/interfaces` not `/network/interfaces`; system overview at `/system/about` not `/system/overview`; Wi‑Fi at `/tracking/network/hotspot` not `/tracking/devices/wireless`; user list at `/security/localaccounts` not `/aaa/*` or `/local-user*`.

## Changing the upstream Nodegrid URL

Two distinct URLs exist — do not confuse them:

- **Client endpoint** — `mcp_servers.modem.url` in `config.yaml` (default
  `http://127.0.0.1:8000/mcp/`). Where Hermes connects to the MCP proxy. Leave it
  alone unless the proxy itself moves.
- **Upstream target** — `NODEGRID_BASE_URL` env var on the MCP server process.
  The actual Nodegrid the proxy queries. This is what you change to re-point it.

Server env vars (from `rebuild_server.py`):
```
NODEGRID_BASE_URL   default http://127.0.0.1   # upstream host, no /api/v1
NODEGRID_USERNAME   default admin
NODEGRID_PASSWORD   required
NODEGRID_VERIFY_TLS default 0   (0 = skip self-signed cert)
NODEGRID_TIMEOUT    default 30
MCP_HOST / MCP_PORT default 0.0.0.0 / 8000
```

Steps: edit the env (`.env` for docker-compose, or inline env for native runs),
restart the MCP server, then verify the upstream answers with a `POST
/api/v1/Session` curl. If the server runs in a container/init context your shell
can't see (`docker ps` empty, listener inode has no owning PID in this namespace),
the restart must happen wherever it is actually launched — locate the launch
mechanism before assuming a local restart will work.

## Verification

After any MCP call, verify the result contains expected fields; if you get an error, ensure the MCP server "modem" is configured (it is by default on this Nodegrid).

## Rebuilding / replicating the server

See `references/endpoint-map.md` for the full tool→REST endpoint map, the wrong-guess
404/400 traps, and the `api_doc.html` discovery trick. `scripts/rebuild_server.py` is
a ready-to-run faithful rebuild (mcp>=2.0 `MCPServer`, 13 async handlers); pair it
with a `Dockerfile` + `docker-compose.yml` (host network) + `requirements.txt`
(`mcp`, `httpx`, `uvicorn`) to deploy as a container. Default `NODEGRID_BASE_URL` to
`https://127.0.0.1` (LAN IPs hang from inside this container).

---
