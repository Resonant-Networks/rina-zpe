---
name: tailscale-troubleshooting
description: "Diagnose and fix Tailscale connectivity issues."
version: 1.0.0
author: Au Wai Choon (hfx), Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [tailscale, tailnet, docker, nodegrid, networking, wireguard, tun]
---

# Tailscale Troubleshooting

Diagnose and fix Tailscale connectivity on this infrastructure: the tailnet
spans ZPE Nodegrid devices and servers, with Tailscale running inside Docker
containers (`zpe-tailscale-gateway` et al.) in `--network host` mode.

## When to Use

- A peer can't be pinged / reached over `100.x` while internet still works
- A `tailscale` Docker container is crash-looping
- Subnet routes or exit-node advertisement isn't working
- Question of "why direct vs relay" between peers

## First diagnostic: `tailscale status --json`

Run inside the container (`docker exec <name> tailscale status --json`). Read
these fields before touching anything:

- `"TUN": false` → tailscaled is in **userspace-networking** mode: no
  `tailscale0` interface, no `100.64.0.0/10` route in the kernel. `ping` to a
  peer fails (packets fall out the default route to the internet) while
  `8.8.8.8` works. This is the #1 cause of "can't ping peers."
- `"Health"` array → actionable warnings, e.g. `--accept-routes is false`
  (peers advertise routes but this node won't accept them).
- Peer `"Active"` / `"InEngine"` / `"LastHandshake"` → a bare `-` or
  zero-time handshake means no connection was ever established to that peer,
  not even a relay.
- Peer `active; relay "sin"` vs `active; direct <ip>` → relay-only means the
  host's uplink is carrier-NAT'd RFC1918 with no usable IPv6; direct is only
  possible when a peer is on a real LAN.

## Fixing TUN mode (userspace → kernel)

The `tailscale/tailscale` image's `containerboot` defaults to userspace
networking unless told otherwise. Mounting `/dev/net/tun` and adding
`NET_ADMIN`/`SYS_MODULE` caps is NOT enough — set the env var:

```
-e TS_USERSPACE=false
```

This is decided at container start; a running container cannot be hot-patched
into TUN mode. Recreate it (`docker rm -f` + `docker run`).

## Fixing the stale-prefs crash loop

Symptom (repeats every few seconds): tailscaled comes up, then dies with

```
Error: changing settings via 'tailscale up' requires mentioning all
non-default flags. ... re-run with --reset or use:
  tailscale up --accept-dns=false ...
```

Cause: persisted state (`--statedir`, the `tailscale-state` volume) still
holds old settings that conflict with the new `TS_EXTRA_ARGS`. Tailscale
refuses a settings change unless every non-default flag is restated, and
`containerboot`'s generated `tailscale up` doesn't include them.

Fix: add `--reset` to `TS_EXTRA_ARGS` (clears stale prefs; node identity and
key survive — no re-auth needed). Or restate all non-default flags
explicitly, including `--accept-dns=false`.

## Subnet routing / exit node prerequisites

- Enable IP forwarding on the host, or subnet routing silently won't work:
  `sysctl -w net.ipv4.ip_forward=1` (and `net.ipv6.conf.all.forwarding=1`).
  The `ip-forwarding-off` warning in `tailscale status` flags this.
- `--advertise-routes` must match the ACTUAL LAN subnet of the interface.
  Verify against the real interface (`/sys/class/net/<if>/` or the routing
  table) — advertising a stale subnet that doesn't exist is a dead route.
- Add `--accept-routes` if this node should honor peers' advertised routes.

## Reaching peers from the Hermes container

From the Hermes agent container there is no `tailscale` binary, no
`/var/run/docker.sock`, and no Docker daemon — but the tailnet data plane is
still reachable, so `ping <peer-100.x-ip>` works even when the hostname does
not resolve. Known peers (resolve via `/proc/net` reachability, not DNS):
`rm1dev-control` = `100.80.103.95` (hostname `rm1dev-control` does NOT resolve
from inside the container). To reach a peer over SSH, use its `100.x` IP, not
the hostname.

## Pitfalls

- `docker exec` from the Hermes agent container is impossible: the agent runs
  in its own netns with no `/var/run/docker.sock`, no `sudo`, no `ip`,
  `iptables`, or `nft`. Diagnose from the host (`root@RS1-ZPE`) or read
  `/proc/net/route`, `/proc/net/fib_trie`, `/sys/class/net/*/operstate` locally.
- Inspect first, don't hotfix: the user's standard is "inspect only" until
  asked. State the root cause and the recreate command; don't run it unasked.
- Access to private RFC1918 addresses and self-signed/insecure-TLS REST calls
  trigger Hermes security scans requiring approval — expect it.

## Verification

After a fix: `ip a` (host) must show `tailscale0` with the node's `100.x` IP;
`tailscale status` must show the self node `Active`; then `ping <peer-ip>` over
IPv4 must return replies (possibly via relay — normal for carrier-NAT'd hosts).
