#!/usr/bin/env bash
# Deploys Tailscale Gateway on Nodegrid host network
set -euo pipefail

CONTAINER_NAME="zpe-tailscale-gateway"

# Load .env if present
if [ -f ../../.env ]; then
  # shellcheck disable=SC2046
  export $(grep -v '^#' ../../.env | xargs)
elif [ -f .env ]; then
  # shellcheck disable=SC2046
  export $(grep -v '^#' .env | xargs)
fi

mkdir -p "${TAILSCALE_STATE_DIR:-/home/admin/tailscale-state}"

echo "Removing existing container ${CONTAINER_NAME} if present..."
docker rm -f "${CONTAINER_NAME}" 2>/dev/null || true

echo "Starting ${CONTAINER_NAME}..."
docker run -d \
  --name "${CONTAINER_NAME}" \
  --network host \
  --restart unless-stopped \
  --cap-add=NET_ADMIN \
  --cap-add=SYS_MODULE \
  -v "${TAILSCALE_STATE_DIR:-/home/admin/tailscale-state}:/var/lib/tailscale" \
  -v /dev/net/tun:/dev/net/tun \
  -e TS_STATE_DIR=/var/lib/tailscale \
  -e TS_USERSPACE=false \
  -e TS_EXTRA_ARGS="--reset --accept-dns=false --accept-routes --advertise-routes=${TS_ADVERTISE_ROUTES:-192.168.74.0/24} --advertise-exit-node" \
  tailscale/tailscale:latest

echo "${CONTAINER_NAME} started successfully."
