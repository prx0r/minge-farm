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
# each applies a KNOWN error family to a good translation, deterministically (stdlib only).
# Covers ALL 14 families in TAXONOMY. Each returns a controlled bad translation (or None if not
# applicable to that particular gold string — the generator skips None rows).
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
    ("omission", "ACCURACY_OMISSION",
     "Perturb the translation by dropping a content element (a controlled bad translation)."),
    ("addition", "ACCURACY_ADDITION",
     "Perturb the translation by adding content not in the source (a controlled bad translation)."),
    ("mistranslation", "ACCURACY_MISTRANSLATION",
     "Perturb the translation so a source element is rendered incorrectly (a controlled bad translation)."),
    ("case_swap", "SYNTAX_KARAKA",
     "Perturb the translation so an agent/patient (who does what to whom) is swapped (a controlled bad translation)."),
    ("sense", "LEXICAL_SENSE",
     "Perturb the translation so a polysemous term is given the wrong sense (a controlled bad translation)."),
    ("coref", "COREFERENCE",
     "Perturb the translation so a pronoun / implicit subject refers to the wrong entity (a controlled bad translation)."),
    ("compound", "COMPOUND_SAMASA",
     "Perturb the translation so a compound / phrase is re-ordered to the wrong head (a controlled bad translation)."),
    ("sandhi", "SEGMENTATION_SANDHI",
     "Perturb the translation so a word boundary is split wrongly (a controlled bad translation)."),
    ("style", "STYLE",
     "Perturb the translation into a mismatched register (a controlled bad translation)."),
]

# adjective → antonym map (used by ACCURACY_MISTRANSLATION / LEXICAL_SENSE)
_ANTONYMS = {
    "good": "evil", "great": "small", "divine": "ordinary", "eternal": "temporary",
    "supreme": "inferior", "wise": "foolish", "pure": "impure", "many": "few",
    "whole": "partial", "bright": "dark", "true": "false", "final": "initial",
    "inner": "outer", "highest": "lowest", "all": "none", "beloved": "hated",
    "liberated": "bound", "auspicious": "inauspicious", "good": "wicked",
}

# words that signal a quotation boundary / speaker for TEXTUAL_STRUCTURE
_QUOTE_WORDS = ["said", "replied", "spoke", "asked", "declared", "says", "saying", "told"]


def _tokens(gold: str) -> list:
    return list(re.finditer(r"\b[\w'-]+\b", gold))


def _replace_word(gold: str, idx: int, new: str) -> str:
    m = _tokens(gold)[idx]
    return gold[:m.start()] + new + gold[m.end():]


def _swap_words(gold: str, i: int, j: int) -> str:
    toks = _tokens(gold)
    if i < 0 or j >= len(toks) or i >= len(toks) or j < 0:
        return None
    a, b = toks[i], toks[j]
    return gold[:a.start()] + b.group(0) + gold[a.end():b.start()] + a.group(0) + gold[b.end():]


def _last_clause(gold: str) -> str:
    # the text after the last comma, if any
    if "," in gold:
        return gold.split(",")[-1].strip()
    return None


def make_challenge(gold: str, family: str) -> str:
    """Return a controlled BAD translation of `gold` (deterministic stdlib heuristic), or None if not applicable."""
    toks = _tokens(gold)
    if not toks:
        return None
    n = len(toks)
    if family == "SCOPE_NEGATION":
        if re.search(r"\b(not|no|never|nor)\b", gold, re.I):
            return re.sub(r"\b(not|no|never|nor)\b", "", gold, count=1, flags=re.I).strip()
        return "not " + gold if gold else None
    if family == "MORPHOLOGY":
        # swap the LAST word's number (singular/plural) — a real, semantic number error
        w = toks[-1].group(0)
        new = w[:-1] if w.endswith("s") else (w + "s")
        return _replace_word(gold, n - 1, new)
    if family == "TECHNICAL_TERM":
        # genericize a capitalized/proper term if present, else prefix a generic gloss
        cap = [t for t in toks if t.group(0)[0].isupper()]
        if cap:
            return _replace_word(gold, toks.index(cap[0]), "the being")
        return "the thing (term left generic) " + gold if gold else None
    if family == "POETIC_METAPHOR":
        # flatten a likely metaphorical noun ("abode","flame","light","heart") to a literal synonym
        for kw in ["abode", "flame", "light", "heart", "lamp", "ocean"]:
            for t in toks:
                if t.group(0).lower() == kw:
                    return _replace_word(gold, toks.index(t), {
                        "abode": "building", "flame": "fire", "light": "lamp",
                        "heart": "organ", "lamp": "object", "ocean": "water",
                    }[kw])
        return None
    if family == "TEXTUAL_STRUCTURE":
        # swap the last quote-speaker to a different common name
        for t in toks:
            if t.group(0).lower() in _QUOTE_WORDS:
                # replace "X said" → "X asked" (boundary/perlocution confusion)
                return _replace_word(gold, toks.index(t), "asked" if t.group(0).lower() != "asked" else "said")
        return None
    if family == "ACCURACY_OMISSION":
        # drop the last clause (after the last comma) if present, else drop the last word
        last = _last_clause(gold)
        if last and len(toks) > 3:
            return gold[:gold.rindex(",")].rstrip(" ,")
        return gold[:toks[-1].start()].rstrip() if n > 1 else None
    if family == "ACCURACY_ADDITION":
        # append a spurious clause not in the source
        return (gold + ", and this was not stated in the original text").strip() if gold else None
    if family == "ACCURACY_MISTRANSLATION":
        # swap the first antonym-able adjective for its antonym
        for t in toks:
            w = t.group(0).lower()
            if w in _ANTONYMS:
                return _replace_word(gold, toks.index(t), _ANTONYMS[w])
        # fallback: swap the first non-stopword for its reverse
        if n > 1:
            w = toks[1].group(0)
            return _replace_word(gold, 1, w[::-1])
        return None
    if family == "SYNTAX_KARAKA":
        # swap the first two content nouns → agent/patient confusion
        return _swap_words(gold, 0, 1)
    if family == "LEXICAL_SENSE":
        # give a common polysemous word the wrong sense (use an antonym if known)
        for t in toks:
            w = t.group(0).lower()
            if w in _ANTONYMS:
                return _replace_word(gold, toks.index(t), _ANTONYMS[w])
        # fallback: swap the last two words
        return _swap_words(gold, n - 2, n - 1)
    if family == "COREFERENCE":
        # swap a possessive pronoun to the wrong referent (his/her/its → other)
        for t in toks:
            w = t.group(0).lower()
            if w in ("his", "her", "its", "their"):
                return _replace_word(gold, toks.index(t), {
                    "his": "her", "her": "his", "its": "their", "their": "its",
                }[w])
        return None
    if family == "COMPOUND_SAMASA":
        # re-order the first two adjacent content words → wrong compound head
        return _swap_words(gold, 0, 1)
    if family == "SEGMENTATION_SANDHI":
        # wrongly split a hyphenated compound / joined word
        for t in toks:
            if "-" in t.group(0):
                return _replace_word(gold, toks.index(t), t.group(0).replace("-", " "))
        return None
    if family == "STYLE":
        # shift register: prefix a colloquial filler (a style mismatch, kept separate from adequacy)
        return ("Like, " + gold) if gold else None
    return None


def generate_challenge_set(n: int) -> dict:
    """Generate challenge-set rows from the gold: {source, good, bad, error_family, instruction}.

    `n` = the target number of CHALLENGE ROWS (across all families). Rows that a family can't
    deterministically perturb (make_challenge returns None or identical) are skipped. Spreads across
    all 14 families so every error family is represented.
    """
    from sanskrit_gold import clean_exemplars
    exemplars = [e for e in clean_exemplars() if e["work"] == "mitrasamgraha"]
    OUT.mkdir(parents=True, exist_ok=True)
    out_file = OUT / "sanskrit-challenge-set.jsonl"
    per_family = {}
    count = 0
    with open(out_file, "w", encoding="utf-8") as f:
        for e in exemplars:
            if count >= n:
                break
            src, gold = e["source"], e["gold"]
            for _, family, instr in PERTURBATIONS:
                if count >= n:
                    break
                # don't let one family dominate; cap each family's contribution
                if per_family.get(family, 0) >= max(4, n // len(PERTURBATIONS)):
                    continue
                bad = make_challenge(gold, family)
                if bad and bad != gold and bad.strip() != gold.strip():
                    rec = {"source": src, "good": gold, "bad": bad,
                           "error_family": family, "instruction": instr}
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    count += 1
                    per_family[family] = per_family.get(family, 0) + 1
    return {"challenges": count, "file": str(out_file), "per_family": per_family}


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
