#!/usr/bin/env python3
"""tools/sanskrit_benchmark.py — the BETTER Sanskrit benchmark: per-tradition × quality × proof × cost.

This is the differentiated Sanskrit leaderboard "nobody else has" (research/PROOF-OF-TRANSLATION.md):
the existing benchmarks (Sāmayik, Itihāsa) give ONE surface number (BLEU/chrF). This one is a decision
system over 4 axes:

  TRADITION  per-tradition control golds (Pratyabhijñā/Trika · Krama · Śaiva Siddhānta · Vedic/General)
  QUALITY    chrF/bleu (surface) + semantic_fidelity (LLM-judge 0-1) — meaning, not word overlap
  PROOF      the deterministic translation_proof gate PASS-rate — verifiable, not asserted
  COST       live per-verse cost from the price catalog (real tokens × live price)

Every experiment (from experiment_lab.py) is logged to the registry; this aggregates them into a
per-tradition, per-model leaderboard with a cost-quality view.

Usage:
  python3 tools/sanskrit_benchmark.py --report            # the 4-axis leaderboard from logged experiments
  python3 tools/sanskrit_benchmark.py --tradition Krama   # the Krama gold subset (control)
  python3 tools/sanskrit_benchmark.py --cost --model deepseek-v4-flash   # cost axis for one model
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pipeline"))

from sanskrit_gold import exemplars, by_tradition, traditions  # noqa: E402

REGISTRY = ROOT / "data" / "corpus" / "registries" / "experiments.jsonl"
PRICES = ROOT / "data" / "corpus" / "model-prices.json"

# the per-verse cost model (from project_translation: 15k prompt / 5k completion tokens per verse)
PROMPT_TOKENS_PER_VERSE = 15000
COMPLETION_TOKENS_PER_VERSE = 5000


def _price_for(model: str):
    """Look up the live per-token price for a model (0 cost if unknown)."""
    try:
        d = json.load(open(PRICES))
        models = d.get("models", {})
        # support both list and dict forms
        if isinstance(models, list):
            by_name = {m.get("id", ""): m for m in models if isinstance(m, dict)}
        else:
            by_name = models
        p = by_name.get(model) or by_name.get(model.split("/")[-1])
        if not p:
            # fuzzy: match by the bare name anywhere in the key (e.g. deepseek-v4-flash-0731)
            for k, cand in by_name.items():
                if model.split("/")[-1].split("-")[0] in k and model.split("/")[-1].split("-")[1] in k:
                    p = cand
                    break
        if not p:
            return None
        fresh = (p.get("prompt_per_token") or 0) * PROMPT_TOKENS_PER_VERSE
        comp = (p.get("completion_per_token") or 0) * COMPLETION_TOKENS_PER_VERSE
        return {"per_verse": fresh + comp, "per_token": p}
    except Exception:
        return None


def _cost_axis(model: str):
    """The cost axis: USD per verse + per 1000 verses."""
    p = _price_for(model)
    if not p:
        return {"per_verse_usd": None, "per_1000_usd": None, "source": "unknown"}
    pv = p["per_verse"]
    return {"per_verse_usd": round(pv, 6), "per_1000_usd": round(pv * 1000, 3), "source": "live-catalog"}


def report() -> None:
    print("=== the BETTER Sanskrit benchmark (per-tradition × quality × proof × cost) ===")

    # 1. the gold control by tradition
    print("\n[gold control] fixed exemplars by tradition:")
    for t in traditions():
        n = len(by_tradition(t))
        print(f"  {t:26} {n}")
    print(f"  {'total':26} {len(exemplars())}")

    # 2. the leaderboard from logged experiments
    print("\n[leaderboard] logged experiments (quality × proof × cost):")
    if not REGISTRY.exists():
        print("  (no experiments logged — run experiment_lab.py first)")
        return
    rows = [json.loads(l) for l in open(REGISTRY) if l.strip()]
    print(f"{'exp':10} {'model':18} {'n':>3} {'chrF':>6} {'sem':>5} {'proof':>5} {'$/1kvers':>9}")
    print("-" * 68)
    for r in rows:
        cost = _cost_axis(r["model"])
        cs = f"{cost['per_1000_usd']}" if cost["per_1000_usd"] else "?"
        print(f"{r['experiment_id'][-10:]:10} {r['model'][:18]:18} {r['n']:>3} "
              f"{r['avg_chrF']:>6.3f} {str(r['avg_semantic']):>5} "
              f"{str(r.get('proof_pass_rate')):>5} {cs:>9}")

    # 3. the cost×quality view (the "which model is best given cost" — the router question)
    print("\n[cost×quality] $/1k-verses vs semantic quality (the router decision):")
    for r in rows:
        cost = _cost_axis(r["model"])
        if cost["per_1000_usd"] and r.get("avg_semantic"):
            quality = r["avg_semantic"]
            q_per_dollar = quality / max(cost["per_1000_usd"], 1e-9)
            print(f"  {r['model'][:18]:18} sem={quality:.2f} ${cost['per_1000_usd']:.2f}/1k "
                  f"→ {q_per_dollar:.2f} quality/$")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--tradition", default=None)
    ap.add_argument("--cost", action="store_true", help="show the cost axis for one model")
    ap.add_argument("--model", default="deepseek-v4-flash")
    args = ap.parse_args()

    if args.tradition:
        subset = by_tradition(args.tradition)
        print(f"=== {args.tradition}: {len(subset)} gold exemplars ===")
        for ex in subset[:6]:
            print(f"  {ex['id']}: src={ex['source'][:45]}… gold={ex['gold'][:45]}…")
        return 0

    if args.cost:
        c = _cost_axis(args.model)
        print(f"=== cost axis: {args.model} ===")
        print(f"  ${c['per_verse_usd']} per verse | ${c['per_1000_usd']} per 1000 verses | source={c['source']}")
        return 0

    report()
    return 0


if __name__ == "__main__":
    sys.exit(main())
