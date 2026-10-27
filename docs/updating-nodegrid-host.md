# Updating the Nodegrid Host URL & MCP Configuration

This guide provides the complete step-by-step procedure to update the `nodegrid-mcp` server when connecting to a new Nodegrid appliance, changing IP addresses, or migrating from localhost to a remote host.

---

## Architecture Context

```
┌──────────────┐                  ┌──────────────────┐                  ┌─────────────────────┐
│ hermes-agent │ ──(127.0.0.1)──> │   nodegrid-mcp   │ ──(REST API)───> │  Target Nodegrid    │
│  (port 8000) │                  │ (Streamable HTTP)│                  │ (NODEGRID_BASE_URL) │
└──────────────┘                  └──────────────────┘                  └─────────────────────┘
```
- **Hermes** always connects locally to the MCP container at `http://127.0.0.1:8000/mcp`.
- **`nodegrid-mcp`** acts as the gateway proxy, taking requests from Hermes and making authenticated calls to `NODEGRID_BASE_URL`.

---

## Step-by-Step Procedure

### Step 1: Pre-Check Target Reachability & Auth
Before altering container settings, verify from the appliance terminal that the new Nodegrid instance is reachable and accepts credentials:

```bash
# Test session creation
curl -k -s -X POST "https://<NEW_NODEGRID_IP_OR_URL>/api/v1/Session" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"<PASSWORD>"}'
```

**Expected Response**:
```json
{"status":"success","session":"...","user":"admin"}
```
> [!WARNING]
> If you receive `401 Unauthorized`, an HTML 404/302, or a timeout, stop here. Check IP routing, Tailscale subnet exposure, and admin credentials before updating the container.

---

### Step 2: Update the `nodegrid-mcp` Container

#### Option A: Direct Docker Run
Stop the existing container and run it with the new `NODEGRID_BASE_URL`:

```bash
# 1. Remove existing container
docker rm -f nodegrid-mcp

# 2. Launch container with updated target URL
docker run -d \
  --name nodegrid-mcp \
  --network host \
  --restart unless-stopped \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_HOST=0.0.0.0 \
  -e MCP_PORT=8000 \
  -e MCP_STREAMABLE_HTTP_PATH=/mcp \
  -e NODEGRID_BASE_URL="https://<NEW_NODEGRID_IP_OR_URL>" \
  -e NODEGRID_USERNAME="admin" \
  -e NODEGRID_PASSWORD="<PASSWORD>" \
  -e NODEGRID_VERIFY_TLS=0 \
  nodegrid-readonly-gateway:1.9.4
```

#### Option B: Docker Compose
If managing via Compose, update `.env`:
```dotenv
NODEGRID_BASE_URL=https://<NEW_NODEGRID_IP_OR_URL>
NODEGRID_PASSWORD=<PASSWORD>
```
And re-create the service:
```bash
docker compose up -d nodegrid-mcp
```

---

### Step 3: Verify MCP Gateway Startup & Logs
Check the MCP container logs to ensure Uvicorn initialized on port 8000:

```bash
docker logs --tail 20 nodegrid-mcp
```

**Expected Log Output**:
```text
INFO: Started server process [...]
INFO: Waiting for application startup.
INFO: Application startup complete.
INFO: Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

---

### Step 4: Verify Hermes `config.yaml`
Hermes connects to the MCP gateway locally. Ensure `/home/agent/.hermes/config.yaml` has:

```yaml
mcp_servers:
  modem:
    url: http://127.0.0.1:8000/mcp
```

> [!IMPORTANT]
> The URL must **not** have a trailing slash (`/mcp`, not `/mcp/`). A trailing slash triggers a Starlette `307 Temporary Redirect` loop that breaks the MCP JSON-RPC connection.

---

### Step 5: Restart Hermes & Re-index Tools
Restart Hermes to reload tool registrations and flush cached connections:

```bash
# 1. Restart hermes container
docker restart hermes

# 2. Verify modem toolset is active
docker exec hermes hermes mcp list
```

**Expected Output**:
```text
Name      Transport                  Tools    Status
modem     http://127.0.0.1:8000/mcp  all      ✓ enabled
```

---

### Step 6: End-to-End Validation
Prompt Hermes in Slack or terminal:
> *"What is the network status?"*

Follow container logs in real time to observe the ticket exchange and telemetry fetch:
```bash
docker logs -f nodegrid-mcp
```

You should observe:
```text
HTTP Request: POST https://<NEW_NODEGRID_IP_OR_URL>/api/v1/Session "HTTP/1.1 200 OK"
HTTP Request: GET https://<NEW_NODEGRID_IP_OR_URL>/api/v1/tracking/network/interfaces "HTTP/1.1 200 OK"
```
Hermes will now output live interface metrics from the new Nodegrid host.
