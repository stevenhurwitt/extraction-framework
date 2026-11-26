#!/bin/bash
# Incremental enwiki lake update. Runs as root (exFAT mount /mnt/lacie is root-owned).
set -euo pipefail
REPO=/home/steven/extraction-framework
LAKE=/mnt/lacie/wiki-data-2026/enwiki
exec >> "$LAKE/updates/update.log" 2>&1
echo "===== $(date -Is) run start ====="
"$REPO/.venv/bin/python" "$REPO/scripts/update_enwiki.py" \
  --data-dir "$LAKE/data" \
  --updates-dir "$LAKE/updates" \
  --state "$LAKE/.update_state.json"
echo "===== $(date -Is) run end ====="
