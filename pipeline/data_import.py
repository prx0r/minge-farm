#!/usr/bin/env python3
"""pipeline/data_import.py — import + catalog the frontier datasets (the blueprint's data layer).

Imports/catalogs the datasets from visionadvice.md that we can acquire on this CPU box:
  - MITRA-parallel v2 (Sanskrit↔Chinese / Sanskrit↔Tibetan cross-canon triangulation) — streamed, sampled
  - Itihāsa / Sāmayik (already imported via frontier_gold.py)
  - Mitrasamgraha (already the primary gold)

For each dataset, writes a data-catalog entry + (for the triangulation one) a small cross-witness sample
we can use for the proof-carrying evidence without bulk-loading 323MB into memory.

Streams (never bulk-loads — box rule). Deterministic + stdlib.

Usage:
  python3 pipeline/data_import.py --sample-mitra 2000     # stream MITRA sa-zh, keep a sample
  python3 pipeline/data_import.py --catalog              # show the data catalog
"""
from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))

# the cloned MITRA-parallel v2 files (Sanskrit ↔ Chinese / Tibetan)
MITRA_V2 = Path("/root/patalacheckpoints/source-evidence/repos/dharmamitra__mitra-parallel/v2")
MITRA_FILES = ["sa-zh_matches.ndjson.gz", "sa-bo_matches.ndjson.gz"]

OUT = ROOT / "data" / "mitra-crosscanon"
CATALOG = ROOT / "data" / "data-catalog.json"


def _stream_mitra(fname: str, sample_n: int) -> list[dict]:
    """Stream a MITRA file, keeping a small sample (never loads the whole 323MB into memory)."""
    p = MITRA_V2 / fname
    if not p.exists():
        print(f"  (no {fname})"); return []
    out = []
    with gzip.open(p, "rt", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= sample_n:
                break
            try:
                d = json.loads(line)
            except Exception:
                continue
            # keep the triangulation-relevant fields (small)
            out.append({"id": d.get("id"), "src_lang": d.get("src_lang"), "tgt_lang": d.get("tgt_lang"),
                        "score": d.get("score"), "gemini_score": d.get("gemini_score"),
                        "sanskrit": d.get("root_string", ""), "parallel": d.get("par_string", ""),
                        "root_id": (d.get("root_segnr") or [""])[0],
                        "par_id": (d.get("par_segnr") or [""])[0]})
    return out


def sample_mitra(n: int) -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    catalog = {}
    for fname in MITRA_FILES:
        rows = _stream_mitra(fname, n)
        if not rows:
            continue
        # write the sample + the pairing (Sanskrit side as the triangulation source)
        sample = OUT / f"{fname.replace('.ndjson.gz','')}-sample.jsonl"
        with open(sample, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        lang = "zh" if "zh" in fname else "bo"
        catalog[f"mitra-sa-{lang}"] = {"source": str(sample), "pairs": len(rows),
                                       "evidence": "cross-canon triangulation (Sanskrit ↔ "
                                                   + ("Chinese" if lang == "zh" else "Tibetan") + ")"}
        print(f"  ✓ mitra-sa-{lang}: {len(rows)} sampled pairs → {sample}")
    return catalog


def catalog_all() -> dict:
    """The full data catalog (what we have + what's imported for training/benchmark)."""
    c = {}
    # mitrasamgraha
    mitra = ROOT / "data" / "benchmarks" / "mitrasamgraha" / "test.jsonl"
    if mitra.exists():
        n = sum(1 for _ in open(mitra, encoding="utf-8") if _.strip())
        c["mitrasamgraha"] = {"pairs": n, "role": "primary translation gold + SFT corpus"}
    # frontier
    for name in ("itihasa", "saamayik"):
        f = ROOT / "data" / "frontier" / name
        if f.exists():
            c[name] = {"role": "external translation gold", "imported": True}
    # mitra cross-canon samples
    for f in sorted((ROOT / "data" / "mitra-crosscanon").glob("*.jsonl")):
        n = sum(1 for _ in open(f, encoding="utf-8") if _.strip())
        c[f.stem] = {"pairs": n, "role": "cross-canon triangulation evidence"}
    # persist the catalog
    CATALOG.parent.mkdir(parents=True, exist_ok=True)
    CATALOG.write_text(json.dumps(c, ensure_ascii=False, indent=2))
    return c


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample-mitra", type=int, default=0)
    ap.add_argument("--catalog", action="store_true")
    args = ap.parse_args()
    if args.sample_mitra:
        print(f"=== importing MITRA cross-canon (sampled to {args.sample_mitra}/file, streamed) ===")
        sample_mitra(args.sample_mitra)
    if args.catalog or args.sample_mitra:
        print("\n=== DATA CATALOG ===")
        for name, info in catalog_all().items():
            print(f"  {name:24} {info.get('pairs', info.get('imported', ''))}  {info.get('role','')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
