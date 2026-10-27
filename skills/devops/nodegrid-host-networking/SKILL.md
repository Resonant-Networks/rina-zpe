---
name: nodegrid-host-networking
description: "Use when inspecting Nodegrid host networking."
version: 1.0.0
metadata:
  hermes:
    tags: [nodegrid, networking, routes, interfaces, tailscale, proc, reachability, ping]
    category: devops
---

# Nodegrid Host Networking Inspection

## Context
The RINA runtime runs ON the Nodegrid (hostname RS1-ZPE) inside a minimal
container. Standard net tools are ABSENT: no `ip`, `ifconfig`, `route`,
`iptables`, `nft`, `ss`, or `tailscale` binary. Do not attempt them — inspect
kernel state through `/proc` and `/sys` instead, which always work.

## First pass: MCP modem tools (preferred)
The `modem` MCP server (local, http://127.0.0.1:8000/mcp/) gives a clean
read without parsing /proc: `get_network_interfaces` (per-ifname state + rx/tx
packet counters), `get_system_overview` (model/firmware/uptime/licenses),
`get_wifi_status` (SSID connection list + ipv4), `get_cellular_status`
(slot/SIM state/signal). Prefer these for a network report; fall back to
/proc below for anything they omit (routes, exact local addresses).
`query_nodegrid_api` expects a path RELATIVE to /api/v1 — pass
`/network/interfaces`, NOT `/api/v1/network/interfaces` (which 404s as
`/api/v1/api/v1/...`).

## Interfaces
```bash
ls /sys/class/net/                 # interface list
cat /sys/class/net/<if>/operstate  # up | down | unknown
cat /sys/class/net/<if>/carrier    # 1 = link up, 0 = no carrier
cat /sys/class/net/<if>/address    # MAC
```
Known interfaces on this box: `wlan0` (192.168.70.x), `backplane0`
(192.168.74.x), `wwan0` (cellular, often down), `eth0`, `docker0` (172.17.x),
`virbr0` (192.168.122.x), plus `loopback`/`loopback0`/`net0`/`sit0`.

## Routing
```bash
cat /proc/net/route      # iface dest gateway flags mask (all hex)
cat /proc/net/fib_trie   # full FIB: local addresses + routes, readable
```
Gateway/mask in `/proc/net/route` are little-endian bytes. `0146A8C0` =
192.168.70.1, `0046A8C0` = 192.168.70.0, `00FFFFFF` = /24.

## Reachability
`ping` IS available. `getent hosts <name>` resolves via /etc/hosts only
(no external DNS in this container; /etc/resolv.conf points at 127.0.0.1).

## Tailscale topology (critical)
Tailscale runs on this host (see `tailscale0` in `/sys/class/net/`, carrier=1
when up); its CGNAT address appears as a LOCAL host address in
`/proc/net/fib_trie` (e.g. `100.123.118.15 /32 host LOCAL`). The `tailscale`
CLI binary is NOT on PATH in the agent container, so `tailscale status`
fails with command-not-found. Distinguish the two topologies you may see:

- Tailscale on-host (this box): `tailscale0` IS present in `/sys/class/net/`
  and its `100.x` address IS in `/proc/net/fib_trie` Local table. Reach peers
  only via the host's tailscale control plane; the agent netns may still
  lack a `100.64.0.0/10` route (see pitfall).
- Tailscale in a SEPARATE container (`zpe-tailscale-gateway`, host-network
  mode): it holds the `100.x` CGNAT address and the `tun` device. The agent
  container is NOT on that netns, so:
  - No `100.64.0.0/10` route appears in `/proc/net/route`.
  - No `tailscale0`/`tun` interface in `/sys/class/net/`.
  - `ping <100.x peer>` fails 100% (egresses via default wlan0 route to the
    internet, where 100.64/10 is non-routable) while `ping 8.8.8.8` works.
  - SSH into this box FROM another tailscale device works, because the
    tailscale container handles that inbound path — it does NOT mean the agent
    container can reach tailscale peers outbound.

When tailscale lives in a separate container, run
`docker exec -it zpe-tailscale-gateway sh` and inside use `tailscale status`.
Distinguish peer health by the status line: `active; relay "<region>"` = live
path with tx/rx counters; a bare `-` = registered but no established
direct/relay connection; `offline` = stale.

Determine whether tailscale is on-host vs containerized by checking BOTH
`ls /sys/class/net/` for `tailscale0` AND `/proc/net/fib_trie` for a
`100.x ... host LOCAL` entry; do not assume one topology from a single signal.

## Pitfalls
- "Can't ping a tailscale peer" is almost never the peer — first check
  `/proc/net/route` for a `100.64.0.0/10` entry. Absent = no tailscale data
  plane in THIS netns; the fix lives in the tailscale container, not here.
- `docker ps`/`docker image ls` fail with "Cannot connect to the Docker daemon"
  in the agent container — the daemon socket is not mounted here. Inspect
  docker state only from the host shell, not from inside the agent container.
- `tailscale` is not on PATH in the agent container; `tailscale status` is
  command-not-found here even when tailscale is running on the host. Read its
  state from `/sys/class/net/tailscale0` and `/proc/net/fib_trie`, not the CLI.
- No iptables/nft binaries means firewall state cannot be read from this
  container; a missing route (see above) is the more likely cause of
  unreachability than a firewall rule.
- This Nodegrid build has no `modprobe`, no `/lib/modules/`, no `/dev/net/tun`,
  and no `dockerd`/`containerd` in the agent container — a bare Docker
  `tailscale/tailscale` container cannot run here as-is. It needs the tun
  device + a running daemon, which are host-level provisioning, not something
  fixable from the agent shell.
