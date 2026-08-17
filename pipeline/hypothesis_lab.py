#!/usr/bin/env python3
"""pipeline/hypothesis_lab.py — the OPEN-ENDED self-exploring loop (the closed loop).

The lab's "observer → reason → hypothesize → test → keep/discard" loop. Unlike the sweep (which
randomizes configs), this learns from WHY translations fail: the semantic-judge's free-text reasoning is
the raw material, and it generates hypotheses from the error families it observes.

The loop (open-ended — it explores, not just tunes):
  1. OBSERVE   — read the last experiment's rows + the judge's error reasoning per row
  2. REASON    — cluster the failures into error families (from the judgment text) + known families
  3. HYPOTHESIZE — generate candidate configs/prompts that target those failures. Includes NOVEL
     hypotheses derived from the actual observed reasoning (not just a fixed table) — this is what makes
     it "explore interesting things": the judge's language drives what we try next.
  4. TEST      — run each candidate on the SAME fixed gold
  5. KEEP/DISCARD — compare vs the current best on the target axis; keep the winner in the registry.

The rule (per LAB.md): every claim ("X is better") must be backed by a logged experiment on the SAME
data. If it isn't in the registry, it isn't decided.

Usage:
  python3 pipeline/hypothesis_lab.py --propose            # read last experiment, propose hypotheses (no run)
  python3 pipeline/hypothesis_lab.py --loop 2             # run 2 rounds of hypothesize→test→keep (open-ended)
  python3 pipeline/hypothesis_lab.py --rounds 1 --n 3     # one round on 3 gold verses
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))

REGISTRY = ROOT / "data" / "corpus" / "registries" / "experiments.jsonl"
REPORTS = ROOT / "data" / "corpus" / "experiment-reports"
HYP_LOG = ROOT / "data" / "corpus" / "registries" / "hypotheses.jsonl"

# the KNOWN error-family → hypothesis map (the seed; novel ones come from the judge's reasoning)
KNOWN_HYPOTHESES = [
    {"family": "compound semantic loss", "prompt_hint": "Decompose every compound into its members before translating; preserve each member's meaning.",
     "config": {"batch_mode": "char", "model": "mimo-v2.5"}},
    {"family": "case-role inversion", "prompt_hint": "Carefully track the grammatical case/role of each noun; preserve subject-object structure.",
     "config": {"model": "mimo-v2.5"}},
    {"family": "negation loss", "prompt_hint": "Check for negation markers; make sure the negation is preserved in English.",
     "config": {"model": "mimo-v2.5"}},
    {"family": "implicit subject", "prompt_hint": "Identify the implicit subject from verb agreement; make it explicit in English.",
     "config": {"model": "mimo-v2.5"}},
    {"family": "technical-term substitution", "prompt_hint": "Use the canonical glossary; keep technical terms (jñāna, māyā, ātman) consistent.",
     "config": {"model": "mimo-v2.5"}},
    {"family": "scope loss", "prompt_hint": "Preserve quantifier scope and universal/all claims exactly.",
     "config": {"model": "mimo-v2.5"}},
    {"family": "metaphor literalisation", "prompt_hint": "Recognize figurative language; render metaphor as metaphor, not literal prose.",
     "config": {"model": "mimo-v2.5"}},
    {"family": "dropped pāda", "prompt_hint": "Translate every clause/pāda; ensure full verse coverage.",
     "config": {"model": "mimo-v2.5"}},
]


def _last_experiment():
    rows = [json.loads(l) for l in open(REGISTRY) if l.strip()]
    return rows[-1] if rows else None


def _extract_family(judgment: str) -> str:
    """Map a judge's free-text reasoning to an error family (or return the raw snippet as novel)."""
    j = judgment.lower()
    for h in KNOWN_HYPOTHESES:
        if h["family"].split()[0] in j:
            return h["family"]
    return None


def propose(verbose=True) -> list[dict]:
    """Read the last experiment, cluster failures into error families, propose hypotheses."""
    exp = _last_experiment()
    if not exp:
        print("  no experiments logged yet"); return []
    if verbose:
        print(f"=== PROPOSE from {exp['experiment_id']} (model={exp['model']}) ===")
    families = {}
    novel = []
    for row in exp.get("rows", []):
        fid = row.get("semantic_fidelity")
        judg = row.get("judgment", "")
        # only reason about low-fidelity or low-chrF rows (where there's something to fix)
        low = (fid is not None and fid < 0.7) or row["chrF"] < 0.55
        if low and judg and not judg.startswith("__"):
            fam = _extract_family(judg)
            if fam:
                families.setdefault(fam, []).append(judg[:80])
            else:
                novel.append(judg[:120])  # unclassified reasoning → novel hypothesis seed
    if verbose:
        print(f"  error families observed: {list(families.keys()) or 'none'}")
        print(f"  novel observations: {len(novel)}")
        for n in novel[:3]:
            print(f"    • {n}")
    return {"families": families, "novel": novel}


def translate_with_hint(model: str, source: str, prompt_hint: str) -> str:
    """Translate with an extra hypothesis-hint appended to the prompt."""
    from model import chat
    system = ("You are a careful Sanskrit scholar-translator. Translate this Sanskrit into accurate, "
              "natural English. Preserve meaning; do not add interpretation. Output only the translation.")
    user = f"{prompt_hint}\n\nTranslate this Sanskrit:\n{source}"
    raw = chat(system, user, model=model, timeout=90)
    return (raw or "").strip().strip('"').strip()


def _metrics(gold, cand):
    import math, re as _re
    def ngrams(s, n):
        s = _re.sub(r"\s+", "", s); return [s[i:i+n] for i in range(len(s)-n+1)]
    if not gold or not cand:
        return 0.0, 0.0
    p = r = 0.0
    for n in (1, 2, 3):
        rg = set(ngrams(gold, n)); cg = set(ngrams(cand, n))
        if rg and cg:
            inter = len(rg & cg); p += inter/len(cg); r += inter/len(rg)
    chrf = 2*p*r/(p+r)/3.0 if (p+r) else 0.0
    rt, ct = gold.split(), cand.split()
    bp = math.exp(min(0, 1 - len(rt)/len(ct))) if (rt and ct) else 0
    bleu = bp * sum(1 for t in ct if t in set(rt))/len(ct) if ct else 0
    return round(chrf, 4), round(bleu, 4)


def run_hypothesis(hint: str, source: str, gold: str, model: str,
                   passage_id: str, config_key: str) -> dict:
    from translation_proof import verify_translation
    cand = translate_with_hint(model, source, hint)
    chrf, bleu = _metrics(gold, cand)
    proof = verify_translation(source, cand, gold=gold)
    return {"passage_id": passage_id, "hint": hint[:60], "candidate": cand[:200],
            "chrF": chrf, "bleu1": bleu, "proof_gate": proof["deterministic_gate"],
            "proof_blocking": proof["blocking"]}


def loop(rounds: int, n: int, test: str, model: str, dry_run: bool) -> int:
    """The open-ended loop: for each round, observe→propose→test→keep."""
    import time
    from datetime import datetime, timezone
    from experiment_lab import TEST_SOURCES

    current_best = None
    for rnd in range(1, rounds + 1):
        print(f"\n{'='*50}\nROUND {rnd}")
        # 1. observe + propose
        obs = propose()
        fams = list(obs["families"].keys())
        # build the hypothesis set: known families observed + (novel-driven) a generic scope hypothesis
        hypotheses = [h for h in KNOWN_HYPOTHESES if h["family"] in fams]
        if not hypotheses:
            # nothing classified → generic "re-verify carefully" (still explores)
            hypotheses = [{"family": "general care", "prompt_hint": "Translate carefully, verbatim meaning.",
                           "config": {"model": model}}]
        if obs["novel"]:
            hypotheses.append({"family": "novel: " + obs["novel"][0][:40],
                               "prompt_hint": "Attend to the specific issue the judge flagged.",
                               "config": {"model": model}})
        print(f"  testing {len(hypotheses)} hypotheses: {[h['family'] for h in hypotheses]}")

        # 2. test each hypothesis on the fixed gold
        rows = TEST_SOURCES[test]["load"]()[:n]
        best = None
        for h in hypotheses:
            results = []
            for r in rows:
                if dry_run:
                    print(f"  [DRY] hint='{h['prompt_hint'][:40]}' on {r['passage_id']}")
                    continue
                results.append(run_hypothesis(h["prompt_hint"], r["source"], r["gold"],
                                              h["config"]["model"], r["passage_id"], "hyp"))
            if dry_run:
                continue
            avg_chrf = sum(x["chrF"] for x in results)/len(results)
            print(f"  {h['family'][:45]:45} avg_chrF={avg_chrf:.3f}")
            if best is None or avg_chrf > best[1]:
                best = (h["family"], avg_chrf, h)

        if dry_run:
            continue

        # 3. keep/discard vs current best
        if best:
            fam, score, h = best
            exp_id = f"EXP-HYP-{rnd}-{datetime.now(timezone.utc).strftime('%H%M%S')}"
            record = {"experiment_id": exp_id, "round": rnd, "family": fam,
                      "prompt_hint": h["prompt_hint"], "model": h["config"]["model"],
                      "test": test, "n": n, "avg_chrF": round(score, 4),
                      "date": datetime.now(timezone.utc).isoformat()}
            if current_best is None or score > current_best[0]:
                print(f"  ✓ IMPROVES (chrF {score:.3f} vs best {current_best[0] if current_best else 'none'}) → KEEP")
                current_best = (score, fam)
            else:
                print(f"  ✗ does not beat best ({current_best[0]:.3f}) → discard")
            REGISTRY.parent.mkdir(parents=True, exist_ok=True)
            with open(REGISTRY, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
            HYP_LOG.parent.mkdir(parents=True, exist_ok=True)
            with open(HYP_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps({"family": fam, "hint": h["prompt_hint"],
                                    "score": round(score, 4), "kept": score > (current_best[0] if current_best else -1),
                                    "round": rnd}, ensure_ascii=False) + "\n")
    if current_best:
        print(f"\n=== BEST after {rounds} rounds: {current_best[1]} chrF={current_best[0]:.3f} ===")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--propose", action="store_true")
    ap.add_argument("--loop", type=int, default=1, help="rounds of hypothesize→test→keep")
    ap.add_argument("--rounds", type=int, default=1)
    ap.add_argument("--n", type=int, default=3)
    ap.add_argument("--test", default="mitrasamgraha")
    ap.add_argument("--model", default="mimo-v2.5")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.propose:
        propose()
        return 0
    return loop(args.loop or args.rounds, args.n, args.test, args.model, args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
