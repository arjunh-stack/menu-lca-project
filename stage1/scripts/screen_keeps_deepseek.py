"""Layer 25 stage 1c — DeepSeek V4 Pro re-screen of Gemini's KEEP verdicts.

Companion to screen_drops_deepseek.py. We already validated Gemini's DROPs;
this validates Gemini's KEEPs to catch over-keeping (Gemini said KEEP but Pro
disagrees → drop candidates we'd otherwise miss).

Inputs:  recipe_screen_gemini.csv (filter to verdict=KEEP)
Outputs: recipe_screen_deepseek_keeps.csv (resumeable)
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
import time
from pathlib import Path

import httpx

GEMINI    = dpath("recipe_screen_gemini.csv")
JUDGMENTS = dpath("recipe_screen_deepseek_keeps.csv")
ENV_FILE  = dpath(".env.openrouter")
ENDPOINT  = "https://openrouter.ai/api/v1/chat/completions"

MODEL       = "deepseek/deepseek-v4-pro"
BATCH_SIZE  = 20
CONCURRENCY = 100
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
            "X-Title": "menu-item-impact L25 deepseek-pro keeps",
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
    print(f"loaded {len(canonicals):,} Gemini-KEEP canonicals to re-screen")
    print(f"model: {MODEL}  batch_size: {BATCH_SIZE}  concurrency: {CONCURRENCY}")

    done = set()
    if os.path.exists(JUDGMENTS):
        with open(JUDGMENTS) as f:
            for row in csv.DictReader(f):
                done.add(int(row["cluster_id"]))
        print(f"  resume: {len(done):,} already judged")
        out_handle = open(JUDGMENTS, "a", newline="")
        writer = csv.writer(out_handle)
    else:
        out_handle = open(JUDGMENTS, "w", newline="")
        writer = csv.writer(out_handle)
        writer.writerow(["cluster_id", "canonical_name", "total_count", "verdict", "reason"])

    pending = [c for c in canonicals if c["cluster_id"] not in done]
    print(f"to process: {len(pending):,}")

    sem = asyncio.Semaphore(CONCURRENCY)
    n_done = n_keep = n_drop = n_err = 0
    t0 = time.time()
    last_print = t0
    write_lock = asyncio.Lock()

    batches = list(chunked(pending, BATCH_SIZE))

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
                    eta = (len(pending) - n_done) / rate if rate > 0 else 0
                    print(f"  {n_done:>6,}/{len(pending):,}  ({n_keep} pro_KEEP-confirmed, {n_drop} pro_DROP-flagged, {n_err} err)  "
                          f"rate={rate:.0f}/s  eta={eta:.0f}s", flush=True)
                    last_print = time.time()

        await asyncio.gather(*(run_one(b) for b in batches))

    out_handle.close()
    elapsed = time.time() - t0
    print(f"\nDONE in {elapsed:.0f}s")
    print(f"  pro_KEEP-confirmed (both said KEEP):              {n_keep:,}")
    print(f"  pro_DROP-flagged (Gemini said KEEP, Pro said DROP): {n_drop:,}")
    print(f"  err: {n_err:,}")

if __name__ == "__main__":
    asyncio.run(main())
