"""Smoke test the OpenRouter call + response parsing on 10 sample pairs."""

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
import sys
sys.path.insert(0, dpath(""))
from judge_merge_candidates import (
    load_api_key, build_user_prompt, parse_response,
    SYSTEM_PROMPT, MODEL, ENDPOINT, TIMEOUT_S,
)
import httpx

CANDIDATES = dpath("merge_candidates.csv")

async def main():
    key = load_api_key()
    pairs = []
    with open(CANDIDATES) as f:
        r = csv.DictReader(f)
        for row in r:
            pairs.append(row)
            if len(pairs) >= 10:
                break

    async with httpx.AsyncClient() as client:
        payload = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": build_user_prompt(pairs)},
            ],
            "temperature": 0,
        }
        r = await client.post(
            ENDPOINT, json=payload,
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/menu-item-impact",
                "X-Title": "menu-item-impact dish dedup",
            },
            timeout=TIMEOUT_S,
        )
        print(f"status: {r.status_code}")
        if r.status_code != 200:
            print(r.text)
            return
        data = r.json()
        text = data["choices"][0]["message"]["content"]
        print(f"\n--- raw response ---\n{text}\n--- end ---\n")
        results = parse_response(text, len(pairs))
        for p, (v, why) in zip(pairs, results):
            print(f"{v:>4} | {p['singleton_name']:<40} -> {p['target_name'][:50]:<50} | {why}")
        usage = data.get("usage", {})
        print(f"\nusage: {usage}")

asyncio.run(main())
