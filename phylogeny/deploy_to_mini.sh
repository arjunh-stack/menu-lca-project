#!/bin/bash
# Deploy + launch the Stage 5 phylogeny precompute on the Mac mini.
#
# The mini already holds the recipe→LCA inputs (recipes.jsonl,
# dish_lca.jsonl, ingredient_ef_table.csv) from the earlier runs, so this
# only ships the precompute scripts, tops up the venv, and starts the
# orchestrator detached under tmux + caffeinate.
#
# Re-run anytime — rsync is incremental, the run is resumable, and the
# tmux session is only created if absent.
set -euo pipefail

HOST="${HOST:-mini}"
REMOTE="${REMOTE:-menu-item-impact/phylogeny}"
SESSION="${SESSION:-phylo}"
MIN_COUNT="${MIN_COUNT:-2}"
HERE="$(cd "$(dirname "$0")" && pwd)"

echo "==> verifying ssh to $HOST"
ssh -o ConnectTimeout=8 -o BatchMode=yes "$HOST" \
  "echo connected as \$(whoami) on \$(hostname)" || {
  echo "ERROR: ssh $HOST failed." >&2; exit 1; }

echo "==> rsyncing precompute scripts + orchestrator"
ssh "$HOST" "mkdir -p ~/$REMOTE/precompute ~/$REMOTE/logs"
rsync -av "$HERE/precompute/"*.py "$HOST:~/$REMOTE/precompute/"
rsync -av "$HERE/run_phylo.sh"    "$HOST:~/$REMOTE/"

echo "==> ensuring venv deps (umap-learn; rest already present)"
ssh "$HOST" bash <<'REMOTE'
set -e
PY="$HOME/menu-item-impact/.venv/bin/python"
"$HOME/menu-item-impact/.venv/bin/pip" install --quiet umap-learn || \
  echo "WARN: umap-learn install failed — build_umap.py will fall back to t-SNE"
echo "-- import check --"
"$PY" - <<'PYEOF'
import importlib, sys
need = ["numpy", "scipy", "sklearn", "sentence_transformers", "httpx"]
for m in need:
    importlib.import_module(m)
    print(f"  ok: {m}")
try:
    import umap  # noqa: F401
    print("  ok: umap  (UMAP layout)")
except Exception as e:
    print(f"  NOTE: umap unavailable ({type(e).__name__}) -> t-SNE fallback")
print("import check passed")
PYEOF
REMOTE

echo "==> launching '$SESSION' in tmux on $HOST (min-count $MIN_COUNT)"
ssh "$HOST" bash <<REMOTE
set -e
if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "tmux session '$SESSION' already running — attach: ssh $HOST -t tmux attach -t $SESSION"
  exit 0
fi
cd ~/$REMOTE
tmux new -d -s "$SESSION" \
  "MIN_COUNT=$MIN_COUNT caffeinate -i bash run_phylo.sh 2>&1 | tee logs/run.log"
sleep 1
tmux ls
REMOTE

cat <<EOF

============================================================
Phylogeny precompute launched on $HOST (tmux: $SESSION)
============================================================
Watch live:
  ssh $HOST -t tmux attach -t $SESSION      # ctrl-b d to detach
Check progress without attaching:
  ssh $HOST 'tail -5 ~/$REMOTE/logs/run.log'
Fetch results when "PHYLO DONE" appears:
  bash $HERE/fetch_from_mini.sh

The run is resumable — re-run this script if anything dies.
EOF
