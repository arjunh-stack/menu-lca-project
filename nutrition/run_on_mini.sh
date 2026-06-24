#!/bin/bash
# Deploy and start the FULL nutrition run (75,325 recipes) on a remote
# Mac mini. Mirrors recipes/run_on_mini.sh.
#
# Prereqs (one-time, on this Mac):
#   ~/.ssh/config has a Host entry named `mini` (or pass HOST=... to override)
#   `ssh mini echo ok` returns 0
#
# What this does:
#   1. rsync the nutrition scripts + the PRE-BUILT data artifacts
#      (fdc_macro_table.csv, fdc_descriptions.csv, embeddings/*.npy,
#      fdc_match_cache.json) to mini:~/menu-item-impact/nutrition/.
#      The raw FDC source CSVs are NOT shipped — port_fdc_data.py and
#      precompute_fdc_embeddings.py already ran locally; the mini only
#      needs to match + aggregate.
#   2. rsync recipes/recipes.jsonl (the 75,325-recipe input) + .env.openrouter.
#   3. ensure the shared venv has numpy + pandas + sentence-transformers
#      + httpx (one-time; sentence-transformers pulls torch — a few min).
#   4. start `tmux new -d -s nutrition` running, chained:
#         match_ingredients.py --recipes ../recipes/recipes.jsonl
#         && aggregate_macros.py --recipes ../recipes/recipes.jsonl
#   5. print attach / monitor / fetch instructions.
#
# match_ingredients.py de-duplicates: the 75,325 recipes collapse to their
# unique ingredient-string set, and each unique string is matched exactly
# once — recipes that share an ingredient never re-query it.
#
# Re-run anytime — rsync is incremental, the tmux session is recreated only
# if absent, and the match step is resumable (the match cache is flushed
# every 250 ingredients, so a re-run skips everything already matched).
set -euo pipefail

HOST="${HOST:-mini}"
REMOTE_ROOT="${REMOTE_ROOT:-menu-item-impact}"
REMOTE_DIR="$REMOTE_ROOT/nutrition"
SESSION="${SESSION:-nutrition}"
CONCURRENCY="${CONCURRENCY:-10}"

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"

echo "==> verifying ssh to $HOST"
ssh -o ConnectTimeout=8 -o BatchMode=yes "$HOST" \
  "echo connected as \$(whoami) on \$(hostname); uname -srm" || {
  echo "ERROR: ssh $HOST failed. Set up ~/.ssh/config Host entry first." >&2
  exit 1
}

echo "==> ensuring remote dirs"
ssh "$HOST" "mkdir -p ~/$REMOTE_DIR/data/embeddings"

echo "==> rsyncing nutrition scripts"
rsync -av \
  "$HERE/port_fdc_data.py" \
  "$HERE/precompute_fdc_embeddings.py" \
  "$HERE/fdc_matcher.py" \
  "$HERE/match_ingredients.py" \
  "$HERE/aggregate_macros.py" \
  "$HERE/PLAN.md" \
  "$HOST:~/$REMOTE_DIR/"

echo "==> rsyncing pre-built FDC data artifacts (no raw source CSVs)"
rsync -av \
  "$HERE/data/fdc_macro_table.csv" \
  "$HERE/data/fdc_descriptions.csv" \
  "$HERE/data/fdc_match_cache.json" \
  "$HOST:~/$REMOTE_DIR/data/"
rsync -av "$HERE/data/embeddings/" "$HOST:~/$REMOTE_DIR/data/embeddings/"

echo "==> rsyncing recipes.jsonl (75,325-recipe input) + .env.openrouter"
rsync -av "$ROOT/recipes/recipes.jsonl" "$HOST:~/$REMOTE_ROOT/recipes/"
rsync -av "$ROOT/.env.openrouter" "$HOST:~/$REMOTE_ROOT/"

echo "==> ensuring venv deps on remote"
# Shared venv at ~/menu-item-impact/.venv (python3.13), created by the
# recipes-stage deploy. Add the nutrition matcher's deps.
ssh "$HOST" bash <<'REMOTE'
set -e
VENV="$HOME/menu-item-impact/.venv"
if [ ! -x "$VENV/bin/python" ]; then
  echo "creating venv at $VENV with python3.13"
  /opt/homebrew/bin/python3.13 -m venv "$VENV"
  "$VENV/bin/pip" install --quiet --upgrade pip
fi
echo "installing numpy pandas sentence-transformers httpx tqdm (may take a few min)..."
"$VENV/bin/pip" install --quiet numpy pandas sentence-transformers httpx tqdm
"$VENV/bin/python" - <<'PY'
import sys, numpy, pandas, httpx, sentence_transformers
print(f"deps OK on python {sys.version.split()[0]}: "
      f"numpy {numpy.__version__}, pandas {pandas.__version__}, "
      f"sentence-transformers {sentence_transformers.__version__}")
PY
command -v tmux >/dev/null || { echo "ERROR: tmux not on remote — brew install tmux" >&2; exit 1; }
REMOTE

echo "==> launching nutrition run in tmux session '$SESSION' on $HOST"
ssh "$HOST" bash <<REMOTE
set -e
if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "tmux session '$SESSION' already running — attach with: ssh $HOST -t tmux attach -t $SESSION"
  exit 0
fi
cd ~/$REMOTE_DIR
PY="\$HOME/menu-item-impact/.venv/bin/python"
RECIPES="\$HOME/menu-item-impact/recipes/recipes.jsonl"
# The whole pipeline is grouped with { ...; } so 2>&1 | tee captures
# every stage's output into run.log, not just the trailing line.
tmux new -d -s "$SESSION" "{ \
  echo '=== match_ingredients START '\$(date)' ==='; \
  \$PY match_ingredients.py --recipes \$RECIPES --out ingredient_fdc_table.csv --concurrency $CONCURRENCY \
  && echo '=== aggregate_macros START '\$(date)' ===' \
  && \$PY aggregate_macros.py --recipes \$RECIPES --table ingredient_fdc_table.csv --out dish_macros.jsonl \
  && echo '=== ALL DONE '\$(date)' ==='; \
  echo \"EXIT CODE: \\\$?\"; \
} 2>&1 | tee run.log"
sleep 1
tmux ls
REMOTE

cat <<EOF

============================================================
Nutrition run started on $HOST (tmux session: $SESSION)
============================================================

Watch live (mosh in, then attach):
  mosh $HOST
  tmux attach -t $SESSION        # ctrl-b d to detach
  # or just tail the log:
  tail -f ~/$REMOTE_DIR/run.log

Check progress from this Mac without SSHing:
  ssh $HOST 'tail -3 ~/$REMOTE_DIR/run.log; wc -l ~/$REMOTE_DIR/dish_macros.jsonl 2>/dev/null'

Fetch results when done:
  bash $HERE/fetch_from_mini.sh

If anything dies, just re-run this script — the match step is resumable
(cache flushed every 250 ingredients).
EOF
