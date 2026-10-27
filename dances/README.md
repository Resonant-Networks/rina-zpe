# Nodegrid Serial Port & LED Dance Scripts

This directory contains automation scripts designed to control, sweep, and sequence Nodegrid serial ports and status LEDs.

## Available Dance Routines

| Script | Method | Description |
|---|---|---|
| `light_sweep_dance.py` | REST API (`/settings/devices`) | Sweeps across console ports sequentially, enabling and disabling LEDs with a configurable delay. |
| `dance_ripple_final.py` | Concurrent REST API | Generates an outward ripple pattern from center ports to edges. |
| `ls_dance_loop.sh` | Bash daemon | Runs `light_sweep_dance.py` in an infinite background loop with logging to `ls_dance_loop.log`. |
| `cpu_loop.sh` | Shell arithmetic | Stress script for testing CPU load and activity triggers on the appliance. |

## Running the Dances

```bash
# Direct run via python
python3 light_sweep_dance.py

# Daemonized loop run
./ls_dance_loop.sh &
```

> [!NOTE]
> The Nodegrid REST API has an intrinsic switching latency of ~5.5s to 6.5s per port enable/disable cycle. Keep the delay parameter between 0.3s and 0.5s; setting delay to 0 does not speed up physical port relays.
