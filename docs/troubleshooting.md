# Troubleshooting Runbook: rina-zpe

This guide details battle-tested diagnostic procedures for common operational failures encountered on RS1-ZPE and RM1-ZPE appliances.

---

## 1. MCP Authentication Rejection (`401 Unauthorized` or `Invalid Session`)

### Symptom
Hermes fails to query network or port telemetry, reporting:
```
MCP modem-server calls are returning errors — server rejecting requests (Invalid Session)
```

### Root Cause
1. `nodegrid-mcp` container started with invalid or masked credentials (`NODEGRID_PASSWORD='***'`).
2. Target REST API endpoint does not accept Basic Auth and requires a Nodegrid session ticket.

### Remediation
1. Verify credentials by manually querying the Nodegrid Session endpoint:
   ```bash
   curl -k -s -X POST https://127.0.0.1/api/v1/Session \
     -H "Content-Type: application/json" \
     -d '{"username":"admin","password":"<YOUR_PASSWORD>"}'
   ```
2. Re-deploy `nodegrid-mcp` with proper password:
   ```bash
   NODEGRID_PASSWORD="<YOUR_PASSWORD>" ./docker/nodegrid-mcp/docker-run.sh
   ```

---

## 2. FastMCP Protocol Incompatibility (`406 Not Acceptable`)

### Symptom
Hermes logs show:
```
httpx.HTTPStatusError: Client error '406 Not Acceptable' for url 'http://127.0.0.1:8000/mcp'
```

### Root Cause
Older `FastMCP` servers (used in RS1-ZPE) expect legacy SSE negotiation. Modern Hermes builds (Python 3.14 / MCP SDK 2.x) send streamable HTTP negotiation headers that FastMCP rejects.

### Remediation
Switch the container to the modern `nodegrid-readonly-gateway:1.9.4` build located in `docker/nodegrid-mcp/`:
```bash
docker build -t nodegrid-readonly-gateway:1.9.4 docker/nodegrid-mcp/
```

---

## 3. Starlette HTTP 307 Redirects

### Symptom
MCP client fails to connect or tool calls fail silently.

### Root Cause
Starlette/FastAPI enforces strict route matching without redirects on POST requests. If the server mounts `/mcp`, sending a request to `/mcp/` returns `307 Temporary Redirect`. Most MCP HTTP client libraries reject 307 redirects on JSON-RPC POST payloads.

### Remediation
Ensure Hermes `config.yaml` points to exact endpoint without trailing slash:
```yaml
mcp_servers:
  modem:
    url: http://127.0.0.1:8000/mcp
```

---

## 4. Stale Tool Discovery Locks

### Symptom
Hermes startup hangs indefinitely during tool registration pass (`discover_mcp_tools`).

### Root Cause
An unclean container shutdown leaves `.mcp-discovery.lock` in the Hermes root directory.

### Remediation
```bash
docker exec -it hermes rm -f /opt/data/.mcp-discovery.lock /opt/data/*.lock
docker restart hermes
```

---

## 5. Slack Conversation Poisoning ("Error Persists")

### Symptom
After fixing MCP, Hermes in Slack continues to reply with the old failure message without attempting a tool call.

### Root Cause
Hermes records prior conversational refusals in SQLite (`state.db`). When prompted in an existing thread, the model prioritizes cached thread context over querying tools.

### Remediation
Clear the active thread session in SQLite:
```bash
sqlite3 /home/agent/.hermes/state.db \
  "DELETE FROM messages WHERE session_id = '<SESSION_ID>'; \
   DELETE FROM sessions WHERE id = '<SESSION_ID>';"
docker restart hermes
```
Alternatively, ask the user to type `/reset` or start a new Slack thread.
