#!/bin/bash
# Waits for the dish->recipe pipeline to finish, then chains the
# recipe->LCA pipeline (match_ingredients.py + aggregate_lca.py).
# Launched detached via nohup+caffeinate; logs to lca/watcher.log.

LCA_DIR="$HOME/menu-item-impact/lca"
RUNLOG="$HOME/menu-item-impact/recipes/run.log"
RECIPES="$HOME/menu-item-impact/recipes/recipes.jsonl"
VENV="$HOME/menu-item-impact/.venv/bin/python"
LOG="$LCA_DIR/watcher.log"

cd "$LCA_DIR" || exit 1
echo "[watcher] armed $(date) — waiting for recipe pipeline" >> "$LOG"

# 1. Wait until no pipeline.py process remains.
while pgrep -f "pipeline.py --concurrency" >/dev/null; do
    sleep 30
done
echo "[watcher] pipeline process gone $(date)" >> "$LOG"

# 2. Let tee flush, then require a clean-completion marker.
sleep 5
if ! grep -q "DONE in" "$RUNLOG"; then
    echo "[watcher] ABORT: no 'DONE in' in run.log — pipeline likely crashed; LCA NOT run." >> "$LOG"
    exit 1
fi
echo "[watcher] pipeline completed cleanly $(date)" >> "$LOG"

# 3. Match ingredients -> EF table.
echo "[watcher] === match_ingredients START $(date) ===" >> "$LOG"
"$VENV" match_ingredients.py --recipes "$RECIPES" --out ingredient_ef_table.csv \
    --concurrency 30 >> "$LOG" 2>&1
MC=$?
echo "[watcher] match_ingredients exit=$MC $(date)" >> "$LOG"
if [ $MC -ne 0 ]; then
    echo "[watcher] ABORT: match_ingredients failed; aggregation skipped." >> "$LOG"
    exit 1
fi

# 4. Aggregate -> per-recipe LCA.
echo "[watcher] === aggregate_lca START $(date) ===" >> "$LOG"
"$VENV" aggregate_lca.py --recipes "$RECIPES" --out dish_lca.jsonl >> "$LOG" 2>&1
AC=$?
echo "[watcher] aggregate_lca exit=$AC $(date)" >> "$LOG"
echo "[watcher] === ALL DONE $(date) (output: lca/dish_lca.jsonl) ===" >> "$LOG"
