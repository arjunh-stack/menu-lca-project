#!/bin/bash
# Pull the recipes.jsonl + run.log back from the Mac mini.
# Safe to re-run mid-run — rsync is incremental.
set -euo pipefail

HOST="${HOST:-mini}"
REMOTE_DIR="${REMOTE_DIR:-menu-item-impact/recipes}"
HERE="$(cd "$(dirname "$0")" && pwd)"

echo "==> remote progress:"
ssh "$HOST" "wc -l ~/$REMOTE_DIR/recipes.jsonl 2>/dev/null || echo '(no recipes.jsonl yet)'; tail -3 ~/$REMOTE_DIR/run.log 2>/dev/null || true"

echo "==> rsyncing back to $HERE"
rsync -av \
  "$HOST:~/$REMOTE_DIR/recipes.jsonl" \
  "$HOST:~/$REMOTE_DIR/run.log" \
  "$HERE/" 2>/dev/null || true

echo "==> local:"
wc -l "$HERE/recipes.jsonl" 2>/dev/null || echo "(no local copy yet)"
