#!/usr/bin/env bash
# Daily faceless Short generator for @TheLearningCurveAI.
# Run via cron:  0 9 * * * /home/developer/proyectos/tlc/yt-clipper/run_daily.sh
# Logs go to:    /tmp/yt-clipper-daily.log
set -euo pipefail

PROJ=/home/developer/proyectos/tlc/yt-clipper
LOG=/tmp/yt-clipper-daily.log
exec >> "$LOG" 2>&1

echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="

cd "$PROJ"
export PATH="$HOME/.local/bin:$PATH"

# Pick a trending topic and produce + upload the Short (privacy=unlisted → schedule later)
python skills/yt-clipper/scripts/faceless.py --upload --privacy unlisted

echo "=== done ==="
