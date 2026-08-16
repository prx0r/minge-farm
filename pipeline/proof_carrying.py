#!/usr/bin/env python3
"""pipeline/proof_carrying.py — the PROOF-CARRYING translation evidence object (§12 of visionadvice.md).

The blueprint's §12: "Don't merely store the answer. Store enough intermediate evidence that another
model—or eventually a human Sanskritist—can attack the answer." This module builds the immutable evidence
artifact every translation ships with, so a translation is auditable, not just asserted.

The evidence object (the §12 table):
  source · segmentation · morphology · syntax · alignment · lexical evidence · parallel evidence ·
  intertextual evidence · candidate distribution · evaluator evidence · terminology · uncertainty ·
  provenance · decision

Deterministic + stdlib. Each field is filled by a lab kernel when available (proof gate, run_recorder,
re-render candidates, MITRA parallels); empty where the instrument doesn't exist yet. The result is a
content-addressed artifact anyone can inspect.

Usage:
  from proof_carrying import build_evidence_object, PROOF_FIELDS
  ev = build_evidence_object(source, candidate, gold, run_signature, candidates=[...])
  # ev is the immutable, inspectable artifact
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))

# the canonical proof-carrying evidence fields (the blueprint §12 table — the contract)
PROOF_FIELDS = [
    "source", "segmentation", "morphology", "syntax", "alignment",
    "lexical_evidence", "parallel_evidence", "intertextual_evidence",
    "candidate_distribution", "evaluator_evidence", "terminology",
    "uncertainty", "provenance", "decision",
]


def _sha(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def build_evidence_object(*, source: str, candidate: str, gold: str = "",
                          run_signature: str = "", candidates: list | None = None,
                          parallels: list | None = None) -> dict:
    """Build the proof-carrying evidence artifact for one translation.

    Fills every field the current instruments support; leaves an explicit 'unavailable' marker where a
    GPU/human instrument isn't built yet (honest — not fabricated).
    """
    from translation_proof import verify_translation
    proof = verify_translation(source, candidate, gold=gold)

    ev = {
        # the immutable core
        "source": {"text": source, "hash": _sha(source)},
        "candidate": {"text": candidate, "hash": _sha(candidate)},

        # the proof gate (deterministic, always available)
        "deterministic_gate": proof["deterministic_gate"],
        "blocking": proof["blocking"],

        # §12 fields — filled where an instrument exists
        "segmentation": {"status": "unavailable", "note": "needs ByT5-Sanskrit/Vidyut (GPU or import)"},
        "morphology": {"status": "unavailable", "note": "needs ByT5/Vidyut/dcs-sh (import available)"},
        "syntax": {"status": "unavailable", "note": "needs dependency parse (ByT5-Sanskrit)"},
        "alignment": {"status": "unavailable", "note": "needs an alignment kernel"},
        "lexical_evidence": {"status": "unavailable", "note": "needs the lemma->sense map"},
        # parallel + intertextual evidence (MITRA cross-canon — built)
        "parallel_evidence": {"n_parallels": len(parallels or []),
                              "parallels": (parallels or [])[:5]},
        "intertextual_evidence": {"status": "unavailable",
                                  "note": "needs the DCS intertextual index"},
        # candidate distribution (re-render — built)
        "candidate_distribution": {"n_candidates": len(candidates or []),
                                   "candidates": (candidates or [])[:5]},
        "evaluator_evidence": {"status": "unavailable", "note": "needs xCOMET/SaQE (GPU)"},
        "terminology": {"status": "unavailable", "note": "needs the glossary + lemma map"},
        "uncertainty": {"status": "unavailable", "note": "needs the calibrated + conformal layer (GPU)"},
        "provenance": {"run_signature": run_signature, "method": "proof_carrying.py",
                       "schema_version": "0.1.0"},
        "decision": "accepted" if proof["deterministic_gate"] == "PASS" else "review",
    }
    ev["artifact_hash"] = _sha(ev)
    return ev


if __name__ == "__main__":
    ev = build_evidence_object(
        source="kramasadbhava namaḥ śivāya", candidate="Homage to Shiva",
        gold="Homage to Shiva", run_signature="abc123",
        candidates=["Homage to Shiva", "Obeisance to Lord Shiva"],
        parallels=[{"lang": "bo", "text": "(parallel sample)"}])
    print("=== proof-carrying evidence artifact ===")
    print(f"  gate: {ev['deterministic_gate']} | decision: {ev['decision']}")
    print(f"  artifact_hash: {ev['artifact_hash'][:16]}")
    print(f"  fields: {len(PROOF_FIELDS) + 5} (source/candidate/gate/parallel/candidate-dist/provenance/decision)")
    print(f"  unavailable (needs GPU): {[f for f in PROOF_FIELDS if isinstance(ev.get(f), dict) and ev[f].get('status')=='unavailable']}")
