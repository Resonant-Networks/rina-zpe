#!/usr/bin/env bash
# ==============================================================================
# deploy.sh — Unified Deployment Script for Nodegrid Appliances (rina-zpe)
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

echo "=== [1/4] Checking Environment Configuration ==="
if [ ! -f .env ]; then
  if [ -f .env.example ]; then
    echo "Warning: .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "Please edit .env with your real credentials before running deployment."
    exit 1
  else
    echo "Error: Neither .env nor .env.example found."
    exit 1
  fi
fi

# Load environment
# shellcheck disable=SC2046
export $(grep -v '^#' .env | xargs)

echo "=== [2/4] Deploying Tailscale Gateway ==="
if [ -f docker/tailscale/docker-run.sh ]; then
  bash docker/tailscale/docker-run.sh
fi

echo "=== [3/4] Building and Deploying Nodegrid MCP ==="
if [ -f docker/nodegrid-mcp/Dockerfile ]; then
  echo "Building nodegrid-readonly-gateway:1.9.4..."
  docker build -t nodegrid-readonly-gateway:1.9.4 docker/nodegrid-mcp/
  bash docker/nodegrid-mcp/docker-run.sh
fi

echo "=== [4/4] Deploying Hermes Agent ==="
if [ -f docker/hermes/docker-run.sh ]; then
  bash docker/hermes/docker-run.sh
fi

echo "=== Deployment Complete ==="
echo "Active containers:"
docker ps --filter "name=zpe-tailscale-gateway" --filter "name=nodegrid-mcp" --filter "name=hermes"
