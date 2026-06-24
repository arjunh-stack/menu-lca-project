"""Stage 5.4 — name each clade with an LLM.

build_tree.py picks the internal nodes worth naming (clades.json). This
step asks DeepSeek v3 for a short human label for each, given the most
common dishes inside it. One call per clade, temperature 0, run with
async concurrency.

Following the repo's frozen-LLM-decision convention (see README), the
verdicts are written to phylogeny/frozen/clade_labels.csv and replayed
deterministically — the file is resumable, so a re-run only calls the
API for clades not yet labelled.

Output (phylogeny/frozen/):
  clade_labels.csv   node_id,level,n_leaves,label,top_dishes

Usage:
  python3 label_clades.py
  python3 label_clades.py --concurrency 60
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

SCRIPT_DIR = Path(__file__).resolve().parent
PHYLO_DIR = SCRIPT_DIR.parent
REPO = PHYLO_DIR.parent
DATA_DIR = PHYLO_DIR / "data"

CLADES_JSON = DATA_DIR / "clades.json"
DISH_META = DATA_DIR / "dish_meta.csv"
OUT_CSV = PHYLO_DIR / "frozen" / "clade_labels.csv"
ENV_FILE = REPO / ".env.openrouter"

ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "deepseek/deepseek-chat-v3-0324"
RETRIES = 3
HTTP_TIMEOUT = httpx.Timeout(connect=15.0, read=90.0, write=15.0, pool=30.0)


def load_api_key() -> str:
    env = os.environ.get("OPENROUTER_API_KEY")
    if env:
        return env.strip()
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            if line.startswith("OPENROUTER_API_KEY="):
                return line.split("=", 1)[1].strip()
    raise SystemExit(f"OPENROUTER_API_KEY not in env or {ENV_FILE}")


def load_dish_names() -> list[str]:
    with open(DISH_META) as f:
        rows = list(csv.DictReader(f))
    names = [""] * len(rows)
    for r in rows:
        names[int(r["idx"])] = r["canonical_name"] or r["top_raw_name"]
    return names


def build_prompt(dish_names: list[str]) -> tuple[str, str]:
    listed = "\n".join(f"- {n}" for n in dish_names)
    system = ("You label groups of restaurant dishes. Reply with ONLY a "
              "short category label of at most 4 words. No punctuation, "
              "no explanation, no quotes.")
    user = (f"These dishes were grouped together because their recipes use "
            f"similar ingredients in similar proportions:\n\n{listed}\n\n"
            f"Give a single label (≤4 words) describing this group.")
    return system, user


def clean_label(text: str) -> str:
    label = (text or "").strip().splitlines()[0] if text else ""
    label = re.sub(r'^["\'\s\-•]+|["\'\s\.]+$', "", label).strip()
    return " ".join(label.split()[:4])


async def call_one(client, key, clade, names, attempt=0) -> dict:
    dish_names = [names[i] for i in clade["top_dish_idxs"] if names[i]]
    system, user = build_prompt(dish_names)
    payload = {
        "model": MODEL,
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": user}],
        "max_tokens": 32,
        "temperature": 0,
    }
    headers = {"Authorization": f"Bearer {key}",
               "Content-Type": "application/json",
               "HTTP-Referer": "https://github.com/menu-item-impact",
               "X-Title": "menu-item-impact phylogeny"}
    try:
        r = await client.post(ENDPOINT, json=payload, headers=headers,
                               timeout=HTTP_TIMEOUT)
        if (r.status_code == 429 or r.status_code >= 500) and attempt < RETRIES:
            await asyncio.sleep(2 ** attempt)
            return await call_one(client, key, clade, names, attempt + 1)
        if r.status_code != 200:
            return {**clade, "label": "", "ok": False}
        text = r.json()["choices"][0]["message"]["content"]
        label = clean_label(text)
        return {**clade, "label": label, "ok": bool(label)}
    except Exception:
        if attempt < RETRIES:
            await asyncio.sleep(2 ** attempt)
            return await call_one(client, key, clade, names, attempt + 1)
        return {**clade, "label": "", "ok": False}


def load_done() -> set[str]:
    if not OUT_CSV.exists():
        return set()
    with open(OUT_CSV) as f:
        return {row["node_id"] for row in csv.DictReader(f)}


async def run(args):
    key = load_api_key()
    clades = json.loads(CLADES_JSON.read_text())
    names = load_dish_names()
    done = load_done()
    pending = [c for c in clades if c["node_id"] not in done]
    print(f"{len(clades):,} clades, {len(done):,} already labelled, "
          f"{len(pending):,} to do")
    if not pending:
        print("nothing to do.")
        return

    new_file = not OUT_CSV.exists()
    out = open(OUT_CSV, "a", newline="")
    writer = csv.writer(out)
    if new_file:
        writer.writerow(["node_id", "level", "n_leaves", "label", "top_dishes"])

    sem = asyncio.Semaphore(args.concurrency)
    lock = asyncio.Lock()
    n_ok = n_err = 0
    t0 = time.time()

    async with httpx.AsyncClient(http2=False, timeout=HTTP_TIMEOUT) as client:
        async def worker(clade):
            nonlocal n_ok, n_err
            async with sem:
                rec = await call_one(client, key, clade, names)
            async with lock:
                top = "; ".join(names[i] for i in clade["top_dish_idxs"][:8]
                                if names[i])
                writer.writerow([rec["node_id"], rec["level"],
                                 rec["n_leaves"], rec["label"], top])
                if rec["ok"]:
                    n_ok += 1
                else:
                    n_err += 1
                done_n = n_ok + n_err
                if done_n % 25 == 0:
                    out.flush()
                    rate = done_n / max(time.time() - t0, 1e-6)
                    print(f"  {done_n}/{len(pending)} "
                          f"({n_ok} ok, {n_err} err) {rate:.1f}/s", flush=True)

        await asyncio.gather(*(worker(c) for c in pending))

    out.flush()
    out.close()
    print(f"DONE in {time.time() - t0:.0f}s — {n_ok} ok, {n_err} err "
          f"→ {OUT_CSV.name}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--concurrency", type=int, default=60)
    args = ap.parse_args()
    if not os.environ.get("OPENROUTER_API_KEY") and not ENV_FILE.exists():
        print(f"ERROR: set OPENROUTER_API_KEY or create {ENV_FILE}",
              file=sys.stderr)
        sys.exit(1)
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
