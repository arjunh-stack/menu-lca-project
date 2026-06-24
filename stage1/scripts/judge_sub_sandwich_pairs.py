"""Layer 18 stage 2 — LLM-judge sub/sandwich candidate pairs with RELAXED prompt.

Same OpenRouter machinery as judge_merge_candidates_v2.py but with a different
prompt that says: "These pairs differ only in sub/sandwich format wording.
Default YES — same dish — unless one is clearly a different food."

Inputs:  sub_sandwich_candidates.csv
Outputs: sub_sandwich_judgments.csv
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

CANDIDATES = dpath("sub_sandwich_candidates.csv")
JUDGMENTS  = dpath("sub_sandwich_judgments.csv")
ENV_FILE   = dpath(".env.openrouter")

MODEL       = "google/gemini-2.0-flash-001"
ENDPOINT    = "https://openrouter.ai/api/v1/chat/completions"
BATCH_SIZE  = 20
CONCURRENCY = 50
RETRIES     = 3
TIMEOUT_S   = 60.0

SYSTEM_PROMPT = (
    "You are a food expert classifying pairs of menu item names. "
    "Each pair below differs ONLY by the inclusion or exclusion of a format word "
    "('sub' / 'sandwich'). These are usually the SAME dish — Subway calls them subs, "
    "other shops call the same item a sandwich. Default to SAME unless one of the "
    "names is clearly a different food (e.g. open-faced vs roll, ciabatta vs sub roll, "
    "wrap vs sandwich, pizza vs sandwich). Names are token-sorted alphabetically.\n\n"
    "Reply with EXACTLY one line per pair, no preamble, no closing remarks:\n"
    "N. YES brief reason  (or)  N. NO brief reason\n"
)

def load_api_key() -> str:
    if not os.path.exists(ENV_FILE):
        raise SystemExit(f"missing {ENV_FILE}")
    for line in Path(ENV_FILE).read_text().splitlines():
        if line.startswith("OPENROUTER_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("OPENROUTER_API_KEY not found")

def load_pairs():
    with open(CANDIDATES) as f:
        return list(csv.DictReader(f))

def chunked(it, size):
    buf = []
    for x in it:
        buf.append(x)
        if len(buf) == size:
            yield buf; buf = []
    if buf:
        yield buf

def build_user_prompt(batch):
    return "\n".join(f'{i}. "{p["singleton_name"]}"  vs  "{p["target_name"]}"'
                     for i, p in enumerate(batch, start=1))

LINE_RE = re.compile(r"^\s*(\d+)[\.\):]?\s*(YES|NO)\b[\s,:\-—]*(.*)$", re.I)

def parse_response(text, batch_size):
    results = [None] * batch_size
    for line in text.splitlines():
        m = LINE_RE.match(line)
        if not m:
            continue
        idx = int(m.group(1)) - 1
        if 0 <= idx < batch_size:
            results[idx] = (m.group(2).upper(), m.group(3).strip())
    for i, r in enumerate(results):
        if r is None:
            results[i] = ("PARSE_ERROR", "no parseable line")
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
            "X-Title": "menu-item-impact dish dedup L18",
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
            return parse_response(data["choices"][0]["message"]["content"], len(batch))
        except Exception as e:
            if attempt < RETRIES:
                await asyncio.sleep(2 ** attempt)
                return await judge_batch(client, batch, sem, key, attempt + 1)
            return [("API_ERROR", f"{type(e).__name__}: {e}")] * len(batch)

async def main():
    key = load_api_key()
    pairs = load_pairs()
    print(f"loaded {len(pairs):,} pairs")

    done = set()
    if os.path.exists(JUDGMENTS):
        with open(JUDGMENTS) as f:
            for row in csv.DictReader(f):
                done.add((row["singleton_cid"], row["target_cid"]))
        print(f"  resume: {len(done):,} already judged")
        out_handle = open(JUDGMENTS, "a", newline="")
        writer = csv.writer(out_handle)
    else:
        out_handle = open(JUDGMENTS, "w", newline="")
        writer = csv.writer(out_handle)
        writer.writerow([
            "singleton_cid", "singleton_name", "singleton_count",
            "target_cid", "target_name", "target_count",
            "skeleton", "verdict", "reason",
        ])

    pending = [p for p in pairs if (p["singleton_cid"], p["target_cid"]) not in done]
    print(f"to process: {len(pending):,}")

    sem = asyncio.Semaphore(CONCURRENCY)
    n_done = n_yes = n_no = n_err = 0
    t0 = time.time()
    write_lock = asyncio.Lock()

    batches = list(chunked(pending, BATCH_SIZE))

    async with httpx.AsyncClient() as client:
        async def run_one(batch):
            nonlocal n_done, n_yes, n_no, n_err
            res = await judge_batch(client, batch, sem, key)
            async with write_lock:
                for p, (verdict, reason) in zip(batch, res):
                    writer.writerow([
                        p["singleton_cid"], p["singleton_name"], p["singleton_count"],
                        p["target_cid"], p["target_name"], p["target_count"],
                        p["skeleton"], verdict, reason,
                    ])
                    n_done += 1
                    if verdict == "YES": n_yes += 1
                    elif verdict == "NO": n_no += 1
                    else: n_err += 1
                out_handle.flush()
        await asyncio.gather(*(run_one(b) for b in batches))

    out_handle.close()
    print(f"\nDONE in {time.time()-t0:.0f}s  YES={n_yes}  NO={n_no}  err={n_err}")

if __name__ == "__main__":
    asyncio.run(main())
