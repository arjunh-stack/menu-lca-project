#!/bin/bash
# Pull the phylogeny precompute results back from the Mac mini.
# Safe to re-run mid-run — rsync is incremental.
set -euo pipefail

HOST="${HOST:-mini}"
REMOTE="${REMOTE:-menu-item-impact/phylogeny}"
HERE="$(cd "$(dirname "$0")" && pwd)"

echo "==> remote status:"
ssh "$HOST" "tail -6 ~/$REMOTE/logs/run.log 2>/dev/null || echo '(no run.log yet)'"

echo "==> rsyncing data/, frozen/, site/data/, logs/ back to $HERE"
mkdir -p "$HERE/data" "$HERE/frozen" "$HERE/site/data" "$HERE/logs"
rsync -av "$HOST:~/$REMOTE/data/"      "$HERE/data/"
rsync -av "$HOST:~/$REMOTE/frozen/"    "$HERE/frozen/"
rsync -av "$HOST:~/$REMOTE/site/data/" "$HERE/site/data/"
rsync -av "$HOST:~/$REMOTE/logs/"      "$HERE/logs/"

echo "==> local site bundle:"
if [ -f "$HERE/site/data/manifest.json" ]; then
  cat "$HERE/site/data/manifest.json"
  echo
  echo "Launch the tool (a local server is needed — file:// can't load"
  echo "the JSON shards):"
  echo "  cd $HERE/site && python3 -m http.server 8000"
  echo "  then open  http://localhost:8000"
else
  echo "(no manifest.json yet — run not finished)"
fi
