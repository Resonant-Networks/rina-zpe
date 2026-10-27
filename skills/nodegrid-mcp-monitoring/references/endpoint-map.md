# Nodegrid MCP tool → REST endpoint map

The `modem` MCP server ("Nodegrid Read-Only Gateway" v1.9.4, uvicorn/FastMCP over
streamable HTTP) is a thin read-only proxy over the ZPE Nodegrid REST API. Every
tool maps to one `GET` under `https://<ip>/api/v1`. Auth is a session ticket:
`POST /api/v1/Session` with `{"username","password"}` → `session` value sent as the
`ticket:` header on all subsequent requests. Self-signed cert: skip TLS verify.

| MCP tool | Nodegrid endpoint |
|----------|-------------------|
| `get_cellular_status` | `GET /tracking/devices/wirelessmodem` |
| `get_cellular_detail` | `GET /tracking/devices/wirelessmodem/{modem_id}` (id = `slot\|iface`, e.g. `Channel-A\|cdc-wdm0`) |
| `get_system_overview` | `GET /system/about` |
| `get_system_metrics` | `GET /tracking/system/cpu` + `/tracking/system/memory` + `/tracking/system/disk` (three parallel calls) |
| `list_managed_devices` | `GET /devices/table` |
| `get_managed_device` | `GET /devices/table/{device_name}` |
| `get_device_outlets_status` | `GET /devices/table/{device_name}/outlets/status` |
| `get_network_interfaces` | `GET /tracking/network/interfaces` |
| `get_wifi_status` | `GET /tracking/network/hotspot` |
| `list_users` | `GET /security/localaccounts` |
| `get_user_detail` | `GET /security/localaccounts/{username}` |
| `get_active_sessions` | `GET /tracking/opensessions` |
| `query_nodegrid_api` | `GET {path}` — path is RELATIVE to `/api/v1` (pass `/network/interfaces`, never `/api/v1/...`) |

## Wrong-guess traps (these 404 or 400 — cost time probing)

- Interfaces live under `/tracking/network/interfaces`, NOT `/network/interfaces`
  (that 404s as `/v1/network/interfaces does not exist`).
- System overview is `/system/about`, NOT `/system/overview`.
- Wi-Fi is `/tracking/network/hotspot`, NOT `/tracking/devices/wireless` (returns `[]`).
- User list is `/security/localaccounts`, NOT `/aaa/*`, `/local-user*`, or
  `/system/aaa/users` — those all 404 on this firmware.
- Outlets are `/devices/table/{pdu}/outlets/status` — serial ports have no outlets
  and return `Failed to get outlets status`.

## Discovering the full surface

`GET https://<ip>/api_doc.html` (with the `ticket:` header) returns an ~8 MB Redoc
page that embeds the complete OpenAPI spec — extract every path with
`re.findall(r'/api/v1/[a-zA-Z0-9_/{}\.\-|]+', html)`. ~345 paths total.

## Reachability

This Hermes runtime runs ON the Nodegrid (RS1-ZPE). The marketing LAN IPs
(`10.15.235.116`, `192.168.72.18`) hang from inside the container; the API answers
at `https://127.0.0.1`. When rebuilding/pointing the MCP server, default
`NODEGRID_BASE_URL` to `https://127.0.0.1`.

## Rebuilding the server

A faithful rebuild lives in `scripts/` of the skills dir and packages as:
`server.py` (mcp>=2.0 `MCPServer`, 13 async `@server.tool()` handlers proxying
`httpx`), `Dockerfile`, `docker-compose.yml` (host network), `requirements.txt`
(`mcp`, `httpx`, `uvicorn`), `.env.example`. Run the streamable-HTTP server with
`asyncio.run(server.run_streamable_http_async(...))` — the method is a coroutine;
calling it bare emits "never awaited" and the server exits immediately.
