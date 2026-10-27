import os
import urllib3
import requests
from typing import Optional, Any, Dict
from mcp.server.fastmcp import FastMCP

# Suppress self-signed certificate warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

NODEGRID_HOST = os.getenv(
    "NODEGRID_HOST",
    "https://192.168.72.8"
).rstrip("/")

NODEGRID_USERNAME = os.getenv("NODEGRID_USERNAME", "admin")
NODEGRID_PASSWORD = os.getenv("NODEGRID_PASSWORD", "")
NODEGRID_API_KEY = os.getenv("NODEGRID_API_KEY", "")

MCP_PORT = int(os.getenv("MCP_PORT", "8000"))
MCP_PATH = os.getenv("MCP_STREAMABLE_HTTP_PATH", "/mcp")
MCP_TRANSPORT = os.getenv("MCP_TRANSPORT", "streamable-http")

mcp = FastMCP(
    "Nodegrid Read-Only Gateway",
    host="0.0.0.0",
    port=MCP_PORT
)

mcp.settings.streamable_http_path = MCP_PATH

_cached_ticket: Optional[str] = None


def get_auth_headers() -> Dict[str, str]:
    global _cached_ticket

    if NODEGRID_API_KEY and NODEGRID_USERNAME:
        return {
            "username": NODEGRID_USERNAME,
            "api_key": NODEGRID_API_KEY,
            "accept": "application/json",
        }

    if _cached_ticket:
        return {
            "ticket": _cached_ticket,
            "accept": "application/json",
        }

    auth_url = f"{NODEGRID_HOST}/api/v1/Session"

    payload = {
        "username": NODEGRID_USERNAME,
        "password": NODEGRID_PASSWORD,
    }

    resp = requests.post(
        auth_url,
        json=payload,
        verify=False,
        timeout=10,
    )

    resp.raise_for_status()

    _cached_ticket = resp.json().get("session")

    return {
        "ticket": _cached_ticket,
        "accept": "application/json",
    }


def execute_read_request(
    path: str,
    params: Optional[Dict[str, Any]] = None
) -> Any:

    global _cached_ticket

    clean_path = path.strip()

    if not clean_path.startswith("/"):
        clean_path = "/" + clean_path

    # Safety guard: strictly block state-changing paths
    dangerous_keywords = [
        "/reset",
        "/cycle",
        "/upgrade",
        "/reboot",
        "/delete",
        "/send",
    ]

    if any(
        keyword in clean_path.lower()
        for keyword in dangerous_keywords
    ):
        return {
            "error": (
                f"Path '{clean_path}' blocked: "
                "Write/Execution endpoints are prohibited."
            )
        }

    url = f"{NODEGRID_HOST}/api/v1{clean_path}"

    headers = get_auth_headers()

    try:
        resp = requests.get(
            url,
            headers=headers,
            params=params,
            verify=False,
            timeout=20,
        )

        # Retry once if session ticket expired
        if resp.status_code == 401 and not NODEGRID_API_KEY:
            _cached_ticket = None

            headers = get_auth_headers()

            resp = requests.get(
                url,
                headers=headers,
                params=params,
                verify=False,
                timeout=20,
            )

        if resp.status_code != 200:
            return {
                "status_code": resp.status_code,
                "error": resp.text,
            }

        return resp.json()

    except Exception as e:
        return {
            "error": str(e)
        }


# =====================================================================
# TOOLS
# =====================================================================

@mcp.tool()
def get_cellular_status() -> Any:
    """Get cellular modem status."""
    return execute_read_request(
        "/tracking/devices/wirelessmodem"
    )


@mcp.tool()
def get_cellular_detail(modem_id: str) -> Any:
    """Get detailed per-SIM cellular metrics."""
    return execute_read_request(
        f"/tracking/devices/wirelessmodem/{modem_id}"
    )


@mcp.tool()
def get_system_overview() -> Dict[str, Any]:
    """Get system info: firmware, model, uptime, licenses and slots."""
    return {
        "about": execute_read_request("/system/about"),
        "licenses": execute_read_request("/system/licenses"),
        "slots": execute_read_request("/system/slots"),
    }


@mcp.tool()
def get_system_metrics() -> Dict[str, Any]:
    """Get live CPU, memory and disk metrics."""
    return {
        "cpu": execute_read_request("/tracking/system/cpu"),
        "memory": execute_read_request("/tracking/system/memory"),
        "disk": execute_read_request("/tracking/system/disk"),
    }


@mcp.tool()
def list_managed_devices() -> Any:
    """Get all managed devices registered in Nodegrid."""
    return execute_read_request("/devices/table")


@mcp.tool()
def get_managed_device(device_name: str) -> Any:
    """Get details for a specific managed device."""
    return execute_read_request(
        f"/devices/table/{device_name}"
    )


@mcp.tool()
def get_device_outlets_status(device_name: str) -> Any:
    """Get status of power outlets for a device."""
    return execute_read_request(
        f"/devices/table/{device_name}/outlets/status"
    )


@mcp.tool()
def get_network_interfaces() -> Any:
    """Get network interfaces traffic and operational status."""
    return execute_read_request(
        "/tracking/network/interfaces"
    )


@mcp.tool()
def list_users() -> Any:
    """List all local user accounts."""
    return execute_read_request(
        "/security/localaccounts"
    )


@mcp.tool()
def get_user_detail(username: str) -> Any:
    """Get detailed account information."""
    return execute_read_request(
        f"/security/localaccounts/{username}"
    )


@mcp.tool()
def get_active_sessions() -> Any:
    """List currently active user sessions."""
    return execute_read_request(
        "/tracking/opensessions"
    )


@mcp.tool()
def get_wifi_status() -> Any:
    """Get Wi-Fi network connections."""

    conns = execute_read_request(
        "/network/connections"
    )

    if isinstance(conns, list):

        wifi = [
            c for c in conns
            if (
                "wifi" in str(
                    c.get("type", "")
                ).lower()
                or c.get("wifi_ssid")
            )
        ]

        return (
            wifi
            if wifi
            else {
                "message": "No active Wi-Fi connections found",
                "all_connections": conns,
            }
        )

    return conns


@mcp.tool()
def query_nodegrid_api(path: str) -> Any:
    """Query a read-only GET endpoint in the Nodegrid API."""
    return execute_read_request(path)


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    print(
        f"Starting FastMCP with transport='{MCP_TRANSPORT}' "
        f"on http://0.0.0.0:{MCP_PORT}{MCP_PATH}"
    )

    mcp.run(transport=MCP_TRANSPORT)

