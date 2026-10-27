#!/usr/bin/env bash
# Deploys Nodegrid Read-Only Gateway (MCP 2.x Streamable HTTP)
set -euo pipefail

CONTAINER_NAME="nodegrid-mcp"
IMAGE_NAME="nodegrid-readonly-gateway:1.9.4"

# Load .env if present
if [ -f ../../.env ]; then
  # shellcheck disable=SC2046
  export $(grep -v '^#' ../../.env | xargs)
elif [ -f .env ]; then
  # shellcheck disable=SC2046
  export $(grep -v '^#' .env | xargs)
fi

echo "Removing existing container ${CONTAINER_NAME} if present..."
docker rm -f "${CONTAINER_NAME}" 2>/dev/null || true

echo "Starting ${CONTAINER_NAME}..."
docker run -d \
  --name "${CONTAINER_NAME}" \
  --network host \
  --restart unless-stopped \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_HOST=0.0.0.0 \
  -e MCP_PORT=8000 \
  -e MCP_STREAMABLE_HTTP_PATH=/mcp \
  -e NODEGRID_BASE_URL="${NODEGRID_BASE_URL:-https://127.0.0.1}" \
  -e NODEGRID_USERNAME="${NODEGRID_USERNAME:-admin}" \
  -e NODEGRID_PASSWORD="${NODEGRID_PASSWORD:?NODEGRID_PASSWORD must be set}" \
  -e NODEGRID_VERIFY_TLS="${NODEGRID_VERIFY_TLS:-0}" \
  "${IMAGE_NAME}"

echo "${CONTAINER_NAME} started successfully on host port 8000."
