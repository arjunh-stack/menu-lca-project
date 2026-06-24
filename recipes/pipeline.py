"""Recipe pipeline — dish name → ingredients + grams.

For each canonical dish:
  - Read its pre-computed top raw name and cuisine bucket from dish_context.csv.
  - Send one OpenRouter call to DeepSeek v3 with a grams-first prompt
    anchored by a structural few-shot example chosen by cuisine bucket.
  - Parse JSON, normalize grams → proportions, append to JSONL output.

Output schema (one JSON object per line):
  {
    "cluster_id": int,
    "canonical_name": str,
    "top_raw_name": str,
    "cuisine_bucket": str,
    "total_count": int,
    "model": str,
    "ingredients": [{"ingredient": str, "grams": float, "proportion_pct": float}, ...]
  }

Resumable: skips any cluster_id already in the output file.

Usage:
  python3 pipeline.py                 # full run (all dishes in dish_context.csv)
  python3 pipeline.py --top 500       # validation slice (top N by total_count)
  python3 pipeline.py --top 500 --out recipes_validation.jsonl --concurrency 100
"""
import argparse
import asyncio
import csv
import json
import os
import re
import sys
import time
from pathlib import Path

import httpx
from tqdm import tqdm

from structural_references import get_structural_reference

ROOT = Path(__file__).resolve().parent.parent
CONTEXT_CSV = Path(__file__).resolve().parent / "dish_context.csv"
ENV_FILE = ROOT / ".env.openrouter"
ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"

MODEL = "deepseek/deepseek-chat-v3-0324"
DEFAULT_CONCURRENCY = 100
RETRIES = 3
# Granular httpx timeouts (connect/read/write/pool). A single blanket
# value lets a slow pool acquisition hide behind a long read budget.
HTTP_TIMEOUT = httpx.Timeout(connect=15.0, read=90.0, write=15.0, pool=30.0)
# Absolute per-dish ceiling enforced by asyncio.wait_for, set above a full
# RETRIES chain. A task that blows past this is cancelled and recorded as
# an error instead of wedging the run (resume re-tries it next pass).
HARD_TIMEOUT_S = 420.0


def load_api_key() -> str:
    # Prefer env var (Codespace secrets / CI), fall back to local .env file.
    env_key = os.environ.get("OPENROUTER_API_KEY")
    if env_key:
        return env_key.strip()
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            if line.startswith("OPENROUTER_API_KEY="):
                return line.split("=", 1)[1].strip()
    raise SystemExit(
        f"OPENROUTER_API_KEY not found in env var or {ENV_FILE}"
    )


def load_dish_context(path: Path) -> list[dict]:
    """Load dish_context.csv, skip rows missing a cluster_id."""
    rows = []
    with open(path) as f:
        for row in csv.DictReader(f):
            if not row.get("cluster_id"):
                continue
            rows.append({
                "cluster_id":     int(row["cluster_id"]),
                "canonical_name": row["canonical_name"],
                "top_raw_name":   row["top_raw_name"],
                "cuisine_bucket": row["cuisine_bucket"] or "default",
                "total_count":    int(row["total_count"] or 0),
            })
    return rows


def load_done_clusters(path: Path) -> set[int]:
    """Read existing JSONL to find which cluster_ids are already processed."""
    if not path.exists():
        return set()
    done = set()
    with open(path) as f:
        for line in f:
            try:
                obj = json.loads(line)
                done.add(int(obj["cluster_id"]))
            except (json.JSONDecodeError, KeyError, ValueError):
                continue
    return done


def build_ingredient_prompt(dish: dict) -> tuple[str, str]:
    """Returns (system_prompt, user_prompt). Ported from
    ../menu-project/ingredient_pipeline.py:build_ingredient_prompt."""
    structural_ref = get_structural_reference(dish["cuisine_bucket"])
    name_for_llm = dish["top_raw_name"] or dish["canonical_name"]

    system = (
        "You are a culinary expert and food scientist. You think in grams and weight. "
        "Always return raw JSON only, no markdown formatting, no extra text."
    )
    user = f"""Here are structural weight breakdowns of similar recipes to calibrate your sense of proportions. Ingredient names are replaced with categories — focus on the weight distribution pattern, not the specific ingredients.

{structural_ref}

Now estimate the specific ingredients and their weights for this menu item: "{name_for_llm}".

Estimate the weight in grams of each ingredient needed for a standard 4-serving recipe. Think carefully about real recipe quantities — a clove of garlic is about 5g, a medium onion is 150g, a chicken breast is 200g, etc.

Return ONLY a JSON object listing each ingredient and its estimated weight in grams:
{{"ingredients": [{{"ingredient": "chicken breast", "grams": 600}}, {{"ingredient": "salt", "grams": 5}}]}}"""
    return system, user


def parse_json_response(text: str) -> dict | None:
    """Strip markdown fences and parse JSON. Ported from menu-project."""
    if not text:
        return None
    cleaned = re.sub(r"^```(?:json)?\s*", "", text.strip())
    cleaned = re.sub(r"\s*```$", "", cleaned).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{[\s\S]*\}", cleaned)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            return None
    return None


def parse_ingredient_response(raw: str) -> list[dict] | None:
    """Normalize grams into proportions. Ported from menu-project."""
    parsed = parse_json_response(raw)
    if not parsed or "ingredients" not in parsed:
        return None
    ingredients = parsed["ingredients"]
    if not isinstance(ingredients, list):
        return None
    total_g = sum(max(float(i.get("grams", 0) or 0), 0) for i in ingredients)
    out = []
    for i in ingredients:
        g = max(float(i.get("grams", 0) or 0), 0)
        pct = round(100 * g / total_g, 2) if total_g > 0 else 0.0
        name = (i.get("ingredient") or "").strip()
        if not name:
            continue
        out.append({
            "ingredient": name,
            "grams": round(g, 1),
            "proportion_pct": pct,
        })
    return out or None


async def call_one(client: httpx.AsyncClient, key: str,
                   dish: dict, attempt: int = 0, parse_retry: bool = False) -> dict:
    """One API call → result dict ready to write.

    The caller (run_one) holds the concurrency semaphore for this call's
    whole lifetime, retries included. call_one must NOT acquire the
    semaphore itself: a recursive re-acquire on retry means every task
    holds a slot while awaiting another, and a wave of simultaneous
    retries deadlocks the whole pool.

    `parse_retry=True` bumps temperature to 0.3 to escape deterministic
    bad outputs (truncated/malformed JSON, empty `{}` responses).
    """
    system, user = build_ingredient_prompt(dish)
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
        "max_tokens": 2048,
        "temperature": 0.3 if parse_retry else 0,
    }
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/menu-item-impact",
        "X-Title": "menu-item-impact recipes",
    }
    try:
        r = await client.post(ENDPOINT, json=payload, headers=headers, timeout=HTTP_TIMEOUT)
        if r.status_code == 429:
            if attempt < RETRIES:
                await asyncio.sleep(2 ** attempt)
                return await call_one(client, key, dish, attempt + 1)
            return _error_record(dish, "RATE_LIMIT")
        if r.status_code >= 500:
            if attempt < RETRIES:
                await asyncio.sleep(2 ** attempt)
                return await call_one(client, key, dish, attempt + 1)
            return _error_record(dish, f"SERVER_{r.status_code}")
        if r.status_code != 200:
            return _error_record(dish, f"HTTP_{r.status_code}")
        data = r.json()
        text = data["choices"][0]["message"]["content"]
        ingredients = parse_ingredient_response(text)
        if ingredients is None:
            # One retry at slightly higher temperature to escape
            # deterministic bad output (empty {} or malformed JSON).
            if not parse_retry:
                return await call_one(client, key, dish, attempt, parse_retry=True)
            return _error_record(dish, "PARSE_ERROR", raw_response=text[:500])
        return _ok_record(dish, ingredients)
    except Exception as e:
        if attempt < RETRIES:
            await asyncio.sleep(2 ** attempt)
            return await call_one(client, key, dish, attempt + 1)
        return _error_record(dish, f"EXCEPTION_{type(e).__name__}")


def _ok_record(dish: dict, ingredients: list[dict]) -> dict:
    return {
        "cluster_id":     dish["cluster_id"],
        "canonical_name": dish["canonical_name"],
        "top_raw_name":   dish["top_raw_name"],
        "cuisine_bucket": dish["cuisine_bucket"],
        "total_count":    dish["total_count"],
        "model":          MODEL,
        "ingredients":    ingredients,
    }


def _error_record(dish: dict, error: str, raw_response: str | None = None) -> dict:
    rec = {
        "cluster_id":     dish["cluster_id"],
        "canonical_name": dish["canonical_name"],
        "top_raw_name":   dish["top_raw_name"],
        "cuisine_bucket": dish["cuisine_bucket"],
        "total_count":    dish["total_count"],
        "model":          MODEL,
        "error":          error,
    }
    if raw_response is not None:
        rec["raw_response"] = raw_response
    return rec


async def run(args):
    key = load_api_key()
    print(f"loading {CONTEXT_CSV.name}...")
    dishes = load_dish_context(CONTEXT_CSV)
    print(f"  {len(dishes):,} dishes with cluster_id")

    # Sort by total_count desc so the validation slice is the highest-impact dishes
    dishes.sort(key=lambda d: -d["total_count"])

    if args.top:
        dishes = dishes[: args.top]
        print(f"  --top {args.top}: limiting to top {len(dishes):,} by total_count")

    out_path = Path(args.out)
    done = load_done_clusters(out_path)
    if done:
        print(f"  resume: {len(done):,} cluster_ids already in {out_path.name}")
    pending = [d for d in dishes if d["cluster_id"] not in done]
    print(f"to process: {len(pending):,}")
    if not pending:
        print("nothing to do.")
        return

    print(f"model: {MODEL}  concurrency: {args.concurrency}")

    sem = asyncio.Semaphore(args.concurrency)
    write_lock = asyncio.Lock()
    out_handle = open(out_path, "a")

    n_ok = n_err = 0
    t0 = time.time()
    # mininterval/maxinterval keep the bar updating smoothly through `tee`
    # in the tmux pane; smoothing=0.1 makes rate/ETA respond to recent
    # throughput rather than averaging over the whole run.
    bar = tqdm(total=len(pending), unit="dish", smoothing=0.1,
               mininterval=0.5, maxinterval=2.0, dynamic_ncols=True)

    # max_keepalive_connections=0 → every request gets a fresh connection
    # that is fully closed after, so a connection the remote drops can't
    # be stranded in the pool (the CLOSE_WAIT socket seen in the v18 run).
    limits = httpx.Limits(max_connections=args.concurrency,
                          max_keepalive_connections=0)
    async with httpx.AsyncClient(http2=False, limits=limits,
                                 timeout=HTTP_TIMEOUT) as client:
        async def run_one(dish):
            nonlocal n_ok, n_err
            # Acquire the concurrency slot ONCE here and hold it across the
            # whole call + retries; wrap the work in a hard wall-clock
            # ceiling so a wedged request becomes a HARD_TIMEOUT error
            # rather than stalling the run.
            async with sem:
                try:
                    rec = await asyncio.wait_for(
                        call_one(client, key, dish), timeout=HARD_TIMEOUT_S)
                except asyncio.TimeoutError:
                    rec = _error_record(dish, "HARD_TIMEOUT")
            async with write_lock:
                out_handle.write(json.dumps(rec) + "\n")
                if "error" in rec:
                    n_err += 1
                else:
                    n_ok += 1
                bar.update(1)
                bar.set_postfix(ok=n_ok, err=n_err, refresh=False)
                if (n_ok + n_err) % 25 == 0:
                    out_handle.flush()

        await asyncio.gather(*(run_one(d) for d in pending))

    bar.close()
    out_handle.flush()
    out_handle.close()
    elapsed = time.time() - t0
    print(f"\nDONE in {elapsed:.0f}s")
    print(f"  ok:  {n_ok:,}")
    print(f"  err: {n_err:,}")
    print(f"  output: {out_path}")


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--top", type=int, default=None,
                   help="Limit to top N dishes by total_count (for validation slices)")
    p.add_argument("--out", type=str, default=str(Path(__file__).resolve().parent / "recipes.jsonl"),
                   help="Output JSONL path (resumable). Default: recipes/recipes.jsonl")
    p.add_argument("--concurrency", type=int, default=DEFAULT_CONCURRENCY,
                   help=f"Max concurrent OpenRouter calls (default: {DEFAULT_CONCURRENCY})")
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if not os.environ.get("OPENROUTER_API_KEY") and not ENV_FILE.exists():
        print(
            f"ERROR: set OPENROUTER_API_KEY env var or create {ENV_FILE}",
            file=sys.stderr,
        )
        sys.exit(1)
    asyncio.run(run(args))
