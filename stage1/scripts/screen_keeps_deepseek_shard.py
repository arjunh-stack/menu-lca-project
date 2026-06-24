"""Sharded version of screen_keeps_deepseek.py — run 4+ copies in parallel.

usage: python3 screen_keeps_deepseek_shard.py <shard_id> <total_shards>

Reads the existing recipe_screen_deepseek_keeps.csv to skip already-done items,
then processes only items whose index % total_shards == shard_id. Writes to a
per-shard CSV so parallel processes don't collide.

Outputs: recipe_screen_deepseek_keeps_shard{shard_id}.csv (resumeable per shard)

After all shards finish, merge into recipe_screen_deepseek_keeps.csv.
"""

# --- repo-root path bootstrap (added by 2026-05 reorg) ---
import os as _os, sys as _sys
_d = _os.path.dirname(_os.path.abspath(__file__))
while _d != _os.path.dirname(_d) and not _os.path.exists(_os.path.join(_d, "paths.py")):
    _d = _os.path.dirname(_d)
if _d not in _sys.path:
    _sys.path.insert(0, _d)
from paths import dpath  # noqa: E402
# --- end bootstrap ---

import asyncio
import csv
import os
import re
import sys
import time
from pathlib import Path

import httpx

if len(sys.argv) != 3:
    raise SystemExit("usage: python3 screen_keeps_deepseek_shard.py <shard_id> <total_shards>")
SHARD_ID = int(sys.argv[1])
TOTAL_SHARDS = int(sys.argv[2])
assert 0 <= SHARD_ID < TOTAL_SHARDS

GEMINI       = dpath("recipe_screen_gemini.csv")
MAIN_OUTPUT  = dpath("recipe_screen_deepseek_keeps.csv")
JUDGMENTS    = dpath(f"recipe_screen_deepseek_keeps_shard{SHARD_ID}.csv")
ENV_FILE     = dpath(".env.openrouter")
ENDPOINT     = "https://openrouter.ai/api/v1/chat/completions"

MODEL       = "deepseek/deepseek-v4-pro"
BATCH_SIZE  = 20
CONCURRENCY = 50
RETRIES     = 3
TIMEOUT_S   = 180.0

SYSTEM_PROMPT = (
    "You are a food expert classifying menu item names. For each name, decide "
    "whether it represents a REAL, SEARCHABLE DISH that someone could Google "
    "and find a repeatable recipe for.\n\n"
    "Names are token-sorted alphabetically — mentally rearrange to native "
    "phrasing before judging. Each line shows the dish's `count` (how many "
    "menus it appears on); high count is suggestive but the name itself must "
    "still pass the recipe-search test.\n\n"
    "KEEP if:\n"
    "  - Recognizable dish from any cuisine. KEEP regional/ethnic names you "
    "don't personally recognize (mofongo, pongal, lau lau, kitfo, banh xeo, "
    "jollof, doro wat). International ethnic names KEEP by default.\n"
    "  - Iconic branded item with widely available copycat recipes online: "
    "whopper, big mac, crunchwrap supreme, bloomin onion, baconator, mcrib.\n"
    "  - Has clear protein/ingredient + style/cuisine/preparation markers.\n\n"
    "DROP if:\n"
    "  - Proper-noun possessive that's clearly a person, not a chain: "
    "'joe favorite chicken'. (But 'papa john pizza' → KEEP, real chain.)\n"
    "  - Vague modifier with no dish identity: 'chef special', 'house special'.\n"
    "  - Single generic word with no qualifier: bare 'chicken', 'pizza', 'salad'.\n"
    "  - Alphabetized gibberish or unrecognizable fragments.\n"
    "  - Menu code: 'b3', 'c95'.\n"
    "  - Add-on or instruction: 'add cheese', 'extra sauce'.\n\n"
    "Reply EXACTLY one line per item, no preamble:\n"
    "N. KEEP <one-word reason>\n"
    "N. DROP <one-word reason>\n"
)

def load_api_key() -> str:
    for line in Path(ENV_FILE).read_text().splitlines():
        if line.startswith("OPENROUTER_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("OPENROUTER_API_KEY not found")

def load_keep_set():
    rows = []
    with open(GEMINI) as f:
        for row in csv.DictReader(f):
            if row["verdict"] == "KEEP":
                rows.append({
                    "cluster_id":     int(row["cluster_id"]),
                    "canonical_name": row["canonical_name"],
                    "total_count":    int(row["total_count"]),
                })
    return rows

def load_done_cluster_ids():
    """Union of cluster_ids already in main CSV and all shard CSVs."""
    done = set()
    for p in [MAIN_OUTPUT] + [
        dpath(f"recipe_screen_deepseek_keeps_shard{i}.csv")
        for i in range(TOTAL_SHARDS)
    ]:
        if os.path.exists(p):
            with open(p) as f:
                for row in csv.DictReader(f):
                    done.add(int(row["cluster_id"]))
    return done

def chunked(it, size):
    buf = []
    for x in it:
        buf.append(x)
        if len(buf) == size:
            yield buf; buf = []
    if buf:
        yield buf

def build_user_prompt(batch):
    return "\n".join(
        f'{i}. "{p["canonical_name"]}" (count={p["total_count"]})'
        for i, p in enumerate(batch, start=1)
    )

LINE_RE = re.compile(r"^\s*(\d+)[\.\):]?\s*(KEEP|DROP)\b[\s,:\-—]*([^\s].*?)?$", re.I)

def parse_response(text, n):
    results = [None] * n
    for line in text.splitlines():
        m = LINE_RE.match(line)
        if not m: continue
        idx = int(m.group(1)) - 1
        if 0 <= idx < n:
            verdict = m.group(2).upper()
            reason = (m.group(3) or "").strip().lower().split()[0] if m.group(3) else ""
            results[idx] = (verdict, reason)
    for i, r in enumerate(results):
        if r is None:
            results[i] = ("PARSE_ERROR", "no_parse")
    return results

async def judge_batch(client, batch, sem, key, attempt=0):
    async with sem:
        payload = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": build_user_prompt(batch)},
            ],
            "temperature": 0,
        }
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/menu-item-impact",
            "X-Title": f"menu-item-impact L25 deepseek-pro keeps shard{SHARD_ID}",
        }
        try:
            r = await client.post(ENDPOINT, json=payload, headers=headers, timeout=TIMEOUT_S)
            if r.status_code == 429:
                if attempt < RETRIES:
                    await asyncio.sleep(2 ** attempt)
                    return await judge_batch(client, batch, sem, key, attempt + 1)
                raise RuntimeError("rate limit")
            r.raise_for_status()
            data = r.json()
            text = data["choices"][0]["message"]["content"]
            return parse_response(text, len(batch))
        except Exception as e:
            if attempt < RETRIES:
                await asyncio.sleep(2 ** attempt)
                return await judge_batch(client, batch, sem, key, attempt + 1)
            return [("API_ERROR", f"{type(e).__name__}")] * len(batch)

async def main():
    key = load_api_key()
    canonicals = load_keep_set()
    done = load_done_cluster_ids()

    # Assign each pending item to a shard by index in the pending list
    pending_all = [c for c in canonicals if c["cluster_id"] not in done]
    my_pending = [c for i, c in enumerate(pending_all) if i % TOTAL_SHARDS == SHARD_ID]
    print(f"[shard {SHARD_ID}/{TOTAL_SHARDS}] keep-set: {len(canonicals):,}  done: {len(done):,}  "
          f"pending-all: {len(pending_all):,}  my-pending: {len(my_pending):,}")

    if os.path.exists(JUDGMENTS):
        my_done = set()
        with open(JUDGMENTS) as f:
            for row in csv.DictReader(f):
                my_done.add(int(row["cluster_id"]))
        my_pending = [c for c in my_pending if c["cluster_id"] not in my_done]
        print(f"[shard {SHARD_ID}] resume: {len(my_done):,} already in shard file  after-filter: {len(my_pending):,}")
        out_handle = open(JUDGMENTS, "a", newline="")
        writer = csv.writer(out_handle)
    else:
        out_handle = open(JUDGMENTS, "w", newline="")
        writer = csv.writer(out_handle)
        writer.writerow(["cluster_id", "canonical_name", "total_count", "verdict", "reason"])

    sem = asyncio.Semaphore(CONCURRENCY)
    n_done = n_keep = n_drop = n_err = 0
    t0 = time.time()
    last_print = t0
    write_lock = asyncio.Lock()

    batches = list(chunked(my_pending, BATCH_SIZE))

    async with httpx.AsyncClient() as client:
        async def run_one(batch):
            nonlocal n_done, n_keep, n_drop, n_err, last_print
            res = await judge_batch(client, batch, sem, key)
            async with write_lock:
                for p, (verdict, reason) in zip(batch, res):
                    writer.writerow([
                        p["cluster_id"], p["canonical_name"], p["total_count"],
                        verdict, reason,
                    ])
                    n_done += 1
                    if verdict == "KEEP": n_keep += 1
                    elif verdict == "DROP": n_drop += 1
                    else: n_err += 1
                out_handle.flush()
                if time.time() - last_print > 10:
                    elapsed = time.time() - t0
                    rate = n_done / elapsed if elapsed > 0 else 0
                    eta = (len(my_pending) - n_done) / rate if rate > 0 else 0
                    print(f"[shard {SHARD_ID}] {n_done:>6,}/{len(my_pending):,}  "
                          f"(K={n_keep} D={n_drop} err={n_err})  rate={rate:.0f}/s  eta={eta:.0f}s", flush=True)
                    last_print = time.time()

        await asyncio.gather(*(run_one(b) for b in batches))

    out_handle.close()
    elapsed = time.time() - t0
    print(f"[shard {SHARD_ID}] DONE in {elapsed:.0f}s  K={n_keep} D={n_drop} err={n_err}")

if __name__ == "__main__":
    asyncio.run(main())
