# Tailscale Gateway for Nodegrid

Runs Tailscale inside Docker with `network_mode: host` and kernel TUN capabilities (`/dev/net/tun`) to route appliance traffic and advertise local subnets across the Tailnet.

## Host Prerequisites
- Device node: `/dev/net/tun`
- CapAdd: `NET_ADMIN`, `SYS_MODULE`
- Persistent state volume: `/home/admin/tailscale-state`

## Subnet Routing Configuration
- `TS_EXTRA_ARGS`:
  - `--reset`: Resets previous lingering flags.
  - `--accept-dns=false`: Prevents MagicDNS from overriding Nodegrid local resolver.
  - `--accept-routes`: Accepts routes from peer nodes.
  - `--advertise-routes=<subnet>`: Advertises local rack subnets (e.g. `192.168.74.0/24`).
  - `--advertise-exit-node`: Allows this gateway to serve as an exit node.
