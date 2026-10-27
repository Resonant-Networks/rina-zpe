# Legacy FastMCP Implementation (RS1-ZPE)

This directory contains the original FastMCP implementation (`nodegrid_readonly_mcp.py`) previously deployed on **RS1-ZPE**.

## Architecture Differences & Compatibility Warning

| Component | Legacy Version (RS1-ZPE) | Modern Version (RM1-ZPE, standard) |
|---|---|---|
| Framework | FastMCP | `mcp.server.mcpserver.MCPServer` |
| Python Base | Python 3.10 / 3.11 | Python 3.12 / 3.14 |
| MCP SDK | `mcp==1.9.4` | `mcp>=2.0.0` |
| Client Compatibility | Older Hermes builds | Modern Hermes Agent (MCP 2.x) |

> [!WARNING]
> Modern Hermes builds (Python 3.14 / MCP SDK 2.x) send streamable HTTP negotiation headers that FastMCP 1.9.4 rejects with:
> `406 Not Acceptable: Client must accept text/event-stream` or `400 Bad Request`.
> **Always use the parent `docker/nodegrid-mcp/` build (`server.py`) for new deployments.**
