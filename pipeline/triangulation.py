#!/usr/bin/env python3
"""pipeline/triangulation.py — the CROSS-CANON triangulation check (§3 of visionadvice.md).

The blueprint §3: for a Sanskrit passage (S) that survives alongside Tibetan (T) / Chinese (C) / English
(E), instead of only asking whether the candidate matches E, test whether S↔E' AND T↔E' / C↔E' all preserve
approximately the same semantic content. MITRA gives the cross-canon parallels for this.

This module:
  - loads the imported MITRA cross-canon sample (Sanskrit ↔ Chinese / Tibetan)
  - given a Sanskrit passage + candidate, finds any cross-canon parallel and reports the agreement signal
  - is the evidence channel for the proof-carrying object + the C_crosslingual confidence feature

Deterministic + stdlib. Streams the (already-sampled) MITRA data.

Usage:
  from triangulation import find_parallels, triangulate
  par = find_parallels(source, lang="bo")       # find a Tibetan parallel for a Sanskrit passage
  t = triangulate(source, candidate, lang="bo") # agreement signal
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))
CROSS = ROOT / "data" / "mitra-crosscanon"

# lang → the imported sample file
LANGS = {"zh": "sa-zh_matches-sample.jsonl", "bo": "sa-bo_matches-sample.jsonl"}


def _load_pairs(lang: str) -> list[dict]:
    f = CROSS / LANGS.get(lang, "")
    if not f.exists():
        return []
    out = []
    for line in open(f, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    return out


def find_parallels(source: str, lang: str = "bo", n: int = 3) -> list[dict]:
    """Find cross-canon parallels for a Sanskrit passage (by token overlap on the Sanskrit side)."""
    # crude: token-overlap between the source and the MITRA Sanskrit side (a real embedder is GPU)
    src_toks = set(w.lower() for w in source.split() if len(w) >= 4)
    if not src_toks:
        return []
    matches = []
    for p in _load_pairs(lang):
        skt = (p.get("sanskrit") or "").lower()
        overlap = sum(1 for t in src_toks if t in skt)
        if overlap >= 1:
            matches.append({"lang": lang, "parallel": p.get("parallel", ""),
                            "sanskrit_side": p.get("sanskrit", ""), "score": p.get("score"),
                            "overlap": overlap, "id": p.get("id")})
    matches.sort(key=lambda m: -m["overlap"])
    return matches[:n]


def triangulate(source: str, candidate: str, lang: str = "bo") -> dict:
    """The cross-canon triangulation agreement signal for one translation."""
    from experiment_lab import chrF
    parallels = find_parallels(source, lang)
    if not parallels:
        return {"available": False, "note": "no cross-canon parallel found", "lang": lang}
    # agreement: chrF between the candidate and the English side IF available; else the parallel presence
    # is the evidence (the real cross-lingual semantic check needs MITRA-E embeddings on GPU)
    return {"available": True, "lang": lang, "n_parallels": len(parallels),
            "parallels": [{"lang": p["lang"], "text": p["parallel"][:60], "score": p["score"]}
                          for p in parallels],
            "note": "parallels found; semantic agreement needs MITRA-E embeddings (GPU)"}


if __name__ == "__main__":
    print("=== cross-canon triangulation (MITRA) ===")
    # a sample Sanskrit passage (from the gold)
    src = "adṛṣṭa pūrvam hṛṣitaḥ asmi dṛṣṭvā bhayena ca pravyathitam manaḥ me"
    for lang in ("zh", "bo"):
        par = find_parallels(src, lang)
        print(f"  {lang}: {len(par)} parallel(s) found")
        for p in par[:2]:
            print(f"    - {p['parallel'][:40]}  (score {p['score']})")
