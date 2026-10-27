# Nodegrid admin shell & swap housekeeping

Use when free/swap is exhausted and you need to run OS-level commands on the box.

## Reach the admin shell over SSH

SSH key auth is rejected and there is NO `sudo`/`sshpass` binary on the host; use the
Nodegrid CLI's `shell` escape with password auth via an askpass helper.

1. The runtime is ON the box, so target a LAN address from `hostname -I` (e.g. `192.168.72.10`).
2. Provide the password non-interactively with `SSH_ASKPASS`:
   ```sh
   export SSH_ASKPASS=/opt/data/cache/scratch/askpass_nodegrid.sh   # prints '<NODEGRID_PASSWORD>'
   export SSH_ASKPASS_REQUIRE=force DISPLAY=:0
   ssh -tt -o StrictHostKeyChecking=no -o PreferredAuthentications=keyboard-interactive,password \
       -o PubkeyAuthentication=no admin@<lan-ip>
   ```
3. You land in a restricted Nodegrid CLI (`... Invalid command: id`). Enter `shell` to
get a real bash prompt (`admin@RS1-ZPE:~$`).
4. Run OS commands there. `sudo` works passwordless in the shell (the earlier `su` to root
with `<NODEGRID_PASSWORD>` fails — do NOT try `su`; use the CLI `shell` escape instead).
5. `exit` returns to the CLI, `logout` is invalid there; just kill the SSH session.

## Clear exhausted swap

Swap pegs at 100% under sustained load (repeated light sweeps). Cycle it off/on to free it:
```sh
sudo swapoff -a && sudo swapon -a && free -m
```
Expect: swap used -> ~0; RAM available dips briefly while swap pages move back to RAM
(not an error). Swap refills quickly if the load source (long-running sweep) continues.

## Pitfalls
- `-c`/single-command args do not pass through the Nodegrid CLI to the shell; use an
  interactive `ssh -tt` session and type commands, or let the shell escape prompt you.
- The CLI rejects OS commands outright (`Error: Invalid command`) — always `shell` first.
- Not a durable rule, but today's box shows `10.15.235.116`/`192.168.72.18` unreachable
  while `https://127.0.0.1` answers 200 on the API (runtime on-box).
