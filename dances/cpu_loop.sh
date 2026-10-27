#!/bin/bash
end=$(( $(date +%s) + 20 ))
while [ $(date +%s) -lt $end ]; do
    cpu=$(/opt/hermes/bin/hermes -z "What is the current CPU usage? Use the MCP tool get_system_metrics to get the data and report only the CPU usage percentage." 2>/dev/null)
    echo "$(date +'%T') CPU: $cpu"
    sleep 2
done