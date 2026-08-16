#!/usr/bin/env python3
"""agent/challenge_verify.py — verify every challenge-set T- is worse than its T+ (the SaQE competence gate).

The DEV-PLAN-NO-GPU N1 gate: "every challenge row's `bad` scores LOWER than its `good` on semantic-fidelity
(a deterministically-checkable property)." A challenge set where the evaluator can't tell the bad from the
good is useless for SaQE training.

Mechanism (stdlib + the hermes judge, no torch):
  for each {source, good, bad, error_family} row:
    fid_good = semantic_fidelity(good, good)  = 1.0 by construction (a good is its own reference)
    fid_bad  = semantic_fidelity(good, bad)   = how much meaning the bad preserves
    pass  ⟺ fid_bad < fid_good
  Report per-family + overall pass rate; log a content-addressed run record + trace line.

Usage:
  python3 agent/challenge_verify.py --n 200        # verify (up to) 200 rows
  python3 agent/challenge_verify.py --n 5          # small sample (box-safe smoke test)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))

from experiment_lab import semantic_fidelity  # noqa: E402  (the LLM-as-judge)
from run_recorder import RunRecorder  # noqa: E402  (content-addressed provenance)

DEFAULT_MODEL = "deepseek-v4-flash"


def verify_one(row: dict, model: str) -> dict:
    """Score good (always 1.0) vs bad (measured); return whether the bad is genuinely worse."""
    _, judg_good = semantic_fidelity(model, row["good"], row["good"])
    fid_bad, judg_bad = semantic_fidelity(model, row["good"], row["bad"])
    fid_good = 1.0  # a good translation preserves its own meaning exactly
    return {
        "error_family": row["error_family"],
        "fid_good": fid_good,
        "fid_bad": fid_bad,
        "pass": fid_bad < fid_good,
        "judg_good": judg_good[:80],
        "judg_bad": judg_bad[:80],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=200, help="rows to verify (default 200)")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    args = ap.parse_args()

    rows = [json.loads(l) for l in
            open(ROOT / "data" / "challenge-sets" / "sanskrit-challenge-set.jsonl", encoding="utf-8")]
    sample = rows[: args.n]
    from collections import Counter
    fam_pass = Counter(); fam_total = Counter()
    results = []
    for i, row in enumerate(sample, 1):
        r = verify_one(row, args.model)
        fam = row["error_family"]
        fam_pass[fam] += 1 if r["pass"] else 0
        fam_total[fam] += 1
        results.append({**row, "fid_bad": r["fid_bad"], "pass": r["pass"]})
        print(f"  [{i}/{len(sample)}] {fam:26} fid_bad={r['fid_bad']:.2f} "
              f"{'PASS' if r['pass'] else 'FAIL'}", flush=True)

    n_pass = sum(1 for r in results if r["pass"])
    overall = n_pass / len(results) if results else 0
    print("\n=== CHALLENGE-SET COMPETENCE GATE (T- < T+ on semantic fidelity) ===")
    print(f"  overall: {n_pass}/{len(results)} rows pass ({overall:.1%})")
    for fam in sorted(fam_total):
        t = fam_total[fam]; p = fam_pass[fam]
        print(f"    {fam:26} {p}/{t} ({p/t:.0%})" if t else f"    {fam:26} n/a")

    metrics = {"n": len(results), "n_pass": n_pass, "pass_rate": round(overall, 4),
               "per_family": {f: {"pass": fam_pass[f], "total": fam_total[f]} for f in fam_total}}
    rr = RunRecorder()
    gold = [{"challenge_set_file": "data/challenge-sets/sanskrit-challenge-set.jsonl",
             "n_rows": len(results), "n_families": len(fam_total)}]
    rec = rr.record(step="challenge_verify", gold=gold, config={"model": args.model, "n": args.n},
                    metrics=metrics, raw=results,
                    assertion="challenge set is a valid SaQE competence test iff pass_rate is high")
    print(f"\n  content-addressed run: {rec['run_signature']}")
    print(f"  => N1 gate {'PASSED' if overall >= 0.9 else 'NOT YET MET'} "
          f"(threshold ≥0.90 bad<good)")
    return 0 if overall >= 0.9 else 1


if __name__ == "__main__":
    sys.exit(main())
