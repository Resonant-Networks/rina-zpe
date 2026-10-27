# Hermes Agent on Nodegrid

Hermes Agent connects to Slack, Telegram, and CLI while utilizing the local `nodegrid-mcp` gateway for live device and interface telemetry.

## Key Directories
- Host Mount: `/home/agent/.hermes` -> `/opt/data` in container.
- Skills: `/opt/data/skills/`
- Configuration: `/opt/data/config.yaml`
- SQLite State: `/opt/data/state.db`

## Critical Operational Notes
- **MCP URL**: Always ensure `config.yaml` uses `http://127.0.0.1:8000/mcp` without trailing slash to prevent Starlette 307 redirects.
- **Discovery Locks**: If startup discovery hangs, ensure `/opt/data/.mcp-discovery.lock` is removed and file ownership is `agent:agent` (UID 1000).
