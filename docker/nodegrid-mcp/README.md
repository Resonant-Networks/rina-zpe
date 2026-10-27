# Nodegrid Read-Only Gateway (MCP Server)

A streamable HTTP Model Context Protocol (MCP) server that interfaces with the ZPE Nodegrid REST API (`/api/v1`).

## Exposed Tools
- `get_network_interfaces`: Inspect all network interfaces (backplane0, eth0, tailscale0, wlan0, wwan0) with packet counters and status.
- `list_managed_devices`: Query serial console ports, baud rates, and connected devices.
- `get_device_status`: Check individual port status and connection state.
- `get_system_info`: Inspect CPU, memory, uptime, and Nodegrid firmware build details.
- `get_cellular_status`: Retrieve LTE/5G modem details, SIM state, RSSI, and carrier metadata.

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `NODEGRID_BASE_URL` | Base URL of Nodegrid host | `https://127.0.0.1` |
| `NODEGRID_USERNAME` | Nodegrid administrative user | `admin` |
| `NODEGRID_PASSWORD` | Nodegrid administrative password | *(Required)* |
| `NODEGRID_VERIFY_TLS` | SSL certificate verification (0 or 1) | `0` |
| `MCP_HOST` | Bind address for MCP HTTP server | `0.0.0.0` |
| `MCP_PORT` | Port for MCP streamable HTTP | `8000` |
| `MCP_STREAMABLE_HTTP_PATH` | Path endpoint | `/mcp` |

## Build and Run

```bash
# Build image
docker build -t nodegrid-readonly-gateway:1.9.4 .

# Run container
./docker-run.sh
```

## Changing Target Nodegrid Host
To point this MCP server to a new or remote Nodegrid host, follow the step-by-step guide in [**`docs/updating-nodegrid-host.md`**](../../docs/updating-nodegrid-host.md).
