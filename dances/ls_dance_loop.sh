#!/bin/sh
# Continuous light sweep: runs sweep cycles until killed.
i=0
while true; do
  i=$((i+1))
  echo "[LOOP] cycle $i start $(date -u +%H:%M:%S)"
  python3 /tmp/ls_dance.py -d 0.2 -c 1 >> /opt/data/ls_dance_loop.log 2>&1
  echo "[LOOP] cycle $i finished $(date -u +%H:%M:%S)"
  sleep 1
done