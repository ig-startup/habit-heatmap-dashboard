#!/usr/bin/env bash
# Sync code to the production server and rebuild the running services.
# Does NOT touch the server's .env — it has its own POSTGRES_PASSWORD/CORS_ORIGINS/WEB_PORT
# that must never be overwritten by the local .env (see 2026-09-05 incident).
set -euo pipefail
cd "$(dirname "$0")/.."

set -a; source .env; set +a

REMOTE_DIR=/opt/habit-heatmap-dashboard

# Uses SSH key auth (see ~/.ssh/id_ed25519) if set up; falls back to sshpass with
# SERVER_PASSWORD when no key is authorized on the server yet.
SSH_CMD="ssh -o StrictHostKeyChecking=no"
if ! ssh -o BatchMode=yes -o ConnectTimeout=5 -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" true 2>/dev/null; then
  SSH_CMD="sshpass -p $SERVER_PASSWORD ssh -o StrictHostKeyChecking=no"
fi

rsync -az --delete \
  --exclude='.git' --exclude='node_modules' --exclude='.venv' --exclude='local-agent' \
  --exclude='dist' --exclude='__pycache__' --exclude='*.pyc' \
  --exclude='.env' \
  -e "$SSH_CMD" \
  ./ "$SERVER_USER@$SERVER_IP:$REMOTE_DIR/"

## Build images one at a time, not in parallel — the production VPS has well under 1GB
## RAM, and `docker compose build` (or `up --build`) bakes all services concurrently by
## default, which previously drove the box into a multi-hour swap/CPU meltdown
## (2026-10-07 incident, see WIKI.md session log).
$SSH_CMD "$SERVER_USER@$SERVER_IP" \
  "cd $REMOTE_DIR && docker compose build backend && docker compose build frontend && docker compose up -d"

echo "Deployed. Checking https://fin.garaev.tech/api/metrics ..."
curl -s -o /dev/null -w "HTTP %{http_code}\n" https://fin.garaev.tech/api/metrics
