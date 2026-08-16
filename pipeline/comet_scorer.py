#!/usr/bin/env python3
"""pipeline/comet_scorer.py — the learned-metric adapter (COMET) for the Sanskrit benchmark.

Phase B of `research/VISION-COMET-SCHOOL-PERIOD-BENCHMARK.md`: before we train anything, measure whether
off-the-shelf COMET actually beats chrF/bleu on OUR Sanskrit gold. This adapter:

  - loads a COMET model (default `Unbabel/wmt22-comet-da`, ref-based; or `cometkiwi-da`, ref-free)
  - scores (source, hypothesis, reference) triples → 0..1 segment scores
  - returns a small, lineage-carrying result dict

Honesty contract: COMET needs torch + the model weights (XLM-R base ~278M, CPU-runnable but not on this
8GB shared box reliably). This module FAILS CLEANLY if comet/torch is absent — it never fabricates a
score. When run on a machine with torch, it returns real learned-metric scores to compare against chrF/bleu.

Usage:
  python3 -c "from comet_scorer import score; print(score('src','hyp','ref'))"   # or run via validate_benchmark
"""
from __future__ import annotations
from pathlib import Path


def _have_comet() -> bool:
    try:
        import torch  # noqa: F401
        import comet  # noqa: F401
        return True
    except Exception:
        return False


COMET_AVAILABLE = _have_comet()


def score(source: str, hypothesis: str, reference: str,
          model: str = "Unbabel/wmt22-comet-da") -> dict:
    """Score one (source, hypothesis, reference) triple with COMET. Returns {comet: 0..1 | None, available, note}.

    Returns comet=None (honestly) if torch/comet is not installed — never a fabricated number.
    """
    if not COMET_AVAILABLE:
        return {"comet": None, "available": False,
                "note": "torch/comet not installed — no learned-metric score (honest: none)"}
    try:
        from comet import download_model, load_from_checkpoint  # noqa: E402
        model_path = download_model(model)
        m = load_from_checkpoint(model_path)
        data = [{"src": source, "mt": hypothesis, "ref": reference}]
        out = m.predict(data, gpus=0, progress_bar=False)
        s = float(out.scores[0]) if hasattr(out, "scores") else float(out[0])
        return {"comet": round(s, 4), "available": True, "model": model}
    except Exception as e:
        return {"comet": None, "available": True, "note": f"comet run failed: {e}"}


def score_batch(pairs: list[dict], model: str = "Unbabel/wmt22-comet-da") -> list[dict]:
    """Score a batch of {src, mt, ref}. Returns the list with a 'comet' key added (or None)."""
    if not COMET_AVAILABLE or not pairs:
        return [{**p, "comet": None} for p in pairs]
    try:
        from comet import download_model, load_from_checkpoint  # noqa: E402
        m = load_from_checkpoint(download_model(model))
        data = [{"src": p["src"], "mt": p["mt"], "ref": p["ref"]} for p in pairs]
        out = m.predict(data, gpus=0, progress_bar=False)
        scores = out.scores if hasattr(out, "scores") else out
        return [{**p, "comet": round(float(s), 4)} for p, s in zip(pairs, scores)]
    except Exception as e:
        return [{**p, "comet": None, "note": f"comet failed: {e}"} for p in pairs]


if __name__ == "__main__":
    print(f"COMET available: {COMET_AVAILABLE}")
    if COMET_AVAILABLE:
        r = score("kramasadbhava namaḥ", "homage to the kramasadbhava", "homage to the kramasadbhava")
        print("sample:", r)
    else:
        print("honest state: torch/comet not installed — run Phase B on a machine with torch.")
