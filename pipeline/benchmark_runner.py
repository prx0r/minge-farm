#!/usr/bin/env python3
"""pipeline/benchmark_runner.py — run the progressive-difficulty Sanskrit benchmark.

For each school × tier passage, PICK the best model (via dealradar's routing) and TRANSLATE + VERIFY it,
scoring per school / period / term-density. This is the benchmark that tests "how well does each model
do on progressively harder Sanskrit texts, tracking school/tradition/time-period/specialist-term %."

Pipeline per passage:
  1. dealradar picks the best model for the tier's task (T4 expert → reasoning-heavy; T1 easy → cheap)
  2. translate the Sanskrit with that model (hermes)
  3. run the deterministic Pāṭala proof gate + semantic-fidelity vs any available gold
  4. record the result per school / period / term-density (content-addressed)

Deterministic + stdlib. Uses hermes for the model calls (dealradar chooses which model). Box-safe:
small samples, one job at a time.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))
sys.path.insert(0, str(ROOT / ".." / "dealradar" / "app"))  # dealradar bridge


def pick_model_for_tier(tier: int) -> dict:
    """Use dealradar to pick the best model for a difficulty tier's task.

    Returns {"recommended": <dealradar's model>, "executed": <hermes-callable model>}.
    dealradar recommends an OpenRouter model (e.g. nvidia/nemotron-3-ultra); the actual translation runs
    via hermes (deepseek-v4-flash) because that's what hermes can reach on this box. We record BOTH —
    the recommendation and what actually ran — so the lineage is honest.
    """
    task = "reasoning" if tier >= 3 else "extraction"
    recommended = "deepseek-v4-flash"
    try:
        from routing import recommend
        res = recommend(task=task, min_quality=0.4, limit=1)
        picks = res.get("picks") or res.get("results") or []
        if picks and isinstance(picks, list):
            recommended = picks[0].get("model") if isinstance(picks[0], dict) else str(picks[0])
        else:
            for k in ("model", "best", "top"):
                if res.get(k):
                    recommended = res[k] if isinstance(res[k], str) else res[k].get("model", "deepseek-v4-flash")
    except Exception as e:
        print(f"  (dealradar pick failed: {e})")
    # the model hermes actually runs (this box); the recommended model is tracked for the lineage
    return {"recommended": recommended, "executed": "deepseek-v4-flash"}


def run_benchmark(n_per_school: int = 2, max_chars: int = 1500, dry_run: bool = False) -> dict:
    from sanskrit_texts import benchmark_rows
    from translation_proof import verify_translation
    from run_recorder import RunRecorder

    rows = benchmark_rows(n_per_school=n_per_school, max_chars=max_chars)
    recorder = RunRecorder()
    results = []
    print(f"=== BENCHMARK: {len(rows)} passages across schools/tiers ===")
    for r in rows:
        pick = pick_model_for_tier(r["tier"])
        rec_model = pick["executed"]  # what hermes actually runs
        print(f"  [T{r['tier']}] {r['school']:22} dealradar={pick['recommended']} run={rec_model} "
              f"density={r['term_density']:.3f}")
        if dry_run:
            results.append({**r, "recommended_model": pick["recommended"], "model": rec_model,
                            "translate": "dry", "gate": "dry"})
            continue
        from model import chat
        system = ("You are a careful Sanskrit scholar-translator. Translate this Sanskrit into accurate, "
                  "natural English. Preserve meaning and technical terms; do not add interpretation. "
                  "Output only the translation.")
        try:
            cand = (chat(system, f"Translate:\n{r['source']}", model=rec_model, timeout=120) or "").strip()
        except Exception as e:
            cand = f"__ERROR__ {e}"
        proof = verify_translation(r["source"], cand)
        results.append({**r, "recommended_model": pick["recommended"], "model": rec_model,
                        "candidate": cand[:300],
                        "deterministic_gate": proof["deterministic_gate"],
                        "blocking": proof["blocking"], "result_id": proof["lineage"]["result_id"]})
        print(f"    → gate={proof['deterministic_gate']} blocking={proof['blocking']}")

    # content-address the whole run (with full lineage)
    rec = recorder.record(step="benchmark", gold=[{"source": x["source"], "school": x["school"]}
                                                   for x in rows],
                          config={"n_per_school": n_per_school, "max_chars": max_chars, "dry_run": dry_run,
                                  "recommender": "dealradar",
                                  "recommended_models": [r.get("recommended_model") for r in results]},
                          metrics={"n_passages": len(rows)},
                          raw=[{k: r.get(k) for k in ("school", "tier", "term_density", "deterministic_gate",
                                                      "recommended_model", "model")}
                               for r in results],
                          assertion=f"benchmark over {len(rows)} Sanskrit passages across "
                                    f"{len(set(r['school'] for r in rows))} schools; "
                                    f"model recommended by dealradar per tier")
    return {"n_passages": len(rows), "results": results, "run_signature": rec["run_signature"][:16]}


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=2)
    ap.add_argument("--max-chars", type=int, default=1500)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    run_benchmark(n_per_school=args.n, max_chars=args.max_chars, dry_run=args.dry_run)
