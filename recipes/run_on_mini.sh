#!/bin/bash
# Deploy and start the recipe pipeline on a remote Mac mini.
#
# Prereqs (one-time, on this Mac):
#   ~/.ssh/config has a Host entry named `mini` (or pass HOST=... to override)
#   `ssh mini echo ok` returns 0
#
# What this does:
#   1. rsync pipeline.py + structural_references.py + dish_context.csv + .env.openrouter
#      to mini:~/menu-item-impact/recipes/
#   2. ensure python3 + httpx on mini
#   3. start `tmux new -d -s recipes` running pipeline.py at concurrency 100
#   4. print instructions for attaching/monitoring/fetching results
#
# Re-run anytime — rsync is incremental, the tmux session is recreated only
# if it doesn't exist, and the pipeline itself is resumable (skips
# cluster_ids already in recipes.jsonl).
set -euo pipefail

HOST="${HOST:-mini}"
REMOTE_DIR="${REMOTE_DIR:-menu-item-impact/recipes}"
SESSION="${SESSION:-recipes}"
CONCURRENCY="${CONCURRENCY:-100}"

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"

echo "==> verifying ssh to $HOST"
ssh -o ConnectTimeout=8 -o BatchMode=yes "$HOST" "echo connected as \$(whoami) on \$(hostname); uname -srm" || {
  echo "ERROR: ssh $HOST failed. Set up ~/.ssh/config Host entry first." >&2
  exit 1
}

echo "==> ensuring remote dir $REMOTE_DIR"
ssh "$HOST" "mkdir -p ~/$REMOTE_DIR"

echo "==> rsyncing pipeline files"
rsync -av \
  "$HERE/pipeline.py" \
  "$HERE/structural_references.py" \
  "$HERE/dish_context.csv" \
  "$HOST:~/$REMOTE_DIR/"

# .env.openrouter sits at repo root locally; we put it next to the script
# on the remote and load_api_key() picks it up via ENV_FILE = ROOT/.env...
# Actually pipeline.py expects it at ../.env.openrouter relative to itself.
# Mirror the layout: put .env.openrouter at ~/menu-item-impact/.env.openrouter
echo "==> rsyncing .env.openrouter"
rsync -av "$ROOT/.env.openrouter" "$HOST:~/$(dirname "$REMOTE_DIR")/"

echo "==> ensuring venv + httpx on remote"
# Mini's /usr/bin/python3 is 3.9.6 (too old for our PEP 604 unions), and
# brew's python is PEP 668-locked. So we use a dedicated venv under
# ~/menu-item-impact/.venv with /opt/homebrew/bin/python3.13.
ssh "$HOST" bash <<'REMOTE'
set -e
VENV="$HOME/menu-item-impact/.venv"
if [ ! -x "$VENV/bin/python" ]; then
  echo "creating venv at $VENV with python3.13"
  /opt/homebrew/bin/python3.13 -m venv "$VENV"
  "$VENV/bin/pip" install --quiet --upgrade pip
fi
"$VENV/bin/pip" install --quiet httpx tqdm
"$VENV/bin/python" -c "import httpx, tqdm, sys; print(f'httpx {httpx.__version__}, tqdm {tqdm.__version__} on python {sys.version.split()[0]}')"
command -v tmux >/dev/null || { echo "ERROR: tmux not on remote — brew install tmux" >&2; exit 1; }
REMOTE

echo "==> launching pipeline in tmux session '$SESSION' on $HOST"
ssh "$HOST" bash <<REMOTE
set -e
if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "tmux session '$SESSION' already running on remote — attach with: ssh $HOST -t tmux attach -t $SESSION"
  exit 0
fi
cd ~/$REMOTE_DIR
tmux new -d -s "$SESSION" "\$HOME/menu-item-impact/.venv/bin/python pipeline.py --concurrency $CONCURRENCY 2>&1 | tee run.log"
sleep 1
tmux ls
REMOTE

cat <<EOF

============================================================
Recipe pipeline started on $HOST (tmux session: $SESSION)
============================================================

Watch live (mosh in, then attach):
  mosh $HOST
  tmux attach -t $SESSION        # ctrl-b d to detach
  # or just tail the log:
  tail -f ~/$REMOTE_DIR/run.log

Check progress from this Mac without SSHing:
  ssh $HOST 'wc -l ~/$REMOTE_DIR/recipes.jsonl 2>/dev/null; tail -3 ~/$REMOTE_DIR/run.log'

Fetch results when done:
  bash $HERE/fetch_from_mini.sh

If anything dies, just re-run this script — pipeline is resumable.
EOF
