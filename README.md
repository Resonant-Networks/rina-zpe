# rina-zpe

Operational baseline, deployment configurations, Model Context Protocol (MCP) gateway, and automation routines for ZPE Nodegrid infrastructure across **RS1-ZPE** and **RM1-ZPE** appliances.

---

## Architecture Overview

```
                                      ┌────────────────────────┐
                                      │   Nodegrid Host OS     │
                                      │  (ZPE REST /api/v1)    │
                                      └───────────┬────────────┘
                                                  │ (localhost:443)
┌───────────────────────────┐         ┌───────────▼────────────┐
│   zpe-tailscale-gateway   │         │      nodegrid-mcp      │
│ (Subnet Router/Exit Node) │         │ (Streamable HTTP 8000) │
└───────────────────────────┘         └───────────▲────────────┘
                                                  │ (localhost:8000/mcp)
                                      ┌───────────┴────────────┐
                                      │      hermes-agent      │
                                      │  (Slack / CLI / Skills)│
                                      └────────────────────────┘
```

The system coordinates three containerized services running on host networking:
1. **`zpe-tailscale-gateway`**: Connects the appliance to the secure Tailnet and advertises local subnets.
2. **`nodegrid-mcp`**: Read-only Model Context Protocol server exposing Nodegrid telemetry (interfaces, serial ports, system status) over streamable HTTP.
3. **`hermes`**: Autonomous AI coding and operations agent integrated with Slack and local skills.

---

## Appliance Matrix

| Feature | RS1-ZPE (Legacy Node) | RM1-ZPE (Current Standard) |
|---|---|---|
| **Host IP** | `100.123.118.15` (Tailscale) | `192.168.0.72` / `100.119.254.114` |
| **Hermes User** | `root` (`/home/root/.hermes`) | `agent` (UID 1000, `/home/agent/.hermes`) |
| **MCP Implementation**| FastMCP (Python 3.11) | MCPServer Streamable HTTP (Python 3.12, v1.9.4) |
| **MCP Endpoint** | `http://127.0.0.1:8000/mcp/` | `http://127.0.0.1:8000/mcp` *(no trailing slash)* |
| **Status** | Operational reference node | Active primary node |

---

## Repository Structure

```
rina-zpe/
├── docker/
│   ├── tailscale/                 # zpe-tailscale-gateway run script & docs
│   ├── nodegrid-mcp/              # Dockerfile, requirements.txt, server.py (v1.9.4)
│   │   └── legacy-fastmcp/        # FastMCP implementation from RS1-ZPE
│   └── hermes/                    # Hermes agent deployment & config template
├── dances/                        # Serial LED sweep, ripple, and loop scripts
├── skills/                        # 12 Hermes skills for Nodegrid telemetry & operations
├── docs/                          # Architecture, troubleshooting, and API docs
├── docker-compose.yml             # Unified Compose specification
├── deploy.sh                      # One-click appliance bootstrapper
└── .env.example                   # Parameterized environment template
```

---

## Quickstart & Deployment

### 1. Prerequisites
- Docker Engine & Docker Compose installed on the Nodegrid appliance.
- Admin credentials for Nodegrid OS (`/api/v1/Session`).

### 2. Configure Environment
```bash
cp .env.example .env
nano .env   # Populate NODEGRID_PASSWORD, Slack tokens, and Tailscale settings
```

### 3. Deploy Containers
```bash
chmod +x deploy.sh
./deploy.sh
```

Or run via Docker Compose:
```bash
docker compose up -d
```

---

## Dance Routines
The `dances/` directory contains serial port light chasers and stress loops:
- **`light_sweep_dance.py`**: Sequentially activates and deactivates console port LEDs in serpentine order.
- **`dance_ripple_final.py`**: Outward ripple pattern from center ports to edges.
- **`ls_dance_loop.sh`**: Runs `light_sweep_dance.py` continuously in the background.

```bash
python3 dances/light_sweep_dance.py
```

---

## Troubleshooting Guide
Refer to [`docs/troubleshooting.md`](docs/troubleshooting.md) for detailed diagnostics, including:
- Fixing Starlette HTTP 307 redirects on MCP endpoints.
- Resolving FastMCP `406 Not Acceptable` errors when pairing with modern Hermes builds.
- Recovering from stale `.mcp-discovery.lock` locks.
- Clearing poisoned Slack conversational threads in `state.db`.

---

## License
MIT License. See [LICENSE](LICENSE) for details.
