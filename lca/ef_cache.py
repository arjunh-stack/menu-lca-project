"""Emission-factor cache with provenance.

Slim port of ../reverse-recipe/ef_cache.py. Same JSON shape, same locking
discipline, same confidence-rank replacement rule. Cache file lives in
lca/data/ef_cache.json and is checked in (grows with each run).
"""

import os
import json
import threading
from datetime import datetime, timezone

CACHE_PATH = os.path.join(os.path.dirname(__file__), "data", "ef_cache.json")
_CACHE_LOCK = threading.Lock()


def _load_cache():
    if not os.path.exists(CACHE_PATH):
        return {"version": 1, "entries": {}}
    try:
        with open(CACHE_PATH, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"version": 1, "entries": {}}


def _save_cache(cache):
    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    with open(CACHE_PATH, "w") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)


def _normalize_key(ingredient_name: str) -> str:
    return ingredient_name.strip().lower()


def lookup(ingredient_name: str) -> dict | None:
    with _CACHE_LOCK:
        cache = _load_cache()
        key = _normalize_key(ingredient_name)
        entry = cache["entries"].get(key)
        if entry is None:
            return None
        entry["last_accessed"] = datetime.now(timezone.utc).isoformat()
        entry["access_count"] = entry.get("access_count", 0) + 1
        _save_cache(cache)
        return entry


def store(ingredient_name: str, value: float, min_val: float, max_val: float,
          confidence: str, method: str, source_description: str,
          notes: str | None = None,
          matched_lci_name: str | None = None) -> dict:
    """Store an EF in the cache. Replaces existing entry if new entry has
    equal-or-higher confidence (rank: high=3, medium=2, low=1, very_low=0).
    """
    with _CACHE_LOCK:
        cache = _load_cache()
        key = _normalize_key(ingredient_name)
        now = datetime.now(timezone.utc).isoformat()

        entry = {
            "ingredient_name": ingredient_name,
            "value": value,
            "min": min_val,
            "max": max_val,
            "unit": "kg CO2e/kg",
            "confidence": confidence,
            "method": method,
            "source_description": source_description,
            "matched_lci_name": matched_lci_name,
            "notes": notes,
            "created_at": now,
            "last_accessed": now,
            "access_count": 0,
        }

        existing = cache["entries"].get(key)
        if existing:
            rank = {"high": 3, "medium": 2, "low": 1, "very_low": 0}
            old_r = rank.get(existing.get("confidence", "low"), 0)
            new_r = rank.get(confidence, 0)
            if new_r >= old_r:
                entry["previous_value"] = {
                    "value": existing["value"],
                    "confidence": existing["confidence"],
                    "method": existing["method"],
                    "replaced_at": now,
                }
                cache["entries"][key] = entry
            else:
                return existing
        else:
            cache["entries"][key] = entry

        _save_cache(cache)
        return entry


def remove(ingredient_name: str) -> bool:
    with _CACHE_LOCK:
        cache = _load_cache()
        key = _normalize_key(ingredient_name)
        if key in cache["entries"]:
            del cache["entries"][key]
            _save_cache(cache)
            return True
        return False


def get_stats() -> dict:
    cache = _load_cache()
    entries = cache["entries"]
    if not entries:
        return {"total": 0}
    by_conf, by_method = {}, {}
    for e in entries.values():
        by_conf[e.get("confidence", "?")] = by_conf.get(e.get("confidence", "?"), 0) + 1
        by_method[e.get("method", "?")] = by_method.get(e.get("method", "?"), 0) + 1
    return {"total": len(entries), "by_confidence": by_conf, "by_method": by_method}
