"""Ingredient → emission-factor matcher.

Slim port of ../reverse-recipe/approach_hybrid.py. Pipeline:
  1. Cache lookup (lca/data/ef_cache.json).
  2. Synonym expansion (hardcoded dict, LLM fallback).
  3. Embedding search across AGRIBALYSE + SU-EATABLE LIFE (cosine on
     pre-computed sentence-transformer vectors).
  4. Poore & Nemecek keyword candidates joined in.
  5. LLM disambiguation over the candidate shortlist.
  6. Widen the min/max range via P&N cross-source values + ±30% floor.
  7. Cache and return; record the matched AGRIBALYSE LCI Name for downstream
     multi-impact (water/land) lookup.

D1: AGRIBALYSE-first — embeddings index uses AGRIBALYSE's ag+processing
column (cradle-to-farm-gate, D3), preferring AGRIBALYSE exact matches in
the recommended value.

D4: matches raw LLM-written ingredient strings; relies on synonym + embed
to absorb variation.

Removed vs reverse-recipe: the LLM-reasoning fallback for unmatched
ingredients (`emissions_estimator_unknown`). Unmatched ingredients now
return a structured record with `recommended=None`; the aggregator will
surface them for review rather than guessing.
"""

import os
import re
import json
import sys

import numpy as np
import pandas as pd
import httpx

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ef_cache  # type: ignore  # noqa: E402

OPENROUTER_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
_HTTP_TIMEOUT_S = 60.0
_RETRIES = 3


def _openrouter_chat(api_key: str, prompt: str, temperature: float) -> str | None:
    """One synchronous OpenRouter chat call with retry on 429/5xx.

    Mirrors the retry pattern in recipes/pipeline.py (3 attempts,
    2^attempt backoff). Returns the message content string, or None
    after exhausting retries.
    """
    import time as _time
    payload = {
        "model": LLM_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/menu-item-impact",
        "X-Title": "menu-item-impact lca matcher",
    }
    for attempt in range(_RETRIES + 1):
        try:
            r = httpx.post(OPENROUTER_ENDPOINT, json=payload, headers=headers,
                           timeout=_HTTP_TIMEOUT_S)
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"]
            if r.status_code == 429 or r.status_code >= 500:
                if attempt < _RETRIES:
                    _time.sleep(2 ** attempt)
                    continue
                print(f"  openrouter HTTP {r.status_code} after {_RETRIES} retries")
                return None
            print(f"  openrouter HTTP {r.status_code}: {r.text[:200]}")
            return None
        except Exception as e:
            if attempt < _RETRIES:
                _time.sleep(2 ** attempt)
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

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
EMBEDDINGS_DIR = os.path.join(DATA_DIR, "embeddings")

# ── Hardcoded synonym dictionary ─────────────────────────────────────────
# Ported verbatim from approach_hybrid.SYNONYM_DICT. Lowercase keys.

SYNONYM_DICT = {
    "high fructose corn syrup": ["fructose", "glucose-fructose syrup", "corn sweetener", "HFCS", "isoglucose", "corn syrup", "fructose syrup"],
    "corn syrup": ["glucose syrup", "fructose", "corn sweetener", "maize syrup"],
    "maltodextrin": ["corn starch", "maize starch", "modified corn starch", "corn maltodextrin", "maize/corn starch"],
    "dextrose": ["glucose", "corn sugar", "fructose", "grape sugar", "dextrose monohydrate"],
    "corn starch": ["maize starch", "maize/corn starch", "cornflour"],
    "canola oil": ["rapeseed oil", "colza oil", "canola", "low erucic acid rapeseed oil"],
    "vegetable oil": ["rapeseed oil", "sunflower oil", "soybean oil", "palm oil", "mixed vegetable oil"],
    "whole milk": ["milk, whole", "full fat milk", "pasteurised milk", "cow's milk"],
    "cream cheese": ["cream cheese", "soft cheese", "philadelphia cheese", "fresh cheese with cream"],
    "cheddar cheese": ["cheddar", "hard cheese", "cheese, cheddar", "mature cheese"],
    "sugar": ["white sugar", "sucrose", "cane sugar", "beet sugar", "granulated sugar", "table sugar"],
    "enriched wheat flour": ["wheat flour", "white flour", "bread flour", "all-purpose flour", "refined wheat flour"],
    "wheat flour": ["white flour", "bread flour", "all-purpose flour", "plain flour"],
    "cocoa powder": ["cocoa", "cacao powder", "unsweetened cocoa", "cocoa solids"],
    "dark chocolate": ["chocolate, dark", "bittersweet chocolate", "70% cocoa chocolate", "plain chocolate"],
    "onion powder": ["dried onion", "dehydrated onion", "onion, dried", "onion flakes"],
    "salt": ["sea salt", "table salt", "sodium chloride", "pure salt"],
    "chicken breast": ["chicken breast, raw", "chicken breast without skin", "boneless chicken breast", "chicken fillet"],
    "roasted peanuts": ["peanut, grilled", "grilled peanuts", "toasted peanuts", "dry roasted peanuts", "peanut, roasted"],
    "peanut butter": ["peanut paste", "peanut spread", "ground peanuts", "peanut butter or peanut paste"],
    "tomato paste": ["concentrated tomato", "tomato concentrate", "tomato puree", "double concentrate tomato"],
    "tomato concentrate": ["tomato paste", "concentrated tomato", "double concentrate tomato", "tomato puree concentrate"],
    "distilled vinegar": ["vinegar", "white vinegar", "spirit vinegar", "acetic acid"],
    "palm oil": ["palm oil, refined", "palm fat", "palm kernel oil"],
    "soybean oil": ["soy oil", "soya oil", "soybean oil, refined"],
    "extra virgin olive oil": ["olive oil", "olive oil, extra virgin", "virgin olive oil", "cold pressed olive oil"],
    "coconut cream": ["coconut milk", "coconut cream", "thick coconut milk", "coconut milk or coconut cream"],
    "strawberries": ["strawberry", "strawberry, raw", "fresh strawberry"],
    "water": ["tap water", "drinking water", "potable water"],
    "butter": ["butter, unsalted", "salted butter", "dairy butter", "cow butter"],
}

# ── Poore & Nemecek 2018 reference values (global meta-analysis) ─────────

_POORE_NEMECEK = {
    "Beef (beef herd)": 99.5, "Beef (dairy herd)": 32.9,
    "Lamb & mutton": 39.8, "Pig meat": 12.3, "Poultry meat": 9.3,
    "Farmed fish": 12.6, "Farmed shrimp": 26.5,
    "Cow's milk": 3.2, "Cheese": 23.9, "Eggs": 4.7,
    "Wheat & rye": 1.6, "Rice": 4.5, "Maize": 1.7, "Oatmeal": 2.5,
    "Barley": 1.1, "Cane sugar": 3.2, "Beet sugar": 1.8,
    "Dark chocolate": 46.1, "Coffee": 28.5,
    "Groundnuts": 3.2, "Tree nuts": 0.4, "Soybeans": 2.0,
    "Tofu": 3.2, "Other pulses": 1.8, "Peas": 1.0,
    "Olive oil": 5.9, "Palm oil": 7.3, "Soybean oil": 6.4,
    "Rapeseed oil": 3.7, "Sunflower oil": 3.8,
    "Tomatoes": 2.1, "Potatoes": 0.5, "Onions & leeks": 0.5,
    "Brassicas": 0.5, "Root vegetables": 0.4, "Other vegetables": 0.5,
    "Apples": 0.4, "Bananas": 0.9, "Berries & grapes": 1.5,
    "Citrus fruit": 0.4, "Wine": 1.8, "Beer": 1.2,
}

_POORE_KEYWORD_MAP = {
    "sugar": [("Cane sugar", 3.2), ("Beet sugar", 1.8)],
    "milk": [("Cow's milk", 3.2)], "butter": [("Cow's milk", 3.2)],
    "cream": [("Cow's milk", 3.2)], "cheese": [("Cheese", 23.9)],
    "cheddar": [("Cheese", 23.9)], "mozzarella": [("Cheese", 23.9)],
    "egg": [("Eggs", 4.7)], "wheat": [("Wheat & rye", 1.6)],
    "flour": [("Wheat & rye", 1.6)], "corn": [("Maize", 1.7)],
    "maize": [("Maize", 1.7)], "rice": [("Rice", 4.5)],
    "oat": [("Oatmeal", 2.5)], "barley": [("Barley", 1.1)],
    "olive": [("Olive oil", 5.9)], "palm": [("Palm oil", 7.3)],
    "soy": [("Soybeans", 2.0), ("Soybean oil", 6.4)],
    "soybean": [("Soybeans", 2.0), ("Soybean oil", 6.4)],
    "canola": [("Rapeseed oil", 3.7)], "rapeseed": [("Rapeseed oil", 3.7)],
    "sunflower": [("Sunflower oil", 3.8)], "tomato": [("Tomatoes", 2.1)],
    "potato": [("Potatoes", 0.5)], "onion": [("Onions & leeks", 0.5)],
    "peanut": [("Groundnuts", 3.2)], "nut": [("Tree nuts", 0.4)],
    "almond": [("Tree nuts", 0.4)], "walnut": [("Tree nuts", 0.4)],
    "tofu": [("Tofu", 3.2)], "bean": [("Other pulses", 1.8)],
    "lentil": [("Other pulses", 1.8)], "pea": [("Peas", 1.0)],
    "chicken": [("Poultry meat", 9.3)], "poultry": [("Poultry meat", 9.3)],
    "turkey": [("Poultry meat", 9.3)],
    "beef": [("Beef (beef herd)", 99.5), ("Beef (dairy herd)", 32.9)],
    "lamb": [("Lamb & mutton", 39.8)], "pork": [("Pig meat", 12.3)],
    "fish": [("Farmed fish", 12.6)], "salmon": [("Farmed fish", 12.6)],
    "shrimp": [("Farmed shrimp", 26.5)], "prawn": [("Farmed shrimp", 26.5)],
    "chocolate": [("Dark chocolate", 46.1)], "cocoa": [("Dark chocolate", 46.1)],
    "coffee": [("Coffee", 28.5)], "apple": [("Apples", 0.4)],
    "banana": [("Bananas", 0.9)], "strawberry": [("Berries & grapes", 1.5)],
    "berry": [("Berries & grapes", 1.5)], "grape": [("Berries & grapes", 1.5)],
    "orange": [("Citrus fruit", 0.4)], "lemon": [("Citrus fruit", 0.4)],
    "citrus": [("Citrus fruit", 0.4)],
    "vinegar": [], "wine": [("Wine", 1.8)], "beer": [("Beer", 1.2)],
    "fructose": [("Cane sugar", 3.2), ("Beet sugar", 1.8)],
    "syrup": [("Cane sugar", 3.2)], "starch": [("Maize", 1.7)],
    "dextrose": [("Cane sugar", 3.2), ("Beet sugar", 1.8)],
    "maltodextrin": [("Maize", 1.7)], "coconut": [], "salt": [], "water": [],
    "vegetable": [("Rapeseed oil", 3.7), ("Sunflower oil", 3.8), ("Soybean oil", 6.4)],
}

# Filter out composite-dish embeddings that show up in AGRIBALYSE
_EXCLUDE_PATTERN = re.compile(
    r"sandwich|pizza|pie,|stew|casserole|cake|biscuit|cookie|wafer|"
    r"muffin|waffle|crepe|croissant|pastry|filled|gratin|quiche|"
    r"omelette|pancake|salad,|roll,|samosa|fritter",
    re.IGNORECASE,
)

_MINIMUM_UNCERTAINTY_FRACTION = 0.30  # ±30% floor on the range
LLM_MODEL = "deepseek/deepseek-chat-v3-0324"

# ── Sentence-transformer model (lazy) ────────────────────────────────────

_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


# ── Pre-built embedding indices (lazy load from .npy) ────────────────────

_agri_emb = _agri_names = _agri_co2e = None
_sel_emb = _sel_names = _sel_co2e = None


def _load_embedding_index():
    global _agri_emb, _agri_names, _agri_co2e
    global _sel_emb, _sel_names, _sel_co2e
    if _agri_emb is None:
        p = os.path.join(EMBEDDINGS_DIR, "agribalyse_embeddings.npy")
        if os.path.exists(p):
            _agri_emb = np.load(p)
            _agri_names = np.load(os.path.join(EMBEDDINGS_DIR, "agribalyse_names.npy"), allow_pickle=True)
            _agri_co2e = np.load(os.path.join(EMBEDDINGS_DIR, "agribalyse_co2e.npy"))
        else:
            _agri_emb, _agri_names, _agri_co2e = np.array([]), np.array([]), np.array([])
    if _sel_emb is None:
        p = os.path.join(EMBEDDINGS_DIR, "sel_embeddings.npy")
        if os.path.exists(p):
            _sel_emb = np.load(p)
            _sel_names = np.load(os.path.join(EMBEDDINGS_DIR, "sel_names.npy"), allow_pickle=True)
            _sel_co2e = np.load(os.path.join(EMBEDDINGS_DIR, "sel_co2e.npy"))
        else:
            _sel_emb, _sel_names, _sel_co2e = np.array([]), np.array([]), np.array([])


# ── Query expansion (synonyms) ───────────────────────────────────────────

def _expand_query(ingredient_name: str, api_key: str | None) -> list[str]:
    """Hardcoded dict first; LLM-generated synonyms as fallback."""
    key = ingredient_name.strip().lower()
    base_key = re.sub(r"\s*\(.*?\)", "", key).strip()
    if key in SYNONYM_DICT:
        return SYNONYM_DICT[key]
    if base_key in SYNONYM_DICT:
        return SYNONYM_DICT[base_key]
    if not api_key:
        return []

    prompt = f"""You are a food science expert. Generate 5-8 alternate names, synonyms, or closely related product names for this food ingredient:

"{ingredient_name}"

Consider:
- Common commercial/trade names vs scientific names
- Regional naming differences (US vs UK vs EU)
- The base agricultural product it's derived from
- How it might appear in a life-cycle assessment (LCA) database
- Processing forms (e.g., "dried", "powdered", "refined")

Return ONLY a JSON array of strings, no explanation:
["synonym1", "synonym2", ...]"""
    text = _openrouter_chat(api_key, prompt, temperature=0.3)
    if not text:
        return []
    try:
        out = json.loads(_strip_code_fence(text))
        return [s for s in out if isinstance(s, str)] if isinstance(out, list) else []
    except json.JSONDecodeError as e:
        print(f"  query expansion JSON parse failed for {ingredient_name!r}: {e}")
        return []


# ── Embedding candidate retrieval ────────────────────────────────────────

def _find_candidates_for_emb(query_emb, top_k=20) -> list[dict]:
    _load_embedding_index()
    out = []
    if _agri_emb is not None and len(_agri_emb) > 0:
        scores = _agri_emb @ query_emb
        order = np.argsort(scores)[::-1][: top_k * 2]
        count = 0
        for idx in order:
            name = str(_agri_names[idx])
            if _EXCLUDE_PATTERN.search(name):
                continue
            out.append({"name": name, "co2e": float(_agri_co2e[idx]),
                        "source": "AGRIBALYSE v3.2", "sim_score": float(scores[idx])})
            count += 1
            if count >= top_k:
                break
    if _sel_emb is not None and len(_sel_emb) > 0:
        scores = _sel_emb @ query_emb
        for idx in np.argsort(scores)[::-1][:10]:
            out.append({"name": str(_sel_names[idx]), "co2e": float(_sel_co2e[idx]),
                        "source": "SU-EATABLE LIFE", "sim_score": float(scores[idx])})
    return out


def _find_candidates_expanded(ingredient_name: str, synonyms: list[str],
                              top_k=20) -> list[dict]:
    """Encode original + synonyms, union+dedup candidates by name."""
    _load_embedding_index()
    model = _get_model()
    queries = [ingredient_name] + synonyms
    query_embs = model.encode(queries, normalize_embeddings=True)
    seen: dict[str, dict] = {}
    for q in query_embs:
        for c in _find_candidates_for_emb(q, top_k=top_k):
            n = c["name"].lower()
            if n not in seen or c["sim_score"] > seen[n]["sim_score"]:
                seen[n] = c
    return sorted(seen.values(), key=lambda c: c["sim_score"], reverse=True)[: top_k * 2]


def _search_poore_candidates(ingredient_name: str, synonyms: list[str] | None = None,
                             max_candidates: int = 5) -> list[dict]:
    """Keyword-based P&N candidates over original + synonyms."""
    terms = [ingredient_name] + (synonyms or [])
    out: list[dict] = []
    seen: set[str] = set()
    for term in terms:
        words = [w for w in re.sub(r"[^a-z ]", "", term.lower()).split() if len(w) > 2]
        for product_name, co2e in _POORE_NEMECEK.items():
            if product_name in seen:
                continue
            if any(w in product_name.lower() for w in words):
                out.append({"name": product_name, "co2e": co2e, "source": "Poore & Nemecek 2018"})
                seen.add(product_name)
    return out[:max_candidates]


# ── Uncertainty widening (cross-source + ±30% floor) ────────────────────

def _poore_cross_source(ingredient_name: str) -> list[tuple[str, float]]:
    words = [w for w in re.sub(r"[^a-z ]", "", ingredient_name.lower()).split() if len(w) > 2]
    found: list[tuple[str, float]] = []
    seen: set[str] = set()
    for word in words:
        for keyword, entries in _POORE_KEYWORD_MAP.items():
            if keyword in word or word in keyword:
                for name, co2e in entries:
                    if name not in seen:
                        seen.add(name)
                        found.append((name, co2e))
    return found


def _widen_uncertainty(selected: dict, ingredient_name: str) -> dict:
    """Cross-source enrichment + ±30% floor on the (min, max) range."""
    if not selected or not selected.get("matches"):
        return selected
    recommended = selected["recommended"]
    matches = selected["matches"]
    all_values = [m["co2e"] for m in matches]
    sources = set(m["source"] for m in matches)

    poore_added = []
    for name, co2e in _poore_cross_source(ingredient_name):
        if recommended > 0 and 0.1 * recommended <= co2e <= 10.0 * recommended:
            all_values.append(co2e)
            poore_added.append((name, co2e))
            sources.add("Poore & Nemecek 2018")

    new_min = min(all_values)
    new_max = max(all_values)
    new_min = min(new_min, recommended * (1.0 - _MINIMUM_UNCERTAINTY_FRACTION))
    new_max = max(new_max, recommended * (1.0 + _MINIMUM_UNCERTAINTY_FRACTION))
    new_min = min(new_min, selected["min"])
    new_max = max(new_max, selected["max"])

    selected["min"] = round(float(new_min), 4)
    selected["max"] = round(float(new_max), 4)
    n_sources = len(sources)
    if n_sources >= 2:
        selected["confidence"] = "high"
    elif len(matches) >= 2:
        selected["confidence"] = "medium"
    selected["uncertainty_method"] = "wider_cross_source"
    selected["n_sources_in_range"] = n_sources
    if poore_added:
        selected["poore_enrichment"] = [{"name": n, "co2e": v} for n, v in poore_added]
    return selected


# ── LLM disambiguation ──────────────────────────────────────────────────

def _llm_select_matches(ingredient_name: str, candidates: list[dict],
                        api_key: str) -> dict | None:
    cand_text = "\n".join(
        f"  {i+1}. {c['name']} -- {c['co2e']:.2f} kg CO2e/kg ({c['source']})"
        for i, c in enumerate(candidates[:25])
    )
    prompt = f"""You are a food science expert matching ingredients to carbon footprint data.

I need the carbon footprint for this ingredient: "{ingredient_name}"

Here are candidate matches from LCA databases, ranked by semantic similarity:
{cand_text}

Select ALL candidates that are a good match for "{ingredient_name}".
Consider:
- Is the candidate the SAME product or a very close equivalent?
- Account for processing level: tomato paste is NOT the same as raw tomato
- A good match should represent the same ingredient in roughly the same form
- Exclude composite dishes (pizza, sandwich, cake) that just contain the ingredient
- Include multiple matches if they represent the same ingredient from different sources -- this helps with uncertainty analysis

Return a JSON object:
{{
  "matches": [
    {{"index": 1, "relevance": "exact"}},
    {{"index": 3, "relevance": "close"}},
    ...
  ]
}}

Where relevance is "exact" (same product), "close" (very similar), or "approximate" (similar but different form/processing).
If NONE of the candidates match, return: {{"matches": []}}
Return ONLY valid JSON."""

    text = _openrouter_chat(api_key, prompt, temperature=0.1)
    if not text:
        return None
    try:
        result = json.loads(_strip_code_fence(text))
        selected_matches: list[dict] = []
        for m in result.get("matches", []):
            idx = m.get("index", 0) - 1
            if 0 <= idx < len(candidates):
                entry = candidates[idx].copy()
                entry["relevance"] = m.get("relevance", "approximate")
                entry.pop("sim_score", None)
                selected_matches.append(entry)
        if not selected_matches:
            return None

        # Prefer AGRIBALYSE exact > AGRIBALYSE any > overall exact > overall median
        agri_exact = [m["co2e"] for m in selected_matches
                      if m["relevance"] == "exact"
                      and "AGRIBALYSE" in m.get("source", "").upper()]
        agri_all = [m["co2e"] for m in selected_matches
                    if "AGRIBALYSE" in m.get("source", "").upper()]
        exact = [m["co2e"] for m in selected_matches if m["relevance"] == "exact"]
        if agri_exact:
            recommended = float(np.median(agri_exact))
        elif agri_all:
            recommended = float(np.median(agri_all))
        elif exact:
            recommended = float(np.median(exact))
        else:
            recommended = float(np.median([m["co2e"] for m in selected_matches]))

        # Pick the matched LCI name (prefer AGRIBALYSE exact; helps downstream
        # multi-impact lookup since water/land come from the same table).
        matched_lci = None
        for tier in (
            [m for m in selected_matches if m["relevance"] == "exact" and "AGRIBALYSE" in m.get("source", "").upper()],
            [m for m in selected_matches if "AGRIBALYSE" in m.get("source", "").upper()],
            [m for m in selected_matches if m["relevance"] == "exact"],
            selected_matches,
        ):
            if tier:
                matched_lci = tier[0]["name"]
                break

        values = [m["co2e"] for m in selected_matches]
        n_sources = len(set(m["source"] for m in selected_matches))
        confidence = "high" if n_sources >= 2 or len(exact) >= 2 else "medium"
        return {
            "ingredient": ingredient_name,
            "matches": selected_matches,
            "matched_lci_name": matched_lci,
            "recommended": recommended,
            "min": float(min(values)),
            "max": float(max(values)),
            "n_matches": len(selected_matches),
            "confidence": confidence,
            "method": "hybrid_query_expansion_wider_uncertainty",
        }
    except Exception as e:
        print(f"  LLM match selection failed for {ingredient_name!r}: {e}")
        return None


# ── Public API ──────────────────────────────────────────────────────────

def match_ingredient(ingredient_name: str, api_key: str | None = None) -> dict:
    """Match an ingredient to EF values.

    Returns
    -------
    dict with keys:
      - ingredient: str
      - matches: list of {name, co2e, source, relevance}
      - matched_lci_name: str | None (best AGRIBALYSE LCI Name for
        downstream multi-impact lookup)
      - recommended: float | None (kg CO2e/kg; None if unmatched)
      - min, max: float | None
      - n_matches: int
      - confidence: str
      - method: str
      - unmatched: bool (True if matching failed; recommended/min/max are None)
    """
    # 1. Cache
    cached = ef_cache.lookup(ingredient_name)
    if cached is not None:
        return {
            "ingredient": ingredient_name,
            "matches": [{"name": cached.get("source_description") or "",
                         "co2e": cached["value"],
                         "source": "Local cache", "relevance": "exact"}],
            "matched_lci_name": cached.get("matched_lci_name"),
            "recommended": cached["value"],
            "min": cached["min"],
            "max": cached["max"],
            "n_matches": 1,
            "confidence": cached["confidence"],
            "method": f"cached_{cached['method']}",
            "unmatched": False,
        }

    key = api_key or os.getenv("OPENROUTER_API_KEY")

    # 2. Expand → 3. Embedding candidates → 4. Add P&N keyword candidates
    synonyms = _expand_query(ingredient_name, key)
    emb_cands = _find_candidates_expanded(ingredient_name, synonyms, top_k=20)
    poore_cands = _search_poore_candidates(ingredient_name, synonyms)

    seen_names = {c["name"].lower() for c in emb_cands}
    candidates = list(emb_cands)
    for pc in poore_cands:
        if pc["name"].lower() not in seen_names:
            candidates.append(pc)
            seen_names.add(pc["name"].lower())

    if not candidates:
        return _unmatched(ingredient_name, reason="no_candidates")

    # 5. If no API key, take median of all candidates (degenerate path)
    if not key:
        values = [c["co2e"] for c in candidates]
        return {
            "ingredient": ingredient_name,
            "matches": candidates,
            "matched_lci_name": next((c["name"] for c in candidates
                                      if "AGRIBALYSE" in c.get("source", "").upper()), None),
            "recommended": float(np.median(values)),
            "min": float(min(values)),
            "max": float(max(values)),
            "n_matches": len(candidates),
            "confidence": "medium",
            "method": "embedding_search_no_llm",
            "unmatched": False,
        }

    # 6. LLM disambiguation
    selected = _llm_select_matches(ingredient_name, candidates, key)
    if not selected or not selected.get("matches"):
        return _unmatched(ingredient_name, reason="llm_rejected_all")

    # 7. Widen uncertainty, cache, return
    selected = _widen_uncertainty(selected, ingredient_name)
    selected["unmatched"] = False
    ef_cache.store(
        ingredient_name=ingredient_name,
        value=selected["recommended"],
        min_val=selected["min"],
        max_val=selected["max"],
        confidence=selected["confidence"],
        method="hybrid_query_expansion_wider_uncertainty",
        source_description="; ".join(
            f"{m['name']} ({m['source']}: {m['co2e']:.2f})"
            for m in selected["matches"][:3]
        ),
        matched_lci_name=selected.get("matched_lci_name"),
        notes=f"{selected['n_matches']} matches; {len(synonyms)} synonyms",
    )
    return selected


def _unmatched(ingredient_name: str, reason: str) -> dict:
    return {
        "ingredient": ingredient_name,
        "matches": [],
        "matched_lci_name": None,
        "recommended": None,
        "min": None,
        "max": None,
        "n_matches": 0,
        "confidence": "very_low",
        "method": f"unmatched:{reason}",
        "unmatched": True,
    }


# ── Build embedding index (one-time, if not already present) ────────────

def build_embedding_index(force_rebuild: bool = False) -> None:
    """Encode AGRIBALYSE + SU-EATABLE names and save to data/embeddings/.

    Only needed if the .npy files weren't copied over (they were, so this
    is typically a no-op). Use --rebuild to force recompute (e.g., after
    a database update).
    """
    os.makedirs(EMBEDDINGS_DIR, exist_ok=True)
    model = _get_model()

    from agribalyse_loader import load_agribalyse, COL_CO2E_AG_PROC

    agri_emb_path = os.path.join(EMBEDDINGS_DIR, "agribalyse_embeddings.npy")
    if force_rebuild or not os.path.exists(agri_emb_path):
        df = load_agribalyse()
        if not df.empty:
            mask = df[COL_CO2E_AG_PROC].notna() & (df[COL_CO2E_AG_PROC] > 0)
            df_valid = df[mask].copy()
            names = df_valid["LCI Name"].fillna("").values.tolist()
            co2e_vals = df_valid[COL_CO2E_AG_PROC].values.astype(np.float32)
            print(f"  Encoding {len(names)} AGRIBALYSE products...")
            emb = model.encode(names, show_progress_bar=True, batch_size=256,
                               normalize_embeddings=True)
            np.save(agri_emb_path, emb)
            np.save(os.path.join(EMBEDDINGS_DIR, "agribalyse_names.npy"),
                    np.array(names, dtype=object))
            np.save(os.path.join(EMBEDDINGS_DIR, "agribalyse_co2e.npy"), co2e_vals)

    sel_emb_path = os.path.join(EMBEDDINGS_DIR, "sel_embeddings.npy")
    if force_rebuild or not os.path.exists(sel_emb_path):
        sel_xlsx = os.path.join(DATA_DIR, "su-eatable", "SuEatableLife_Food_Fooprint_database.xlsx")
        if os.path.exists(sel_xlsx):
            df = pd.read_excel(sel_xlsx, sheet_name="SEL CF for users")
            col_name = "Food commodity ITEM"
            col_co2e = "Carbon Footprint kg CO2eq/kg or l of food ITEM"
            mask = df[col_co2e].notna() & (df[col_co2e] > 0)
            df_valid = df[mask].copy()
            names = df_valid[col_name].fillna("").values.tolist()
            co2e_vals = df_valid[col_co2e].values.astype(np.float32)
            print(f"  Encoding {len(names)} SU-EATABLE LIFE products...")
            emb = model.encode(names, show_progress_bar=True, batch_size=256,
                               normalize_embeddings=True)
            np.save(sel_emb_path, emb)
            np.save(os.path.join(EMBEDDINGS_DIR, "sel_names.npy"),
                    np.array(names, dtype=object))
            np.save(os.path.join(EMBEDDINGS_DIR, "sel_co2e.npy"), co2e_vals)


if __name__ == "__main__":
    import sys
    if "--rebuild" in sys.argv:
        build_embedding_index(force_rebuild=True)
    else:
        build_embedding_index(force_rebuild=False)
    print("done.")
