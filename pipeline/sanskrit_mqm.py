#!/usr/bin/env python3
"""pipeline/sanskrit_mqm.py — the Sanskrit MQM error taxonomy + CHALLENGE-SET generator.

The blueprint's SaQE training material (visionadvice.md §6, §11): a Sanskrit-specific MQM error taxonomy,
and a generator that manufactures CONTROLLED BAD TRANSLATIONS (challenge sets) from good ones. This lets us
measure evaluator competence independently from translator competence, and gives training data for a
Sanskrit evaluator (SaQE).

The taxonomy distinguishes ordinary MT errors from Sanskrit-specific ones:
  - Accuracy: omission / unsupported addition / mistranslation
  - Segmentation: incorrect sandhi split
  - Morphology: wrong number/case/gender/person/tense/mood/voice
  - Syntax: wrong kāraka/argument relation
  - Compounding: wrong samāsa decomposition or semantic head
  - Scope: negation / restriction / quantification
  - Lexical semantics: wrong sense of a polysemous term
  - Coreference: implicit subjects / pronouns / ellipsis
  - Technical terminology: philosophical/ritual/grammatical term mistranslated
  - Poetic semantics: metaphor flattened / literalized
  - Textual structure: quotation/commentary boundary confusion
  - Style: register / readability (kept separate from factual adequacy)

Deterministic + stdlib. Writes challenge-set JSONL: each row = {source, good, bad, error_family, instruction}.

Usage:
  python3 pipeline/sanskrit_mqm.py --challenge --n 5     # generate challenge sets from the gold
  python3 pipeline/sanskrit_mqm.py --taxonomy            # print the error taxonomy
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))
OUT = ROOT / "data" / "challenge-sets"

# the Sanskrit MQM error taxonomy (the canonical closed set — don't invent new families)
TAXONOMY = {
    "ACCURACY_OMISSION": "a source element is dropped in the translation",
    "ACCURACY_ADDITION": "the translation adds content not in the source",
    "ACCURACY_MISTRANSLATION": "a source element is rendered incorrectly",
    "SEGMENTATION_SANDHI": "an incorrect sandhi split / word boundary",
    "MORPHOLOGY": "wrong number/case/gender/person/tense/mood/voice",
    "SYNTAX_KARAKA": "wrong kāraka/argument relation (who does what to whom)",
    "COMPOUND_SAMASA": "wrong samāsa decomposition or semantic head",
    "SCOPE_NEGATION": "negation / restriction / quantification scope is wrong",
    "LEXICAL_SENSE": "wrong sense of a polysemous term",
    "COREFERENCE": "implicit subject / pronoun / ellipsis resolved wrongly",
    "TECHNICAL_TERM": "philosophical/ritual/grammatical technical term mistranslated",
    "POETIC_METAPHOR": "metaphor / image flattened or wrongly literalized",
    "TEXTUAL_STRUCTURE": "quotation/commentary boundary confusion",
    "STYLE": "register or readability problem (separate from factual adequacy)",
}

# the perturbation → error-family → instruction map (how to manufacture a bad translation)
# each applies a KNOWN error family to a good translation, deterministically.
PERTURBATIONS = [
    ("negation", "SCOPE_NEGATION",
     "Perturb the translation so a negation marker is removed or inverted (a controlled bad translation)."),
    ("number", "MORPHOLOGY",
     "Perturb the translation so a number (singular/plural) is swapped (a controlled bad translation)."),
    ("technical", "TECHNICAL_TERM",
     "Perturb the translation so a technical term is mistranslated as a generic word (a controlled bad translation)."),
    ("metaphor", "POETIC_METAPHOR",
     "Perturb the translation so a metaphor is flattened to a literal statement (a controlled bad translation)."),
    ("speaker", "TEXTUAL_STRUCTURE",
     "Perturb the translation so the quoted speaker / quotation boundary is confused (a controlled bad translation)."),
]


def make_challenge(gold: str, family: str) -> str:
    """Return a controlled BAD translation of `gold` by applying the error family (deterministic heuristic)."""
    if family == "SCOPE_NEGATION":
        # remove a "not / no / never" if present, else add one
        if re.search(r"\b(not|no|never|nor)\b", gold, re.I):
            return re.sub(r"\b(not|no|never|nor)\b", "", gold, count=1, flags=re.I).strip()
        return "not " + gold if gold else gold
    if family == "MORPHOLOGY":
        # swap the last singular noun for a plural (or vice versa) — heuristic
        m = list(re.finditer(r"\b(\w+)\b", gold))
        if not m:
            return gold
        w = m[-1].group(1)
        if w.endswith("s"):
            new = w[:-1]
        else:
            new = w + "s"
        return gold[:m[-1].start()] + new + gold[m[-1].end():]
    if family == "TECHNICAL_TERM":
        return "the thing (term left generic) " + gold if gold else gold
    if family == "POETIC_METAPHOR":
        return gold  # heuristic placeholder; a model refines this
    if family == "TEXTUAL_STRUCTURE":
        return gold  # heuristic placeholder; a model refines this
    return gold


def generate_challenge_set(n: int) -> dict:
    """Generate challenge-set rows from the gold: {source, good, bad, error_family, instruction}."""
    from sanskrit_gold import clean_exemplars
    rows = [e for e in clean_exemplars() if e["work"] == "mitrasamgraha"][:n]
    OUT.mkdir(parents=True, exist_ok=True)
    out_file = OUT / "sanskrit-challenge-set.jsonl"
    count = 0
    with open(out_file, "w", encoding="utf-8") as f:
        for e in rows:
            src, gold = e["source"], e["gold"]
            # one controlled bad translation per family (deterministic)
            for _, family, instr in PERTURBATIONS:
                bad = make_challenge(gold, family)
                if bad and bad != gold:
                    rec = {"source": src, "good": gold, "bad": bad,
                           "error_family": family, "instruction": instr}
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    count += 1
    return {"challenges": count, "file": str(out_file)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--challenge", type=int, default=0)
    ap.add_argument("--taxonomy", action="store_true")
    args = ap.parse_args()
    if args.taxonomy:
        print("=== SANSKRIT MQM ERROR TAXONOMY (closed set) ===")
        for fam, desc in TAXONOMY.items():
            print(f"  {fam:24} {desc}")
    if args.challenge:
        r = generate_challenge_set(args.challenge)
        print(f"\n=== challenge set: {r['challenges']} controlled bad translations → {r['file']} ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
