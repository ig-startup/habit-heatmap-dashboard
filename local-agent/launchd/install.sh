#!/bin/bash
# Registers the habit-heatmap local agent as a launchd job (every 30 min + on network change).
set -euo pipefail

AGENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${HABIT_AGENT_VENV:-$HOME/.venvs/habit-heatmap-agent}"  # outside Yandex.Disk sync
PLIST_NAME="com.igfinance.habit-heatmap-agent.plist"
DEST="$HOME/Library/LaunchAgents/$PLIST_NAME"

mkdir -p "$AGENT_DIR/logs"

sed \
  -e "s|__VENV_PYTHON__|$VENV_DIR/bin/python3|g" \
  -e "s|__AGENT_DIR__|$AGENT_DIR|g" \
  "$AGENT_DIR/launchd/$PLIST_NAME" > "$DEST"

launchctl unload "$DEST" 2>/dev/null || true
launchctl load "$DEST"

echo "Installed and loaded $DEST"
echo "Logs: $AGENT_DIR/logs/agent.log"
echo "Runs every 30 min, on network change and once now. To stop: launchctl unload $DEST"
