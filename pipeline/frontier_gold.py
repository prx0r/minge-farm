#!/usr/bin/env python3
"""pipeline/frontier_gold.py — import + load the FRONTIER translation benchmark datasets.

The frontier labs (Sāmayik, Itihāsa, MITRA) publish parallel English↔Sanskrit test sets. We import them
as ADDITIONAL benchmark sources so our meta-eval ("does our metric beat chrF?") is validated on EXTERNAL
gold, not only our own Mitrasamgraha/IPVV gold. Per AXIOMS: reuse, don't rebuild — we adopt their data.

Imported (from patalacheckpoints/source-evidence/repos/):
  - Sāmayik (LREC-COLING 2024): 2,417 En→Sa test pairs, contemporary prose.
  - Itihāsa: 11,721 En→Sa test pairs, classical śloka (Rāmāyaṇa/Mahābhārata).

Usage:
  from frontier_gold import load_frontier, TEST_SETS
  rows = load_frontier("saamayik")   # [{source(EN), gold(SA), ...}]
"""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FRONTIER = ROOT / "data" / "frontier"

# each set: source language → target language, and the file suffixes
TEST_SETS = {
    "saamayik": {"label": "Sāmayik En→Sa contemporary prose (LREC-COLING 2024)",
                 "src": "test.en", "tgt": "test.sa", "src_lang": "en", "tgt_lang": "sa"},
    "itihasa": {"label": "Itihāsa En→Sa classical śloka (Rāmāyaṇa/Mahābhārata)",
                "src": "test.en", "tgt": "test.sn", "src_lang": "en", "tgt_lang": "sa"},
}


def load_frontier(name: str, n: int | None = None) -> list[dict]:
    """Load one frontier set into gold rows: {source, gold, passage_id, split='<name>-test'}."""
    cfg = TEST_SETS[name]
    src = FRONTIER / name / cfg["src"]
    tgt = FRONTIER / name / cfg["tgt"]
    if not src.exists() or not tgt.exists():
        return []
    rows = []
    with open(src, encoding="utf-8") as s, open(tgt, encoding="utf-8") as t:
        for i, (sl, tl) in enumerate(zip(s, t)):
            s_, t_ = sl.strip(), tl.strip()
            if s_ and t_:
                rows.append({"source": s_, "gold": t_, "passage_id": f"{name}:{i}",
                             "split": f"{name}-test", "src_lang": cfg["src_lang"],
                             "tgt_lang": cfg["tgt_lang"]})
            if n and len(rows) >= n:
                break
    return rows


def available() -> dict:
    """What's imported and how many rows each has."""
    out = {}
    for name, cfg in TEST_SETS.items():
        src = FRONTIER / name / cfg["src"]
        out[name] = {"label": cfg["label"], "imported": src.exists(),
                     "rows": len(load_frontier(name)) if src.exists() else 0}
    return out


if __name__ == "__main__":
    print("=== frontier benchmark datasets ===")
    for name, info in available().items():
        print(f"  {name:10} {info['rows']:>7} rows  {info['label']}")
