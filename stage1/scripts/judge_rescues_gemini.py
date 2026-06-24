"""Gemini Flash auto-judges the 1,072 drop-rescue candidates.

For each candidate, asks: "Is the dropped form essentially the same dish as
the suggested merge target?" YES/NO. Auto-apply YES merges downstream.

Inputs:
  - dish_rescue_data.json (from find_drop_rescues.py)
Outputs:
  - dish_rescue_judgments.csv (cluster_id, verdict, reason, target_cid, target_canonical)
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
import time
from pathlib import Path

import httpx

DATA      = dpath("dish_rescue_data.json")
JUDGMENTS = dpath("dish_rescue_judgments.csv")
ENV_FILE  = dpath(".env.openrouter")
ENDPOINT  = "https://openrouter.ai/api/v1/chat/completions"

MODEL       = "google/gemini-2.0-flash-001"
BATCH_SIZE  = 20
CONCURRENCY = 50
RETRIES     = 3
TIMEOUT_S   = 90.0

SYSTEM_PROMPT = (
    "You decide whether a token-sorted 'dropped' dish name is essentially the "
    "SAME dish as a cleaner 'target' dish name from the same database, just "
    "with extra noisy or proper-noun tokens.\n\n"
    "Names are token-sorted alphabetically. The 'noise' tokens are the words "
    "in the dropped form that are NOT in the target. Each line shows you the "
    "dropped form, its count, a raw human-readable form, the target, target's "
    "count, and the noise tokens.\n\n"
    "Reply YES if the dropped form is just the same target dish + meaningless "
    "noise. Conditions for YES:\n"
    "  - noise tokens are proper nouns (person names, restaurant names, "
    "locations, brand names): 'sean', 'nino', 'ennis', 'shasta', 'vagabond', "
    "'james', 'jungle', 'maverick'\n"
    "  - noise tokens are filler modifiers without changing the dish: "
    "'special', 'famous', 'homemade', 'signature', 'classic', 'original'\n"
    "  - noise tokens are restaurant brand artifacts: 'things' (BWW Wild "
    "Things), 'whatameal' (Whataburger combo)\n\n"
    "Reply NO if the noise tokens change the dish identity:\n"
    "  - protein/ingredient changes: 'veggie' (veggie burger ≠ meat burger), "
    "'beyond', 'impossible', 'tofu', 'plant'\n"
    "  - style/cuisine changes: 'gyro', 'fried', 'grilled', 'baked', 'smoked', "
    "'cajun', 'thai', 'mexican'\n"
    "  - format changes: 'wrap', 'bowl', 'platter', 'sub', 'sandwich', "
    "'sliders' (when the target is not already that format)\n"
    "  - combo plates: dropped form clearly combines two dishes\n"
    "  - you can't tell what the dropped item is\n\n"
    "Reply EXACTLY one line per item, no preamble:\n"
    "N. YES <one-word reason>\n"
    "N. NO <one-word reason>\n"
)

def load_api_key() -> str:
    for line in Path(ENV_FILE).read_text().splitlines():
        if line.startswith("OPENROUTER_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("OPENROUTER_API_KEY not found")

def chunked(it, size):
    buf = []
    for x in it:
        buf.append(x)
        if len(buf) == size:
            yield buf; buf = []
    if buf:
        yield buf

def build_user_prompt(batch):
    lines = []
    for i, p in enumerate(batch, start=1):
        raw = p["raw_forms"][0] if p["raw_forms"] else p["dropped"]
        lines.append(
            f'{i}. DROPPED: "{p["dropped"]}" ({p["drop_count"]} menus, '
            f'raw: "{raw}") | TARGET: "{p["target"]}" ({p["target_count"]} menus) '
            f'| NOISE: {", ".join(p["noise"])}'
        )
    return "\n".join(lines)

LINE_RE = re.compile(r"^\s*(\d+)[\.\):]?\s*(YES|NO)\b[\s,:\-—]*([^\s].*?)?$", re.I)

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
            "X-Title": "menu-item-impact L25 drop-rescue judge",
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
    d = json.load(open(DATA))
    items = d["items"]
    # Flatten: one entry per (dropped, top_target_suggestion)
    flat = []
    for it in items:
        sug = it["merge_suggestions"][0] if it["merge_suggestions"] else None
        if sug is None: continue
        flat.append({
            "drop_cid":     it["cluster_id"],
            "dropped":      it["canonical"],
            "drop_count":   it["count"],
            "raw_forms":    it["raw_forms"],
            "target_cid":   sug["cluster_id"],
            "target":       sug["canonical"],
            "target_count": sug["count"],
            "noise":        sug["noise_tokens"],
        })
    print(f"to judge: {len(flat):,}")

    out_handle = open(JUDGMENTS, "w", newline="")
    writer = csv.writer(out_handle)
    writer.writerow(["drop_cid","dropped","drop_count","target_cid","target","target_count","noise","verdict","reason"])
    write_lock = asyncio.Lock()
    sem = asyncio.Semaphore(CONCURRENCY)
    n_done = n_yes = n_no = n_err = 0
    t0 = time.time()
    last_print = t0

    batches = list(chunked(flat, BATCH_SIZE))
    async with httpx.AsyncClient() as client:
        async def run_one(batch):
            nonlocal n_done, n_yes, n_no, n_err, last_print
            res = await judge_batch(client, batch, sem, key)
            async with write_lock:
                for p, (verdict, reason) in zip(batch, res):
                    writer.writerow([
                        p["drop_cid"], p["dropped"], p["drop_count"],
                        p["target_cid"], p["target"], p["target_count"],
                        "|".join(p["noise"]),
                        verdict, reason,
                    ])
                    n_done += 1
                    if verdict == "YES": n_yes += 1
                    elif verdict == "NO": n_no += 1
                    else: n_err += 1
                out_handle.flush()
                if time.time() - last_print > 5:
                    elapsed = time.time() - t0
                    rate = n_done / elapsed if elapsed > 0 else 0
                    eta = (len(flat) - n_done) / rate if rate > 0 else 0
                    print(f"  {n_done:>5,}/{len(flat):,}  ({n_yes} YES, {n_no} NO, {n_err} err)  "
                          f"rate={rate:.0f}/s  eta={eta:.0f}s", flush=True)
                    last_print = time.time()
        await asyncio.gather(*(run_one(b) for b in batches))
    out_handle.close()
    print(f"\nDONE in {time.time()-t0:.0f}s")
    print(f"  YES (merge): {n_yes:,}")
    print(f"  NO  (keep dropped): {n_no:,}")
    print(f"  err: {n_err:,}")

if __name__ == "__main__":
    asyncio.run(main())
