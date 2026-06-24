#!/bin/bash
# Stage 5 precompute orchestrator — runs the whole dish→phylogeny build.
# Designed to run detached on the Mac mini (launched by deploy_to_mini.sh
# inside tmux + caffeinate). Resumable: each heavy stage is skipped if its
# output already exists, so a re-run after a crash picks up where it left
# off. The recipe→LCA inputs are expected to already be on the host.
#
# Emits "PHYLO DONE" on clean completion (watchers / fetch can grep it).
set -uo pipefail

PHYLO_DIR="${PHYLO_DIR:-$HOME/menu-item-impact/phylogeny}"
VENV="${VENV:-$HOME/menu-item-impact/.venv/bin/python}"
PC="$PHYLO_DIR/precompute"
DATA="$PHYLO_DIR/data"
MIN_COUNT="${MIN_COUNT:-2}"

cd "$PHYLO_DIR" || { echo "no $PHYLO_DIR" >&2; exit 1; }
mkdir -p "$DATA" "$PHYLO_DIR/frozen" "$PHYLO_DIR/logs" "$PHYLO_DIR/site/data"
echo "=== phylogeny precompute START $(date) ==="
echo "python: $($VENV --version 2>&1)  min-count: $MIN_COUNT"
t0=$(date +%s)

run_stage() {  # name  output-to-check  command...
  local name="$1" out="$2"; shift 2
  if [ -e "$out" ]; then
    echo "--- $name: SKIP (exists: $out) ---"
    return 0
  fi
  echo "--- $name: START $(date) ---"
  "$@"
  local rc=$?
  if [ $rc -ne 0 ]; then
    echo "!!! $name FAILED (exit $rc) — aborting" >&2
    exit $rc
  fi
  echo "--- $name: OK $(date) ---"
}

# 1. dish → semantic recipe vectors
run_stage "build_vectors" "$DATA/dish_vectors.npy" \
  "$VENV" "$PC/build_vectors.py" --min-count "$MIN_COUNT"

# 2. vectors → hierarchical tree + clade list
run_stage "build_tree" "$DATA/tree.json" \
  "$VENV" "$PC/build_tree.py"

# 3. vectors → 2D manifold layout
run_stage "build_umap" "$DATA/umap.json" \
  "$VENV" "$PC/build_umap.py"

# 3b. per-dish cuisine / protein / carb classes (needs menu_dishes.sqlite)
run_stage "classify_dishes" "$DATA/dish_classes.csv" \
  "$VENV" "$PC/classify_dishes.py"

# 4. clade labels (internally resumable — always invoked; no-ops if done)
echo "--- label_clades: START $(date) ---"
"$VENV" "$PC/label_clades.py" --concurrency 60 || {
  echo "!!! label_clades FAILED — aborting" >&2; exit 1; }
echo "--- label_clades: OK $(date) ---"

# 5. assemble the static site bundle (cheap — always re-run)
echo "--- export_site_data: START $(date) ---"
"$VENV" "$PC/export_site_data.py" || {
  echo "!!! export_site_data FAILED — aborting" >&2; exit 1; }
echo "--- export_site_data: OK $(date) ---"

echo "=== PHYLO DONE in $(( $(date +%s) - t0 ))s $(date) ==="
