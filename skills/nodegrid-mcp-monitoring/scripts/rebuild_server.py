#!/usr/bin/env python3
"""
Nodegrid Read-Only Gateway — MCP server (rebuild).

Read-only Nodegrid status tools over MCP (streamable HTTP), proxying the ZPE
Nodegrid REST API. Faithful rebuild of the "modem" server
("Nodegrid Read-Only Gateway" v1.9.4).

Env config: NODEGRID_BASE_URL (default http://127.0.0.1), NODEGRID_USERNAME
(default admin), NODEGRID_PASSWORD (required), NODEGRID_VERIFY_TLS (0/1),
MCP_HOST (default 0.0.0.0), MCP_PORT (default 8000).
"""
from __future__ import annotations

import asyncio
import json
import os
from typing import Any

import httpx
from mcp.server.mcpserver import MCPServer

BASE_URL: str = os.environ.get("NODEGRID_BASE_URL", "http://127.0.0.1").rstrip("/")
USERNAME: str = os.environ.get("NODEGRID_USERNAME", "admin")
PASSWORD: str = os.environ.get("NODEGRID_PASSWORD", "")
VERIFY_TLS: bool = os.environ.get("NODEGRID_VERIFY_TLS", "0") == "1"
TIMEOUT: float = float(os.environ.get("NODEGRID_TIMEOUT", "30"))

API = f"{BASE_URL}/api/v1"

_ticket: str | None = None
_ticket_lock = asyncio.Lock()


async def _get_ticket() -> str:
    global _ticket
    if _ticket:
        return _ticket
    async with _ticket_lock:
        if _ticket:
            return _ticket
        async with httpx.AsyncClient(verify=VERIFY_TLS, timeout=TIMEOUT) as client:
            resp = await client.post(
                f"{API}/Session",
                json={"username": USERNAME, "password": PASSWORD},
            )
            resp.raise_for_status()
            _ticket = resp.json()["session"]
        return _ticket


async def _get(path: str) -> Any:
    ticket = await _get_ticket()
    url = f"{API}/{path.lstrip('/')}"
    async with httpx.AsyncClient(verify=VERIFY_TLS, timeout=TIMEOUT) as client:
        resp = await client.get(
            url, headers={"ticket": ticket, "accept": "application/json"}
        )
        if resp.status_code == 404 and "Session" in resp.text.upper():
            global _ticket
            _ticket = None
            ticket = await _get_ticket()
            resp = await client.get(
                url, headers={"ticket": ticket, "accept": "application/json"}
            )
        resp.raise_for_status()
        try:
            return resp.json()
        except json.JSONDecodeError:
            return {"raw": resp.text}


server = MCPServer(name="Nodegrid Read-Only Gateway", version="1.9.4")


@server.tool()
async def get_cellular_status() -> Any:
    """Get cellular modem status."""
    return await _get("tracking/devices/wirelessmodem")


@server.tool()
async def get_cellular_detail(modem_id: str) -> Any:
    """Get detailed per-SIM cellular metrics."""
    return await _get(f"tracking/devices/wirelessmodem/{modem_id}")


@server.tool()
async def get_system_overview() -> Any:
    """Get system info: firmware, model, uptime, licenses and slots."""
    return await _get("system/about")


@server.tool()
async def get_system_metrics() -> dict:
    """Get live CPU, memory and disk metrics."""
    cpu, mem, disk = await asyncio.gather(
        _get("tracking/system/cpu"),
        _get("tracking/system/memory"),
        _get("tracking/system/disk"),
    )
    return {"cpu": cpu, "memory": mem, "disk": disk}


@server.tool()
async def list_managed_devices() -> Any:
    """Get all managed devices registered in Nodegrid."""
    return await _get("devices/table")


@server.tool()
async def get_managed_device(device_name: str) -> Any:
    """Get details for a specific managed device."""
    return await _get(f"devices/table/{device_name}")


@server.tool()
async def get_device_outlets_status(device_name: str) -> Any:
    """Get status of power outlets for a device."""
    return await _get(f"devices/table/{device_name}/outlets/status")


@server.tool()
async def get_network_interfaces() -> Any:
    """Get network interfaces traffic and operational status."""
    return await _get("tracking/network/interfaces")


@server.tool()
async def get_wifi_status() -> Any:
    """Get Wi-Fi network connections."""
    return await _get("tracking/network/hotspot")


@server.tool()
async def list_users() -> Any:
    """List all local user accounts."""
    return await _get("security/localaccounts")


@server.tool()
async def get_user_detail(username: str) -> Any:
    """Get detailed account information."""
    return await _get(f"security/localaccounts/{username}")


@server.tool()
async def get_active_sessions() -> Any:
    """List currently active user sessions."""
    return await _get("tracking/opensessions")


@server.tool()
async def query_nodegrid_api(path: str) -> Any:
    """Query a read-only GET endpoint in the Nodegrid API."""
    return await _get(path)


def main() -> None:
    host = os.environ.get("MCP_HOST", "0.0.0.0")
    port = int(os.environ.get("MCP_PORT", "8000"))
    asyncio.run(
        server.run_streamable_http_async(
            host=host, port=port, streamable_http_path="/mcp"
        )
    )


if __name__ == "__main__":
    main()
