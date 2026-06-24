"""Cleanup pass for the ~60 items missed by sharded Pro KEEP-screen.

Reads recipe_screen_deepseek_keeps_missing.csv, screens with DeepSeek Pro,
appends to recipe_screen_deepseek_keeps.csv.
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
import re
import time
from pathlib import Path

import httpx

MISSING   = dpath("recipe_screen_deepseek_keeps_missing.csv")
MAIN      = dpath("recipe_screen_deepseek_keeps.csv")
ENV_FILE  = dpath(".env.openrouter")
ENDPOINT  = "https://openrouter.ai/api/v1/chat/completions"

MODEL       = "deepseek/deepseek-v4-pro"
BATCH_SIZE  = 5     # smaller to avoid the hang condition
CONCURRENCY = 8
RETRIES     = 5
TIMEOUT_S   = 60.0

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
    "  - Iconic branded item with widely available copycat recipes online.\n"
    "  - Has clear protein/ingredient + style/cuisine/preparation markers.\n\n"
    "DROP if:\n"
    "  - Proper-noun possessive that's clearly a person, not a chain.\n"
    "  - Vague modifier with no dish identity: 'chef special', 'house special'.\n"
    "  - Single generic word with no qualifier: bare 'chicken', 'pizza', 'salad'.\n"
    "  - Alphabetized gibberish or unrecognizable fragments.\n"
    "  - Menu code, add-on, or instruction.\n\n"
    "Reply EXACTLY one line per item, no preamble:\n"
    "N. KEEP <one-word reason>\n"
    "N. DROP <one-word reason>\n"
)

def load_api_key() -> str:
    for line in Path(ENV_FILE).read_text().splitlines():
        if line.startswith("OPENROUTER_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("OPENROUTER_API_KEY not found")

def load_missing():
    rows = []
    with open(MISSING) as f:
        for row in csv.DictReader(f):
            rows.append({
                "cluster_id":     int(row["cluster_id"]),
                "canonical_name": row["canonical_name"],
                "total_count":    int(row["total_count"]),
            })
    return rows

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
            "X-Title": "menu-item-impact L25 deepseek-pro keeps cleanup",
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
            print(f"  giving up on batch: {[p['canonical_name'] for p in batch]}: {type(e).__name__}")
            return [("API_ERROR", f"{type(e).__name__}")] * len(batch)

async def main():
    key = load_api_key()
    missing = load_missing()
    print(f"cleanup: {len(missing):,} items")

    out_handle = open(MAIN, "a", newline="")
    writer = csv.writer(out_handle)
    write_lock = asyncio.Lock()
    sem = asyncio.Semaphore(CONCURRENCY)

    n_done = 0
    t0 = time.time()

    async with httpx.AsyncClient() as client:
        async def run_one(batch):
            nonlocal n_done
            res = await judge_batch(client, batch, sem, key)
            async with write_lock:
                for p, (verdict, reason) in zip(batch, res):
                    writer.writerow([
                        p["cluster_id"], p["canonical_name"], p["total_count"],
                        verdict, reason,
                    ])
                    n_done += 1
                out_handle.flush()

        batches = list(chunked(missing, BATCH_SIZE))
        await asyncio.gather(*(run_one(b) for b in batches))

    out_handle.close()
    print(f"DONE: {n_done}/{len(missing)} in {time.time()-t0:.0f}s")

if __name__ == "__main__":
    asyncio.run(main())
