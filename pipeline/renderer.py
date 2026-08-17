#!/usr/bin/env python3
"""pipeline/renderer.py — the RE-RENDERER: generate N equally-valid translations of a passage.

The vision: take a full text, re-render passages/sections into MULTIPLE translations that all score as
equally valid in our ML verification system. This is the "one text, many valid renderings" capability —
useful for (a) fine-tuning data, (b) style/register variants, (c) a "translation lattice" of a text.

For a passage, the renderer:
  1. generates N candidate translations with DIFFERENT registers (literal / plain / precise / natural)
  2. scores each with the deterministic proof gate (translation_proof.py) + semantic fidelity vs gold
  3. keeps the "equally valid" set = those that PASS the gate AND score >= a fidelity threshold
  4. records the valid set as a content-addressed run (the equally-valid renderings)

This is deterministic + stdlib except the model call (hermes). Box-safe: small n.

Usage:
  python3 pipeline/renderer.py --source "…" --gold "…" --n 4          # render one passage
  python3 pipeline/renderer.py --passage <idx> --n 4                  # render a gold passage by index
  python3 pipeline/renderer.py --n 1 --dry-run                        # scaffold check (no model calls)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))

# the registers → different equally-valid renderings of the same meaning
REGISTERS = [
    ("literal", "Translate literally, preserving word order and each clause. Output only the translation."),
    ("plain", "Translate into clear, plain, natural modern English. Simple and readable. Output only the translation."),
    ("precise", "Translate with scholarly precision; keep technical terms transliterated and exact. Output only the translation."),
    ("natural", "Translate fluently and idiomatically as a native English reader would expect. Output only the translation."),
]

SEMANTIC_THRESHOLD = 0.5  # keep renderings scoring >= this semantic fidelity vs gold


def candidate_disagreement(candidates: list[dict]) -> dict:
    """The blueprint §14 signal: how much the valid candidates disagree.

    If N candidates independently converge on the same semantics → LOW disagreement (high confidence).
    If they split into different interpretations → HIGH disagreement → send to human review regardless
    of any single candidate's COMET/semantic score.

    Deterministic: uses character-overlap between the valid candidates (a cheap stand-in for semantic
    divergence until a Sanskrit embedder is available on the GPU box).
    """
    valid = [c["candidate"] for c in candidates if c.get("valid")]
    if len(valid) < 2:
        return {"n_valid": len(valid), "agreement": 1.0, "disagreement": 0.0,
                "verdict": "insufficient-candidates"}
    # pairwise chrF between valid candidates (higher = more agreement)
    from experiment_lab import chrF
    agreements = []
    for i in range(len(valid)):
        for j in range(i + 1, len(valid)):
            agreements.append(chrF(valid[i], valid[j]))
    mean = sum(agreements) / len(agreements)
    # disagreement = 1 - agreement; if candidates are very different interpretations, this is high
    disagreement = round(1.0 - mean, 3)
    verdict = ("convergent" if disagreement < 0.3 else
               "mixed" if disagreement < 0.55 else
               "divergent-review")
    return {"n_valid": len(valid), "mean_pairwise_chrF": round(mean, 3),
            "agreement": round(mean, 3), "disagreement": disagreement,
            "verdict": verdict}


def render_one(source: str, gold: str, n: int, model: str, dry: bool) -> dict:
    from model import chat
    from translation_proof import verify_translation
    from run_recorder import RunRecorder

    candidates = []
    for i in range(n):
        name, style = REGISTERS[i % len(REGISTERS)]
        if dry:
            candidates.append({"register": name, "candidate": "dry", "valid": False})
            continue
        system = ("You are a careful Sanskrit scholar-translator. " + style +
                  " Preserve the meaning faithfully.")
        cand = (chat(system, f"Translate:\n{source}", model=model, timeout=120) or "").strip()
        proof = verify_translation(source, cand, gold=gold)
        # semantic fidelity vs the gold (the "equally valid" measure)
        from experiment_lab import semantic_fidelity
        fid, _ = semantic_fidelity(model, gold, cand)
        valid = proof["deterministic_gate"] == "PASS" and fid >= SEMANTIC_THRESHOLD
        candidates.append({"register": name, "candidate": cand[:300],
                           "gate": proof["deterministic_gate"], "semantic": round(fid, 3),
                           "valid": valid})

    valid_set = [c for c in candidates if c.get("valid")]
    disagreement = candidate_disagreement(candidates)
    rec = RunRecorder().record(
        step="render", gold=[{"source": source, "gold": gold}],
        config={"model": model, "n": n, "registers": [r[0] for r in REGISTERS]},
        metrics={"n_candidates": n, "n_valid": len(valid_set),
                 "disagreement": disagreement["disagreement"]},
        raw=[{k: c.get(k) for k in ("register", "gate", "semantic", "valid")} for c in candidates],
        assertion=f"rendered {n} candidate translations of a passage; {len(valid_set)} score as "
                  f"equally valid; candidate verdict: {disagreement['verdict']} "
                  f"(disagreement {disagreement['disagreement']})")
    return {"candidates": candidates, "n_valid": len(valid_set),
            "disagreement": disagreement,
            "run_signature": rec["run_signature"][:16]}


def render_passage(idx: int, n: int, model: str, dry: bool) -> dict:
    from sanskrit_gold import clean_exemplars
    rows = [e for e in clean_exemplars() if e["work"] == "mitrasamgraha"]
    e = rows[idx % len(rows)]
    print(f"=== rendering passage {idx} ({e['work']}) ===")
    print(f"  SRC:  {e['source'][:70]}")
    print(f"  GOLD: {e['gold'][:70]}\n")
    return render_one(e["source"], e["gold"], n, model, dry)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default="")
    ap.add_argument("--gold", default="")
    ap.add_argument("--passage", type=int, default=-1)
    ap.add_argument("--n", type=int, default=4)
    ap.add_argument("--model", default="mimo-v2.5")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.passage >= 0:
        r = render_passage(args.passage, args.n, args.model, args.dry_run)
    else:
        if not args.source or not args.gold:
            print("need --source and --gold (or --passage N)"); return 2
        print(f"=== rendering passage ===")
        r = render_one(args.source, args.gold, args.n, args.model, args.dry_run)
    print(f"\n  candidates={len(r['candidates'])} equally-valid={r['n_valid']} "
          f"(run {r['run_signature']})")
    for c in r["candidates"]:
        print(f"    [{c['register']:8}] gate={c.get('gate','-')} semantic={c.get('semantic','-')} "
              f"valid={c['valid']} → {c.get('candidate','')[:60]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
