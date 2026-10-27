#!/usr/bin/env bash
# Deploys Hermes Agent on Nodegrid host network
set -euo pipefail

CONTAINER_NAME="hermes"
DATA_DIR="${HERMES_DATA_DIR:-/home/agent/.hermes}"

# Load .env if present
if [ -f ../../.env ]; then
  # shellcheck disable=SC2046
  export $(grep -v '^#' ../../.env | xargs)
elif [ -f .env ]; then
  # shellcheck disable=SC2046
  export $(grep -v '^#' .env | xargs)
fi

mkdir -p "${DATA_DIR}"

echo "Removing existing container ${CONTAINER_NAME} if present..."
docker rm -f "${CONTAINER_NAME}" 2>/dev/null || true

echo "Starting ${CONTAINER_NAME}..."
docker run -d \
  --name "${CONTAINER_NAME}" \
  --network host \
  --restart unless-stopped \
  -v "${DATA_DIR}:/opt/data" \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -e SLACK_BOT_TOKEN="${SLACK_BOT_TOKEN:-}" \
  -e SLACK_APP_TOKEN="${SLACK_APP_TOKEN:-}" \
  nousresearch/hermes-agent:latest

echo "${CONTAINER_NAME} started successfully."
