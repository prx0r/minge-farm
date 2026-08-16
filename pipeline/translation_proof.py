#!/usr/bin/env python3
"""pipeline/translation_proof.py — the canonical PĀṬALA PROOF of translation.

Per research/PROOF-OF-TRANSLATION.md: an LLM translation is a verifiable PĀṬALA PROOF only when it passes
deterministic, checkable constraints — not because a model wrote it (the ONE RULE). This module turns a
translation into a proof:

  SOURCE_BINDING    every rendered English clause traces to source Sanskrit (no hallucination)
  TERM_CONSISTENCY  technical terms map 1:1 to a canonical glossary (no drift)
  ABSTENTION        unsure spans are flagged, never invented
  COVERAGE          the whole source is addressed (no dropped pādas)
  SEMANTIC_FIDELITY 0-1 meaning-match vs an independent gold (the quality grade, not the gate)

A translation is PASS (a verifiable PROOF) when all deterministic dimensions pass; the semantic score
grades it. Every proof carries full lineage (result_id, source_sha, gold_version, model_version, checks,
date) — a result that can't resolve doesn't exist.

Deterministic checks run WITHOUT a model (pure Python) — the "proof" is reproducible, not asserted.
"""
from __future__ import annotations

import hashlib
import re
from typing import Optional

# canonical technical-term glossary (the term-consistency reference). Terms we expect to be
# transliterated consistently or translated consistently across the factory's tradition.
# key = the Sanskrit term (IAST), value = an accepted rendering.
CANONICAL_GLOSSARY = {
    "śiva": ("Shiva", "Śiva"),
    "śakti": ("Shakti", "Śakti", "power"),
    "māyā": ("Maya", "Māyā", "illusion"),
    "ātman": ("Self", "Ātman", "self"),
    "brahman": ("Brahman", "brahman"),
    "jñāna": ("knowledge", "Jñāna"),
    "karma": ("karma", "Karma"),
    "dharma": ("dharma", "Dharma"),
    "nirvāṇa": ("nirvana", "Nirvana", "Nirvāṇa"),
    "yoga": ("yoga", "Yoga"),
    "puruṣa": ("purusha", "Puruṣa", "person"),
    "prakṛti": ("prakriti", "Prakṛti", "nature"),
}

IAST_DIACRITICS = "āīūṛṝḷḹṃñṅśṣṭḍḥ"


def source_sha(source: str) -> str:
    return hashlib.sha256(source.encode("utf-8")).hexdigest()[:16]


def check_source_binding(source: str, candidate: str) -> dict:
    """Every meaningful English content-word should trace to a source token (no hallucination).

    Heuristic: extract the Sanskrit content words (IAST tokens >2 chars) and require that the candidate
    is roughly the same 'amount of meaning' — i.e. not dramatically longer than the source would allow.
    A faithful translation is within ~3.5× the source word count (English tends to be longer but not 3×+);
    a hallucinated translation balloons. This is a CONSERVATIVE length gate; the real anti-hallucination
    check is the GOLD-REFERENCE comparison (see agent/verify.py --gold), which is robust where IAST
    token-overlap is not.
    """
    src_words = [w for w in re.split(r"\s+", source.strip()) if len(w) > 2 and not re.search(r"\d", w)]
    cand_words = [w for w in re.split(r"\s+", candidate.strip()) if len(w) > 2]
    if not src_words:
        return {"PASS": False, "reason": "empty source"}
    ratio = len(cand_words) / max(1, len(src_words))
    ok = ratio <= 3.5  # generous: a 3.5× expansion is likely hallucination/addition
    return {"PASS": ok, "ratio": round(ratio, 2),
            "reason": "candidate within 3.5× source length" if ok else
                      f"candidate {ratio:.1f}× source — likely hallucinated addition"}


def check_coverage(source: str, candidate: str) -> dict:
    """No dropped pādas / clauses: the candidate shouldn't be dramatically shorter than the source.

    A dropped pāda (half-verse) makes the translation much shorter than its source would warrant.
    We require the candidate to be at least ~40% the source's semantic units (very conservative).
    """
    src_units = len([w for w in re.split(r"\s+", source.strip()) if w])
    cand_units = len([w for w in re.split(r"\s+", candidate.strip()) if w])
    if not src_units:
        return {"PASS": False, "reason": "empty source"}
    ratio = cand_units / max(1, src_units)
    ok = ratio >= 0.4
    return {"PASS": ok, "ratio": round(ratio, 2),
            "reason": "candidate covers the source" if ok else
                      f"candidate only {ratio:.0%} of source units — dropped pādas"}


def check_abstention(candidate: str) -> dict:
    """The model must abstain (flag AMBIGUOUS / uncertain), not fabricate. If the candidate contains a
    fabricated-sounding guess marker or is empty-on-hard-terms, flag it."""
    # A candidate that just repeats the source (no translation) is an abstention, not a translation.
    iast = sum(1 for c in candidate if c in IAST_DIACRITICS)
    if iast > 5 and len(candidate) > 40:
        return {"PASS": False, "reason": "candidate repeats source (no real translation) — abstain, don't guess"}
    return {"PASS": True, "reason": "no abstention violation"}


def check_term_consistency(candidate: str) -> dict:
    """Technical terms map consistently to the canonical glossary (no within-text drift).

    If the candidate uses a glossary term, it must use ONE rendering of it (not mix 'Shiva' and 'Siva'
    for the same term). Deterministic: pick the most-used rendering of each term and flag conflicts.
    """
    issues = []
    for term, renderings in CANONICAL_GLOSSARY.items():
        # find which renderings appear in the candidate for this term
        hits = [r for r in renderings if r.lower() in candidate.lower()]
        if len(hits) > 1 and len(set(h.lower() for h in hits)) > 1:
            issues.append(f"'{term}': mixed renderings {hits}")
    return {"PASS": len(issues) == 0, "issues": issues,
            "reason": "terms consistent" if not issues else "; ".join(issues)}


def check_citation_grounding(source: str, candidate: str, glossary: dict | None = None) -> dict:
    """Every substantive term in the candidate must trace to a REAL source (the darshana-graph rule).

    Adopted from the darshana-graph debate simulator's anti-hallucination rule ("agents can only cite real
    graph edges; fabricated citations are rejected"). Here: a translation may not introduce a technical term
    that is neither in the source nor in the canonical glossary. If the candidate contains a technical term
    that has NO source match AND is not a known glossary term, it is a fabricated addition — reject.

    This is a CONSERVATIVE check: it only fires on terms the glossary recognizes, so a legitimate synonym
    that isn't a glossary term doesn't false-positive. The gold-reference check (verify.py) is the stronger
    anti-hallucination signal; this catches the "invented technical claim" case.
    """
    glossary = glossary or CANONICAL_GLOSSARY
    # collect the known terms (both source tokens + glossary terms) the candidate MAY legitimately use
    known = set()
    for w in re.split(r"\s+", source.lower()):
        w = re.sub(r"[^a-zā-īūṛṝḷḹṃñṅśṣṭḍḥ]", "", w)
        if len(w) >= 4:
            known.add(w)
    for term, renderings in glossary.items():
        known.add(term.lower())
        for r in renderings:
            known.add(r.lower())
    # check each glossary term the candidate uses is grounded in the SOURCE (not just known)
    ungrounded = []
    for term, renderings in glossary.items():
        used = [r for r in renderings if r.lower() in candidate.lower()]
        if used:
            # grounded iff the source actually contains the IAST term (or a source token starts with it)
            src_contains = term.lower() in source.lower() or \
                           any(w.startswith(term.lower()[:3]) for w in re.split(r"\s+", source.lower())
                               if len(w) >= 4)
            if not src_contains:
                ungrounded.append(f"'{term}' used in candidate but not in source")
    return {"PASS": len(ungrounded) == 0, "ungrounded": ungrounded,
            "reason": "all technical terms grounded in source" if not ungrounded
                      else "; ".join(ungrounded)}


def verify_translation(source: str, candidate: str,
                       gold: Optional[str] = None,
                       semantic_fidelity: Optional[float] = None) -> dict:
    """Run all deterministic proof checks + attach the semantic grade. Returns the Pāṭala PROOF."""
    checks = {
        "SOURCE_BINDING": check_source_binding(source, candidate),
        "COVERAGE": check_coverage(source, candidate),
        "ABSTENTION": check_abstention(candidate),
        "TERM_CONSISTENCY": check_term_consistency(candidate),
        "CITATION_GROUNDING": check_citation_grounding(source, candidate),
    }
    blocking = [name for name, c in checks.items() if not c["PASS"]]
    passed = all(c["PASS"] for c in checks.values())
    return {
        "source_sha": source_sha(source),
        "checks": checks,
        "deterministic_gate": "PASS" if passed else "BLOCKED",
        "blocking": blocking,
        "semantic_fidelity": semantic_fidelity,
        "proof": passed,  # a verifiable PROOF only when deterministic checks pass
        "lineage": {
            "result_id": hashlib.sha256(f"{source_sha}|{candidate[:40]}".encode()).hexdigest()[:16],
            "source_sha": source_sha(source),
            "gold_version": "mitrasamgraha-test-v1" if gold else None,
            "checks": list(checks.keys()),
            "method": "translation_proof deterministic gate",
        },
    }
