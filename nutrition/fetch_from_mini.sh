#!/bin/bash
# Pull the nutrition-run outputs back from the Mac mini.
# Safe to re-run mid-run — rsync is incremental.
#
# Fetches:
#   ingredient_fdc_table.csv   the unique-ingredient -> FDC macro table
#   dish_macros.jsonl          per-recipe macros (the stage 2b output)
#   data/fdc_match_cache.json  the updated match cache (so a local re-run
#                              is also cache-warm)
#   run.log                    the tmux run log
set -euo pipefail

HOST="${HOST:-mini}"
REMOTE_DIR="${REMOTE_DIR:-menu-item-impact/nutrition}"
HERE="$(cd "$(dirname "$0")" && pwd)"

SESSION="${SESSION:-nutrition}"

echo "==> remote progress:"
# Prefer the live tmux pane (always current); fall back to run.log.
ssh "$HOST" "tmux capture-pane -t $SESSION -p 2>/dev/null | grep -v '^\$' | tail -5 \
             || tail -5 ~/$REMOTE_DIR/run.log 2>/dev/null || echo '(no progress yet)'; \
             wc -l ~/$REMOTE_DIR/dish_macros.jsonl 2>/dev/null || echo '(no dish_macros.jsonl yet)'"

echo "==> rsyncing outputs back to $HERE"
rsync -av \
  "$HOST:~/$REMOTE_DIR/ingredient_fdc_table.csv" \
  "$HOST:~/$REMOTE_DIR/dish_macros.jsonl" \
  "$HOST:~/$REMOTE_DIR/run.log" \
  "$HERE/" 2>/dev/null || true
rsync -av "$HOST:~/$REMOTE_DIR/data/fdc_match_cache.json" \
  "$HERE/data/" 2>/dev/null || true

echo "==> local:"
wc -l "$HERE/dish_macros.jsonl" 2>/dev/null || echo "(no local dish_macros.jsonl yet)"
