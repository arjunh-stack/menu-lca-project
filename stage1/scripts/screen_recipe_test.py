"""Layer 25 — recipe-test screen via two independent LLMs.

Asks each canonical: "could a chef Google this exact name and find a real,
repeatable recipe?" KEEP/DROP binary classification.

Run twice — once with Gemini Flash, once with DeepSeek V4 Flash. Then
`compare_recipe_screens.py` joins the verdicts and surfaces disagreements.

Usage:
    python screen_recipe_test.py gemini
    python screen_recipe_test.py deepseek

Inputs:  dish_canonical_summary_v18.csv
Outputs: recipe_screen_<model>.csv (resumeable)
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

if len(sys.argv) < 2 or sys.argv[1] not in ("gemini", "deepseek"):
    raise SystemExit("usage: python screen_recipe_test.py {gemini|deepseek}")

MODEL_KEY = sys.argv[1]
MODELS = {
    "gemini":   "google/gemini-2.0-flash-001",
    "deepseek": "deepseek/deepseek-v4-pro",
}
MODEL = MODELS[MODEL_KEY]

SUMM       = dpath("dish_canonical_summary_v18.csv")
JUDGMENTS  = dpath(f"recipe_screen_{MODEL_KEY}.csv")
ENV_FILE   = dpath(".env.openrouter")
ENDPOINT   = "https://openrouter.ai/api/v1/chat/completions"

BATCH_SIZE  = 20
CONCURRENCY = 50
RETRIES     = 3
TIMEOUT_S   = 90.0

SYSTEM_PROMPT = (
    "You are a food expert classifying menu item names. For each name, decide "
    "whether it represents a REAL, SEARCHABLE DISH that someone could Google "
    "and find a repeatable recipe for.\n\n"
    "Names are token-sorted alphabetically — mentally rearrange to native "
    "phrasing before judging. Each line also shows the dish's `count` (how many "
    "menus it appears on); high count is suggestive but the name itself must "
    "still pass the recipe-search test.\n\n"
    "KEEP if:\n"
    "  - Recognizable dish from any cuisine — American, Mexican, Italian, "
    "Chinese, Indian, Thai, Japanese, Korean, Vietnamese, Filipino, Ethiopian, "
    "Caribbean, Eastern European, Middle Eastern, etc. KEEP regional/ethnic "
    "names you don't personally recognize (mofongo, pongal, lau lau, kitfo, "
    "banh xeo, jollof, doro wat). International ethnic names KEEP by default.\n"
    "  - Iconic branded item with widely available copycat recipes online: "
    "whopper, big mac, crunchwrap supreme, bloomin onion, baconator, "
    "junior whopper, mcrib. KEEP.\n"
    "  - Has clear protein/ingredient + style/cuisine/preparation markers: "
    "'garlic butter shrimp', 'lemon pepper wings', 'chicken parmesan'. KEEP.\n\n"
    "DROP if:\n"
    "  - Proper-noun possessive that's clearly a person, not a chain: "
    "'joe favorite chicken', 'dave special burger', 'uncle ricky chicken', "
    "'mama best lasagna'. (But 'papa john pizza' → KEEP, real chain.)\n"
    "  - Vague modifier with no dish identity: 'chef special', "
    "'house special', 'today special', 'favorite combo', 'best of menu'.\n"
    "  - Single generic word with no qualifier: bare 'chicken', bare 'pizza', "
    "bare 'salad' — too vague to identify.\n"
    "  - Alphabetized gibberish or unrecognizable fragments: 'chee corn fri', "
    "'ad bg chx', random letter combinations.\n"
    "  - Menu code: 'b3', 'c95', 'h12'.\n"
    "  - Add-on or instruction: 'add cheese', 'extra sauce', 'side fries'.\n\n"
    "Reply EXACTLY one line per item, no preamble:\n"
    "N. KEEP <one-word reason>\n"
    "N. DROP <one-word reason>\n\n"
    "Reasons: dish | regional | branded | combo | possessive | vague | "
    "generic | gibberish | code | addon\n"
)

def load_api_key() -> str:
    for line in Path(ENV_FILE).read_text().splitlines():
        if line.startswith("OPENROUTER_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("OPENROUTER_API_KEY not found")

def load_canonicals():
    rows = []
    with open(SUMM) as f:
        for row in csv.DictReader(f):
            try:
                cid = int(row["cluster_id"])
                cnt = int(row["total_count"])
            except (ValueError, KeyError):
                continue
            rows.append({
                "cluster_id": cid,
                "canonical_name": row["canonical_name"],
                "total_count": cnt,
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

def parse_response(text, batch_size):
    results = [None] * batch_size
    for line in text.splitlines():
        m = LINE_RE.match(line)
        if not m:
            continue
        idx = int(m.group(1)) - 1
        if 0 <= idx < batch_size:
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
            "X-Title": f"menu-item-impact L25 {MODEL_KEY}",
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
    canonicals = load_canonicals()
    print(f"loaded {len(canonicals):,} canonicals")
    print(f"model: {MODEL}  batch_size: {BATCH_SIZE}  concurrency: {CONCURRENCY}")

    # Resume support
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
                if time.time() - last_print > 5:
                    elapsed = time.time() - t0
                    rate = n_done / elapsed if elapsed > 0 else 0
                    eta = (len(pending) - n_done) / rate if rate > 0 else 0
                    print(f"  {n_done:>7,}/{len(pending):,}  ({n_keep} KEEP, {n_drop} DROP, {n_err} err)  "
                          f"rate={rate:.0f}/s  eta={eta:.0f}s", flush=True)
                    last_print = time.time()

        await asyncio.gather(*(run_one(b) for b in batches))

    out_handle.close()
    elapsed = time.time() - t0
    print(f"\nDONE in {elapsed:.0f}s")
    print(f"  KEEP: {n_keep:,}")
    print(f"  DROP: {n_drop:,}")
    print(f"  err:  {n_err:,}")

if __name__ == "__main__":
    asyncio.run(main())
