---
name: hermes-host-recon
description: "Answer questions about this machine or device reachability."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [recon, network, ip, container, ssh, reachability, capability, probing]
    related_skills: [hermes-chat-surfaces, nodegrid-serial-dance, hermes-agent]
---

# Host & Reachability Recon

Answers "what is your IP", "can you reach X", "do you have access to Y", "if I give you a key can
you SSH in". These questions are answered with a **probe**, never from configuration or memory — and
the answer must separate what was verified from what is only expected.

## Procedure

1. **Answer with the live machine, not the profile.** The user profile describes the user's own
   setup and can disagree with the box the agent is actually running on. Read the environment
   section for the platform, then probe.
2. **Addresses.** One call covers it:
   ```bash
   hostname -I; cat /etc/os-release | head -3; hostname
   ip -4 -o addr show 2>/dev/null | awk '{print $2, $4}'
   curl -s --max-time 8 https://api.ipify.org
   ```
   Report three distinct things, labelled: loopback/internal interfaces, the primary NIC address to
   reach this box from inside the network, and the **public egress** address (what the internet sees).
   State plainly that there is no inbound public address unless something forwards to the box, and
   that "my IP" for an agent is not a service endpoint — it is a process on that host.
   `for i in /sys/class/net/*; do ...` gives MACs and flags virtual bridges (`docker0`, `virbr0`,
   `loopback*`, `sit0`) that should not be presented as user-facing addresses.
3. **Container or host?** Decide before making claims about reachability or filesystem:
   - `/.dockerenv` present, `mount | grep overlay` on `/` → container.
   - `uname -r` (e.g. a vendor/`yocto` kernel) disagreeing with `/etc/os-release` (e.g. Debian) means
     the container sits on an appliance/host whose kernel is the give-away.
   - A bare data mount (`/dev/sda8 on /opt/data`) is a volume, not the host root: the host's
     filesystem is NOT visible from inside, so never promise to edit host files.
   - Devices that live on the host but not in the container (`/dev/ttyS*`, USB serial) cannot be
     touched directly — that work needs the host-side API or its CLI.
4. **Port and reachability probes, no installs.**
   ```bash
   for p in 22 443 80 8080; do timeout 3 bash -c "echo > /dev/tcp/HOST/$p" 2>/dev/null \
     && echo "port $p OPEN" || echo "port $p closed/filtered"; done
   ```
   For SSH, read the **offered auth methods** without credentials — this is the cheapest and most
   decisive probe:
   ```bash
   ssh -o BatchMode=yes -o PreferredAuthentications=none -o StrictHostKeyChecking=accept-new \
       -o ConnectTimeout=6 USER@HOST true
   ```
   `Permission denied (publickey,keyboard-interactive)` proves the service is up and that key auth
   will work; `Connection refused`/timeout is a different (network) answer.
5. **Key bootstrap when a password cannot be automated.** Check `command -v sshpass paramiko`-style
   tooling, but do NOT `pip install` to fix a missing helper — generate a keypair instead, it is
   deterministic and needs nothing new:
   ```bash
   ssh-keygen -t ed25519 -N '' -C 'hermes@<host> -> <target> user' -f $HOME/.ssh/id_<target>
   chmod 600 $HOME/.ssh/id_<target>
   ```
   Hand the **public** line to the user to install on the target (vendor UI / `authorized_keys`), then
   verify with `ssh -i <key> -o IdentitiesOnly=yes USER@HOST '<one-shot cmd>'`. A vendor appliance
   often drops `admin` into its own menu CLI, not a shell — if the one-shot form misbehaves, use
   `ssh -tt` and drive the menu rather than concluding the login failed.

## Answering style

Lead with the answer, then the evidence line. Plain text, no headers or bullets-as-decoration for a
one-line question. Give the exact addresses/handles/paths, and when something is unverified say so in
that same breath ("server offers publickey — so a key will work; the login itself is not tested until
the pubkey is installed"). No narration of the probing.\n\n## Common quick checks\n\nFor frequent host questions (time, CPU, memory, containers, uptime), run the appropriate command and return only the essential answer in a concise format, matching the user\'s preference for one-line responses without extra explanation.\n\n- Time: `date +\"%H:%M:%S\"` → output exactly as `HH:MM:SS`\n- CPU usage: `top -bn1 | grep \"Cpu(s)\"` → report the usage percentage (e.g., `56.5%`) or a simple bar.\n- Memory: `free -h` → report used/total (e.g., `2.1G/7.8G`)\n- Containers: if Docker daemon accessible, `docker ps --format \"{{.Names}}\"` → list names or \"none\"; if not accessible, report \"Docker daemon not reachable\".\n- Uptime: `uptime -p` → output as-is.

## Pitfalls

- **The secret file costs a shell approval; the config file does not.** `config.yaml`,
  `channel_directory.json`, `gateway_state.json`, `/etc/os-release` and `hostname -I` are free reads.
  A heredoc or `python -c` that opens `.env` (or that calls a platform API with a token) triggers an
  approval prompt, and when the user is away it auto-blocks after minutes with **no** output — the
  turn is lost. If a question can be answered without a secret, answer it without one; if the user
  must know a cosmetic detail that needs a token lookup, say the detail is unavailable in this
  session instead.
- **Never put a private key or password in chat.** Chat history is durable and replayed into later
  sessions. Have the user place key material on disk / in the vendor UI, and paste only the public
  half. Never echo a token while debugging either.
- **A missing local helper is not a capability limit.** Absent `sshpass`, `paramiko`, `expect`, or
  `screen` changes the *route* to a device (key auth, `ssh -tt`), not whether the device is reachable.
  Report the route, and never record "tool X does not work" as a standing fact.
- **Capability claims need one probe each.** "Installed" ≠ "reachable" ≠ "able to do the thing":
  config `enabled: true` is not a live connection, an open port is not a successful login, and an API
  that answers on one path is not an API that exposes the path you want. Say which one you verified.
- **Probe every address before declaring a device down.** Multi-homed appliances answer on several
  local addresses of the same host; a failure against one is frequently the wrong interface, not a
  dead box.
