"""precompute_fdc_embeddings.py — Embed every FDC food description once.
(Stage 2b, step 2.)

Reads data/fdc_descriptions.csv (built by port_fdc_data.py), encodes each
description with the `all-MiniLM-L6-v2` sentence-transformer — the same
model the LCA matcher uses — and saves the index to data/embeddings/:

  fdc_embeddings.npy  (N, 384) float32, L2-normalised  -> cosine = dot product
  fdc_ids.npy         (N,)     fdc_id strings,  row-aligned
  fdc_names.npy       (N,)     description strings, row-aligned
  fdc_sources.npy     (N,)     source tags,         row-aligned

~13.6 k rows, runs in well under a minute on CPU. One-time; re-run only
after port_fdc_data.py changes.
"""
from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent / "data"
EMB_DIR = DATA_DIR / "embeddings"
MODEL_NAME = "all-MiniLM-L6-v2"


def main() -> None:
    desc_path = DATA_DIR / "fdc_descriptions.csv"
    if not desc_path.exists():
        raise SystemExit(f"{desc_path} not found — run port_fdc_data.py first.")

    df = pd.read_csv(desc_path, dtype=str)
    descriptions = df["description"].fillna("").tolist()
    print(f"loaded {len(descriptions):,} FDC descriptions")

    from sentence_transformers import SentenceTransformer
    print(f"encoding with {MODEL_NAME} ...")
    model = SentenceTransformer(MODEL_NAME)
    emb = model.encode(descriptions, batch_size=256, show_progress_bar=True,
                        normalize_embeddings=True).astype(np.float32)

    EMB_DIR.mkdir(parents=True, exist_ok=True)
    np.save(EMB_DIR / "fdc_embeddings.npy", emb)
    np.save(EMB_DIR / "fdc_ids.npy", df["fdc_id"].to_numpy(dtype=object))
    np.save(EMB_DIR / "fdc_names.npy", np.array(descriptions, dtype=object))
    np.save(EMB_DIR / "fdc_sources.npy", df["source"].to_numpy(dtype=object))
    print(f"wrote 4 .npy files to {EMB_DIR}  (embeddings shape {emb.shape})")


if __name__ == "__main__":
    main()
