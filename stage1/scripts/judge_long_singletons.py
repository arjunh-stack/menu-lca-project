"""Layer 20 stage 2 — LLM keep/drop on the 807 flagged long singletons.

Strict prompt: "Could a chef Google this name and find a real dish?" — but
explicitly tells the model to KEEP regional/ethnic dishes (Mexican, Puerto Rican,
Ethiopian, Thai, etc.) even if it doesn't recognize them, and DROP only when
clearly a list of options / ingredients / sauces / descriptors.

Inputs:  long_singleton_flags.csv
Outputs: long_singleton_judgments.csv
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

CANDIDATES = dpath("long_singleton_flags.csv")
JUDGMENTS  = dpath("long_singleton_judgments.csv")
ENV_FILE   = dpath(".env.openrouter")

MODEL       = "google/gemini-2.0-flash-001"
ENDPOINT    = "https://openrouter.ai/api/v1/chat/completions"
BATCH_SIZE  = 15
CONCURRENCY = 30
RETRIES     = 3
TIMEOUT_S   = 60.0

SYSTEM_PROMPT = (
    "You are a food expert deciding whether each menu name represents a real, "
    "searchable dish. Names are token-sorted alphabetically (word order is "
    "meaningless — mentally rearrange before judging).\n\n"
    "KEEP if it's a real dish from any cuisine — including regional / ethnic "
    "dishes you may not recognize personally (Mexican, Puerto Rican, Cuban, "
    "Ethiopian, Thai, Vietnamese, Filipino, etc.). When the tokens look like "
    "a coherent dish name in a non-English language (mofongo, ropa vieja, "
    "huitlacoche, ceviche, kitfo, etc.), KEEP.\n\n"
    "DROP if it's clearly:\n"
    "  - a list of options ('bacon eggs ham or sausage') — gives diner choices\n"
    "  - a list of sides / sauces / ingredients with no main dish\n"
    "  - bulk-pricing copy ('by the pound', 'serves 4')\n"
    "  - quality descriptors only ('prime usda choice fresh')\n"
    "  - run-on alphabetized junk where you cannot identify a single dish\n\n"
    "Reply with EXACTLY one line per item, no preamble:\n"
    "N. KEEP brief reason  (or)  N. DROP brief reason\n"
)

def load_api_key() -> str:
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
    return "\n".join(f'{i}. "{p["canonical_name"]}"' for i, p in enumerate(batch, start=1))

LINE_RE = re.compile(r"^\s*(\d+)[\.\):]?\s*(KEEP|DROP)\b[\s,:\-—]*(.*)$", re.I)

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
            "X-Title": "menu-item-impact dish dedup L20",
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
    print(f"loaded {len(pairs):,} flagged singletons")

    out_handle = open(JUDGMENTS, "w", newline="")
    writer = csv.writer(out_handle)
    writer.writerow(["cluster_id", "canonical_name", "n_tokens", "verdict", "reason"])

    sem = asyncio.Semaphore(CONCURRENCY)
    n_done = n_keep = n_drop = n_err = 0
    t0 = time.time()
    write_lock = asyncio.Lock()

    batches = list(chunked(pairs, BATCH_SIZE))

    async with httpx.AsyncClient() as client:
        async def run_one(batch):
            nonlocal n_done, n_keep, n_drop, n_err
            res = await judge_batch(client, batch, sem, key)
            async with write_lock:
                for p, (verdict, reason) in zip(batch, res):
                    writer.writerow([p["cluster_id"], p["canonical_name"], p["n_tokens"], verdict, reason])
                    n_done += 1
                    if verdict == "KEEP": n_keep += 1
                    elif verdict == "DROP": n_drop += 1
                    else: n_err += 1
                out_handle.flush()
        await asyncio.gather(*(run_one(b) for b in batches))

    out_handle.close()
    print(f"\nDONE in {time.time()-t0:.0f}s  KEEP={n_keep}  DROP={n_drop}  err={n_err}")

if __name__ == "__main__":
    asyncio.run(main())
