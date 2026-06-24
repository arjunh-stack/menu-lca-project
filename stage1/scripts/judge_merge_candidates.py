"""Layer 14 stage 2 — LLM-judge each merge candidate pair via OpenRouter.

Reads merge_candidates.csv (128k pairs from token-overlap stage 1).
Sends batched requests to OpenRouter (default model: gemini-2.0-flash-001).
Writes candidate_judgments.csv with per-pair YES/NO + reason.

Tunables: BATCH_SIZE (pairs per request), CONCURRENCY (in-flight requests).
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
import json
import os
import re
import sys
import time
from pathlib import Path

import httpx

CANDIDATES = dpath("merge_candidates.csv")
JUDGMENTS  = dpath("candidate_judgments.csv")
ENV_FILE   = dpath(".env.openrouter")

MODEL       = "google/gemini-2.0-flash-001"
ENDPOINT    = "https://openrouter.ai/api/v1/chat/completions"
BATCH_SIZE  = 20      # pairs per LLM request
CONCURRENCY = 50      # in-flight requests
RETRIES     = 3
TIMEOUT_S   = 60.0

SYSTEM_PROMPT = (
    "You are a food expert classifying pairs of menu item names. "
    "For each numbered pair, decide whether the two names are different ways of describing the SAME real dish "
    "(someone could plausibly order either name and get the same thing) or DIFFERENT dishes. "
    "Names are token-sorted alphabetically (word order is meaningless). "
    "Be strict: if one name adds a key topping/protein/sauce/style that distinguishes the dish (e.g. 'chicken sandwich' vs 'buffalo chicken sandwich'), they are DIFFERENT. "
    "Generic-vs-specific is DIFFERENT. Spelling variants and known synonyms are SAME.\n\n"
    "Reply with EXACTLY one line per pair, no preamble, no closing remarks:\n"
    "N. YES brief reason  (or)  N. NO brief reason\n"
)

def load_api_key() -> str:
    if not os.path.exists(ENV_FILE):
        raise SystemExit(f"missing {ENV_FILE}")
    for line in Path(ENV_FILE).read_text().splitlines():
        if line.startswith("OPENROUTER_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("OPENROUTER_API_KEY not found in env file")

def load_pairs():
    pairs = []
    with open(CANDIDATES) as f:
        for row in csv.DictReader(f):
            pairs.append(row)
    return pairs

def chunked(it, size):
    buf = []
    for x in it:
        buf.append(x)
        if len(buf) == size:
            yield buf
            buf = []
    if buf:
        yield buf

def build_user_prompt(batch):
    lines = []
    for i, p in enumerate(batch, start=1):
        lines.append(f'{i}. "{p["singleton_name"]}"  vs  "{p["target_name"]}"')
    return "\n".join(lines)

LINE_RE = re.compile(r"^\s*(\d+)[\.\):]?\s*(YES|NO)\b[\s,:\-—]*(.*)$", re.I)

def parse_response(text, batch_size):
    """Parse model reply into [(verdict, reason)] of length batch_size."""
    results = [None] * batch_size
    for line in text.splitlines():
        m = LINE_RE.match(line)
        if not m:
            continue
        idx = int(m.group(1)) - 1
        if 0 <= idx < batch_size:
            results[idx] = (m.group(2).upper(), m.group(3).strip())
    # Fill missing with parse_error so we don't lose pairs silently
    for i, r in enumerate(results):
        if r is None:
            results[i] = ("PARSE_ERROR", "no parseable line for this pair")
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
            "X-Title": "menu-item-impact dish dedup",
        }
        try:
            r = await client.post(ENDPOINT, json=payload, headers=headers, timeout=TIMEOUT_S)
            if r.status_code == 429:
                if attempt < RETRIES:
                    await asyncio.sleep(2 ** attempt)
                    return await judge_batch(client, batch, sem, key, attempt + 1)
                raise RuntimeError("rate limit, exhausted retries")
            r.raise_for_status()
            data = r.json()
            text = data["choices"][0]["message"]["content"]
            return parse_response(text, len(batch))
        except Exception as e:
            if attempt < RETRIES:
                await asyncio.sleep(2 ** attempt)
                return await judge_batch(client, batch, sem, key, attempt + 1)
            return [("API_ERROR", f"{type(e).__name__}: {e}")] * len(batch)

async def main():
    key = load_api_key()
    pairs = load_pairs()
    print(f"loaded {len(pairs):,} candidate pairs")
    print(f"model: {MODEL}  batch_size: {BATCH_SIZE}  concurrency: {CONCURRENCY}")

    # Resume support: if JUDGMENTS exists, skip already-judged rows by (singleton_cid, target_cid)
    done = set()
    out_handle = None
    if os.path.exists(JUDGMENTS):
        with open(JUDGMENTS) as f:
            r = csv.DictReader(f)
            for row in r:
                done.add((row["singleton_cid"], row["target_cid"]))
        print(f"  resume: {len(done):,} pairs already judged, skipping")
        out_handle = open(JUDGMENTS, "a", newline="")
        writer = csv.writer(out_handle)
    else:
        out_handle = open(JUDGMENTS, "w", newline="")
        writer = csv.writer(out_handle)
        writer.writerow([
            "singleton_cid", "singleton_name", "target_cid", "target_name",
            "target_count", "shared_tokens", "overlap_ratio",
            "verdict", "reason",
        ])

    pending = [p for p in pairs if (p["singleton_cid"], p["target_cid"]) not in done]
    print(f"to process: {len(pending):,} pairs in {(len(pending) + BATCH_SIZE - 1)//BATCH_SIZE:,} batches")

    sem = asyncio.Semaphore(CONCURRENCY)
    n_done = 0
    n_yes = 0
    n_no = 0
    n_err = 0
    t0 = time.time()
    last_print = t0
    write_lock = asyncio.Lock()

    batches = list(chunked(pending, BATCH_SIZE))

    async with httpx.AsyncClient() as client:
        async def run_one(batch):
            nonlocal n_done, n_yes, n_no, n_err, last_print
            res = await judge_batch(client, batch, sem, key)
            async with write_lock:
                for p, (verdict, reason) in zip(batch, res):
                    writer.writerow([
                        p["singleton_cid"], p["singleton_name"],
                        p["target_cid"], p["target_name"],
                        p["target_count"], p["shared_tokens"], p["overlap_ratio"],
                        verdict, reason,
                    ])
                    n_done += 1
                    if verdict == "YES":
                        n_yes += 1
                    elif verdict == "NO":
                        n_no += 1
                    else:
                        n_err += 1
                out_handle.flush()
                if time.time() - last_print > 5:
                    elapsed = time.time() - t0
                    rate = n_done / elapsed if elapsed > 0 else 0
                    eta = (len(pending) - n_done) / rate if rate > 0 else 0
                    print(f"  {n_done:>7,}/{len(pending):,}  ({n_yes} YES, {n_no} NO, {n_err} err)  "
                          f"rate={rate:.0f}/s  eta={eta:.0f}s", flush=True)
                    last_print = time.time()

        await asyncio.gather(*(run_one(b) for b in batches))

    out_handle.close()
    elapsed = time.time() - t0
    print(f"\nDONE in {elapsed:.0f}s")
    print(f"  YES: {n_yes:,}")
    print(f"  NO:  {n_no:,}")
    print(f"  err: {n_err:,}")

if __name__ == "__main__":
    asyncio.run(main())
