#!/usr/bin/env bash
# Sync code to the production server and rebuild the running services.
# Does NOT touch the server's .env — it has its own POSTGRES_PASSWORD/CORS_ORIGINS/WEB_PORT
# that must never be overwritten by the local .env (see 2026-09-05 incident).
set -euo pipefail
cd "$(dirname "$0")/.."

set -a; source .env; set +a

REMOTE_DIR=/opt/habit-heatmap-dashboard

sshpass -p "$SERVER_PASSWORD" rsync -az --delete \
  --exclude='.git' --exclude='node_modules' --exclude='.venv' --exclude='local-agent' \
  --exclude='dist' --exclude='__pycache__' --exclude='*.pyc' \
  --exclude='.env' \
  -e "ssh -o StrictHostKeyChecking=no" \
  ./ "$SERVER_USER@$SERVER_IP:$REMOTE_DIR/"

sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" \
  "cd $REMOTE_DIR && docker compose up -d --build"

echo "Deployed. Checking https://fin.garaev.tech/api/metrics ..."
curl -s -o /dev/null -w "HTTP %{http_code}\n" https://fin.garaev.tech/api/metrics
