# Nodegrid REST API Reference

The ZPE Nodegrid OS exposes an HTTPS REST API at `https://<host>/api/v1`.

## Authentication Flow

Nodegrid uses session ticket-based authentication.

### Step 1: Obtain Session Ticket
- **Method**: `POST`
- **Endpoint**: `/api/v1/Session`
- **Request Body**:
  ```json
  {
    "username": "admin",
    "password": "<PASSWORD>"
  }
  ```
- **Response Headers**:
  `Set-Cookie: session_id=<SESSION_ID>`
- **Response Body**:
  ```json
  {
    "status": "success",
    "session": "Cvn6z4mmTjFkXx02hHuIquoK5GZ9qkY/GA==",
    "user": "admin"
  }
  ```

### Step 2: Authenticated Requests
Pass the session ticket in the `ticket:` header (or cookie):
```bash
curl -k -H "ticket: <SESSION_TICKET>" https://127.0.0.1/api/v1/tracking/network/interfaces
```

### Step 3: Session Teardown
- **Method**: `DELETE`
- **Endpoint**: `/api/v1/Session`
- **Header**: `ticket: <SESSION_TICKET>`

---

## Key Telemetry Endpoints

### 1. Network Interfaces
- **Endpoint**: `GET /api/v1/tracking/network/interfaces`
- Returns interface names, operational state, packet counters, and collision stats.

### 2. Managed Devices / Serial Ports
- **Endpoint**: `GET /api/v1/settings/devices`
- Returns configured console ports (e.g. `ttyS1`, `ttyS2`), speed, parity, and target host labels.

### 3. Port Enable / Disable (Used by Dances)
- **Endpoint**: `PUT /api/v1/settings/devices/{device_id}/enable`
- **Endpoint**: `PUT /api/v1/settings/devices/{device_id}/disable`
- Activates or deactivates console port interfaces and their associated front-panel LEDs.
- *Note*: Hardware relay switching requires approximately 5.5s to 6.5s per action.
