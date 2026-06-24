"""fdc_matcher.py — Recipe ingredient string -> one USDA FoodData Central
food, for per-100 g macro lookup. (Stage 2b matcher module.)

Pipeline per ingredient (mirrors lca/matcher.py, simplified):
  1. Cache lookup (data/fdc_match_cache.json).
  2. Embedding search: encode the ingredient with all-MiniLM-L6-v2,
     cosine vs. the pre-computed FDC description index, take the top-K.
  3. LLM disambiguation: a single OpenRouter call picks the ONE best FDC
     entry, applying a cooked-vs-raw preference rule (PLAN D3).
  4. Attach that food's per-100 g macros, cache, return.

Why one match, not many: macros need a single per-100 g value per
ingredient. The LCA matcher deliberately keeps multiple matches to widen
an uncertainty range; here we want the single best nutrition entry.

Unmatched ingredients return a structured record with macros=None and
unmatched=True — the aggregator surfaces them rather than guessing.
"""
import json
import os
import sys
import time
from pathlib import Path
from threading import Lock

import httpx
import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent / "data"
EMB_DIR = DATA_DIR / "embeddings"
CACHE_PATH = DATA_DIR / "fdc_match_cache.json"

OPENROUTER_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
LLM_MODEL = "deepseek/deepseek-chat-v3-0324"  # mirrors recipes + lca stages
_HTTP_TIMEOUT_S = 60.0
_RETRIES = 3
TOP_K = 25

MACRO_COLS = ["energy_kcal", "protein_g", "fat_g", "carb_g"]

# ── Manual overrides for known FDC coverage gaps ─────────────────────────
# A few recipe ingredients have no acceptable FDC entry — the matcher
# correctly rejects every candidate. Where a defensible proxy exists we
# pin it here by fdc_id, so the macros are still sourced from the real
# FDC macro table rather than guessed. Keys are lowercased ingredient
# strings; values are fdc_id strings present in fdc_macro_table.csv.
_MANUAL_OVERRIDES = {
    # FDC has no plain pizza-dough / raw-crust entry — only composite
    # pizzas and branded refrigerated doughs. Proxy: plain white-wheat
    # bread (SR Legacy 167532), the closest lean baked-flour-dough macro
    # profile. Without this, pizza dishes undercount calories badly.
    "pizza dough": "167532",
    # The embedding/LLM step missed these despite good FDC entries
    # existing (added after the NUT-3 full run surfaced them in the
    # low-match tail). All four are real FDC SR Legacy foods:
    "oil": "171411",            # Oil, soybean, salad or cooking — the
                                #   generic US cooking/vegetable oil
    "whole chicken": "171450",  # Chicken, broilers or fryers, meat and
                                #   skin, cooked, roasted (as-eaten)
    "filet mignon": "168722",   # Beef, tenderloin, steak, choice,
                                #   cooked, broiled
    "jasmine rice": "168878",   # Rice, white, long-grain, regular,
                                #   enriched, cooked
}


# ── OpenRouter ───────────────────────────────────────────────────────────

def _openrouter_chat(api_key: str, prompt: str, temperature: float) -> str | None:
    """One synchronous OpenRouter chat call, 3 retries with 2^n backoff."""
    payload = {
        "model": LLM_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/menu-item-impact",
        "X-Title": "menu-item-impact nutrition matcher",
    }
    for attempt in range(_RETRIES + 1):
        try:
            r = httpx.post(OPENROUTER_ENDPOINT, json=payload, headers=headers,
                           timeout=_HTTP_TIMEOUT_S)
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"]
            if r.status_code == 429 or r.status_code >= 500:
                if attempt < _RETRIES:
                    time.sleep(2 ** attempt)
                    continue
                print(f"  openrouter HTTP {r.status_code} after {_RETRIES} retries")
                return None
            print(f"  openrouter HTTP {r.status_code}: {r.text[:200]}")
            return None
        except Exception as e:
            if attempt < _RETRIES:
                time.sleep(2 ** attempt)
                continue
            print(f"  openrouter call failed after {_RETRIES} retries: {e}")
            return None
    return None


def _strip_code_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text
        if text.endswith("```"):
            text = text.rsplit("\n", 1)[0]
    return text.strip()


# ── Lazy globals: model, embedding index, macro table, cache ─────────────

_model = None
_emb = _ids = _names = _sources = None
_macros: dict[str, dict] | None = None
_cache: dict[str, dict] | None = None
_cache_lock = Lock()


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def _load_index() -> None:
    global _emb, _ids, _names, _sources
    if _emb is None:
        _emb = np.load(EMB_DIR / "fdc_embeddings.npy")
        _ids = np.load(EMB_DIR / "fdc_ids.npy", allow_pickle=True)
        _names = np.load(EMB_DIR / "fdc_names.npy", allow_pickle=True)
        _sources = np.load(EMB_DIR / "fdc_sources.npy", allow_pickle=True)


def _load_macros() -> dict[str, dict]:
    global _macros
    if _macros is None:
        df = pd.read_csv(DATA_DIR / "fdc_macro_table.csv", dtype={"fdc_id": str})
        _macros = {}
        for _, row in df.iterrows():
            rec = {c: float(row[c]) for c in MACRO_COLS}
            rec["description"] = str(row["description"])
            rec["source"] = str(row["source"])
            _macros[row["fdc_id"]] = rec
    return _macros


def _load_cache() -> dict[str, dict]:
    global _cache
    if _cache is None:
        if CACHE_PATH.exists():
            _cache = json.loads(CACHE_PATH.read_text())
        else:
            _cache = {}
    return _cache


def save_cache() -> None:
    """Persist the in-memory match cache. Call once after a batch run."""
    with _cache_lock:
        if _cache is not None:
            CACHE_PATH.write_text(json.dumps(_cache, indent=1, sort_keys=True))


def warm() -> None:
    """Pre-load every lazy global so worker threads don't race on first use."""
    _get_model()
    _load_index()
    _load_macros()
    _load_cache()


# ── Embedding candidate retrieval ────────────────────────────────────────

def _find_candidates(ingredient: str, top_k: int = TOP_K) -> list[dict]:
    _load_index()
    q = _get_model().encode([ingredient], normalize_embeddings=True)[0]
    scores = _emb @ q
    order = np.argsort(scores)[::-1][:top_k]
    return [
        {"fdc_id": str(_ids[i]), "description": str(_names[i]),
         "source": str(_sources[i]), "sim": float(scores[i])}
        for i in order
    ]


# ── LLM disambiguation ───────────────────────────────────────────────────

# Sentinel: the LLM call itself failed (HTTP error / unparseable / timeout)
# as opposed to the LLM cleanly judging that no candidate matches. The
# former is transient and must NOT be cached; the latter is a real verdict.
_LLM_CALL_FAILED = object()


def _llm_select(ingredient: str, candidates: list[dict],
                api_key: str):
    """Returns a dict {chosen, confidence} on a match, None on a genuine
    "no candidate fits" verdict, or _LLM_CALL_FAILED on a transient error."""
    cand_text = "\n".join(
        f"  {i+1}. {c['description']}  [{c['source']}]"
        for i, c in enumerate(candidates)
    )
    prompt = f"""You are a food scientist matching a recipe ingredient to a USDA FoodData Central (FDC) entry, so its calories/protein/fat/carbohydrate can be looked up.

Recipe ingredient: "{ingredient}"

Candidate FDC entries, ranked by semantic similarity:
{cand_text}

Pick the SINGLE best entry for the nutrition of this ingredient as it would be eaten in a finished dish.

Rules:
- Match the ingredient's form. If the name implies cooking ("fried chicken", "grilled steak", "roasted potatoes", "boiled rice", "cooked pasta"), prefer a COOKED entry. If the name is neutral or raw ("chicken breast", "potato", "rice", "flour"), prefer a raw or plain/generic entry.
- Respect processing level: "tomato paste" is not raw tomato; "wheat flour" is not wheat grain; "cheese" is not milk.
- Prefer a plain whole-ingredient entry over a branded product or a composite dish that merely contains the ingredient.
- The candidate must be the SAME food, not just topically related.

Return ONLY JSON, no prose:
{{"index": <number>, "confidence": "high"|"medium"|"low"}}
where <number> is the integer printed before the chosen entry above (the
list is numbered starting at 1).
If NONE of the candidates is an acceptable match, return: {{"index": null}}"""

    text = _openrouter_chat(api_key, prompt, temperature=0.0)
    if not text:
        return _LLM_CALL_FAILED
    try:
        result = json.loads(_strip_code_fence(text))
    except json.JSONDecodeError as e:
        print(f"  LLM JSON parse failed for {ingredient!r}: {e}")
        return _LLM_CALL_FAILED
    idx = result.get("index")
    if idx is None:
        return None  # genuine "no candidate fits" verdict
    try:
        idx = int(idx)
    except (TypeError, ValueError):
        return None
    # Candidates are numbered 1..N in the prompt. Models reliably return a
    # 1-based number, but occasionally 0-index. Since 0 is never valid under
    # 1-based numbering, treat a returned 0 as "the first candidate";
    # otherwise convert the 1-based number to a 0-based list index.
    idx = 0 if idx == 0 else idx - 1
    if not (0 <= idx < len(candidates)):
        return None
    chosen = candidates[idx]
    return {"chosen": chosen, "confidence": result.get("confidence", "medium")}


# ── Public API ───────────────────────────────────────────────────────────

def _unmatched(ingredient: str, reason: str) -> dict:
    return {
        "ingredient": ingredient, "fdc_id": None,
        "matched_description": None, "source": None,
        "energy_kcal": None, "protein_g": None, "fat_g": None, "carb_g": None,
        "confidence": "none", "method": f"unmatched:{reason}",
        "unmatched": True,
    }


def _matched(ingredient: str, chosen: dict, macros: dict,
             confidence: str, method: str) -> dict:
    return {
        "ingredient": ingredient,
        "fdc_id": chosen["fdc_id"],
        "matched_description": chosen["description"],
        "source": chosen["source"],
        "energy_kcal": macros["energy_kcal"],
        "protein_g": macros["protein_g"],
        "fat_g": macros["fat_g"],
        "carb_g": macros["carb_g"],
        "confidence": confidence,
        "method": method,
        "unmatched": False,
    }


def match_ingredient(ingredient: str, api_key: str | None = None) -> dict:
    """Match one ingredient string to an FDC food + its per-100 g macros.

    Returns a dict with fdc_id, matched_description, source, the four
    per-100 g macros, confidence, method, and unmatched (bool). On any
    failure, macros are None and unmatched is True.
    """
    name = (ingredient or "").strip()
    if not name:
        return _unmatched(ingredient, "empty")

    key_l = name.lower()
    cache = _load_cache()
    with _cache_lock:
        if key_l in cache:
            return dict(cache[key_l])

    macro_tbl = _load_macros()
    api_key = api_key or os.getenv("OPENROUTER_API_KEY")

    # Manual override for a known FDC coverage gap (e.g. pizza dough).
    override_id = _MANUAL_OVERRIDES.get(key_l)
    if override_id and override_id in macro_tbl:
        m = macro_tbl[override_id]
        chosen = {"fdc_id": override_id, "description": m["description"],
                  "source": m["source"]}
        result = _matched(name, chosen, m, "medium", "manual_override")
        with _cache_lock:
            cache[key_l] = result
        return dict(result)

    candidates = _find_candidates(name)
    cacheable = True
    if not candidates:
        result = _unmatched(name, "no_candidates")
    elif not api_key:
        # Degenerate path: take the top embedding hit.
        top = candidates[0]
        m = macro_tbl.get(top["fdc_id"])
        result = (_matched(name, top, m, "low", "embedding_top1_no_llm")
                  if m else _unmatched(name, "no_macros_for_top1"))
    else:
        sel = _llm_select(name, candidates, api_key)
        if sel is _LLM_CALL_FAILED:
            # Transient API failure — return unmatched but DO NOT cache,
            # so a re-run retries this ingredient.
            result = _unmatched(name, "llm_call_failed")
            cacheable = False
        elif sel is None:
            result = _unmatched(name, "llm_rejected_all")
        else:
            chosen = sel["chosen"]
            m = macro_tbl.get(chosen["fdc_id"])
            result = (_matched(name, chosen, m, sel["confidence"],
                               "embedding_search_llm_disambiguation")
                      if m else _unmatched(name, "no_macros_for_choice"))

    if cacheable:
        with _cache_lock:
            cache[key_l] = result
    return dict(result)


if __name__ == "__main__":
    # Quick smoke test.
    warm()
    for ing in sys.argv[1:] or ["grilled chicken breast", "cheddar cheese",
                                "all-purpose flour", "boiled white rice"]:
        r = match_ingredient(ing)
        print(f"{ing!r:34s} -> {r['matched_description']}  "
              f"[{r['source']}] {r['confidence']}  "
              f"kcal={r['energy_kcal']} p={r['protein_g']} "
              f"f={r['fat_g']} c={r['carb_g']}")
    save_cache()
