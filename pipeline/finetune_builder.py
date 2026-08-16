#!/usr/bin/env python3
"""pipeline/finetune_builder.py — build FINE-TUNING data (register pairs) from gold + re-renders.

The vision's fine-tuning step: create datasets to fine-tune for "more plain English" and "more precise"
registers. This builder produces LoRA-ready instruction pairs:

  {"instruction": "Translate this Sanskrit into plain English.", "input": <sanskrit>, "output": <plain>}
  {"instruction": "Translate this Sanskrit precisely.", "input": <sanskrit>, "output": <precise>}

Source of the pairs:
  - the GOLD (mitrasamgraha english) as the "natural" target
  - re-rendered candidates (renderer.py) as the "plain" / "precise" / "literal" variants
  - the output is only included if it is VALID (passes the proof gate + semantic threshold)

Deterministic + stdlib except the model call for re-rendering. Writes data/finetune/<name>.jsonl.

Usage:
  python3 pipeline/finetune_builder.py --n 5            # build pairs from 5 gold passages (+ re-renders)
  python3 pipeline/finetune_builder.py --n 1 --dry-run  # scaffold check
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))
OUT = ROOT / "data" / "finetune"


def build(n: int, dry: bool) -> dict:
    from sanskrit_gold import clean_exemplars
    from renderer import render_one, REGISTERS, SEMANTIC_THRESHOLD

    rows = [e for e in clean_exemplars() if e["work"] == "mitrasamgraha"][:n]
    OUT.mkdir(parents=True, exist_ok=True)
    pairs = []
    for e in rows:
        src, gold = e["source"], e["gold"]
        # the gold itself is a "natural/precise" target
        pairs.append({"instruction": "Translate this Sanskrit faithfully into English.",
                      "input": src, "output": gold, "register": "natural", "source": "gold"})
        if dry:
            continue
        # re-render into the other registers; keep only VALID candidates
        r = render_one(src, gold, len(REGISTERS), "deepseek-v4-flash", dry=False)
        for c in r["candidates"]:
            if c.get("valid") and c.get("candidate") != gold:
                reg = c["register"]
                instr = {"literal": "Translate this Sanskrit literally, preserving word order.",
                         "plain": "Translate this Sanskrit into plain, simple modern English.",
                         "precise": "Translate this Sanskrit with scholarly precision, keeping terms exact.",
                         "natural": "Translate this Sanskrit naturally and idiomatically."}[reg]
                pairs.append({"instruction": instr, "input": src,
                              "output": c["candidate"], "register": reg, "source": "render"})

    out_file = OUT / "sanskrit-translation-pairs.jsonl"
    with open(out_file, "w", encoding="utf-8") as f:
        for p in pairs:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
    from collections import Counter
    by_reg = Counter(p["register"] for p in pairs)
    print(f"=== fine-tune pairs: {len(pairs)} (from {len(rows)} gold passages) → {out_file}")
    print(f"  by register: {dict(by_reg)}")
    return {"n_pairs": len(pairs), "by_register": dict(by_reg)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=5)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    build(args.n, args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
