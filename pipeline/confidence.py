#!/usr/bin/env python3
"""pipeline/confidence.py — the confidence feature-vector + multidimensional proof score (§7, §20).

The blueprint §7: DON'T train a model to estimate vague "confidence". Define Y=1 iff a Sanskrit expert
judges no major/critical semantic error, then collect a FEATURE VECTOR z and learn P(Y=1|z) on human data.
This module builds the feature vector from the signals we HAVE (the ones a CPU box can compute), and
defines the multidimensional proof-score schema (§20) that the UI shows instead of one fuzzy number.

The feature vector z (the §7 list):
  q_xCOMET · q_MetricX · q_SaQE · N_major · N_critical · A_alignment · M_morph · R_retrieval ·
  D_ensemble · C_crosslingual · B_backtranslation
  (the neural ones are 'unavailable' until GPU; the deterministic ones are computed now)

Deterministic + stdlib. CPU-computable features are filled; the rest marked unavailable.

Usage:
  from confidence import feature_vector, PROOF_SCORE
  z = feature_vector(source, candidate, gold, candidates=[...], parallels=[...])
  # z is the input to the (future) calibrated model
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))

# the full §7 feature vector (each feature -> status)
FEATURES = [
    "q_xCOMET", "q_MetricX", "q_SaQE", "N_major", "N_critical",
    "A_alignment", "M_morph", "R_retrieval", "D_ensemble", "C_crosslingual", "B_backtranslation",
]


def feature_vector(*, source: str, candidate: str, gold: str = "",
                   candidates: list | None = None, parallels: list | None = None) -> dict:
    """Build the confidence feature vector z. CPU-computable features are filled; neural ones are not."""
    from experiment_lab import chrF
    from renderer import candidate_disagreement

    z = {}
    # neural features — honest 'unavailable' until a GPU/torch box (never fabricate a number)
    for f in ("q_xCOMET", "q_MetricX", "q_SaQE", "A_alignment", "M_morph", "R_retrieval",
              "B_backtranslation"):
        z[f] = {"value": None, "status": "unavailable", "note": "needs GPU/embedding model"}
    # error counts — unavailable until an error-span detector (xCOMET/SaQE) exists
    z["N_major"] = {"value": None, "status": "unavailable", "note": "needs error-span detector"}
    z["N_critical"] = {"value": None, "status": "unavailable", "note": "needs error-span detector"}

    # D_ensemble = candidate disagreement (CPU-computable NOW, §14)
    cands = [{"valid": True, "candidate": c} for c in (candidates or [])]
    disc = candidate_disagreement(cands)
    z["D_ensemble"] = {"value": disc["disagreement"], "status": "available",
                       "verdict": disc["verdict"]}

    # C_crosslingual = parallel agreement (CPU-computable via MITRA parallels, §3)
    if parallels:
        # crude agreement: chrF between the candidate and any English parallel (placeholder for the
        # cross-lingual semantic check — the real one needs MITRA-E embeddings on GPU)
        aggr = [chrF(candidate, p.get("text", "")) for p in parallels if p.get("text")]
        z["C_crosslingual"] = {"value": round(sum(aggr)/len(aggr), 3) if aggr else None,
                               "status": "available" if aggr else "unavailable",
                               "n_parallels": len(parallels)}
    else:
        z["C_crosslingual"] = {"value": None, "status": "unavailable", "note": "no parallels"}
    return z


# the multidimensional proof score (§20) — the UI shows ALL of these, not one fuzzy number
def proof_score(*, source: str, candidate: str, gold: str = "",
                candidates: list | None = None, parallels: list | None = None) -> dict:
    """The multidimensional proof score (§20): separate signals, each expandable."""
    from translation_proof import verify_translation
    from experiment_lab import chrF as _chrF
    proof = verify_translation(source, candidate, gold=gold)
    return {
        "deterministic_gate": proof["deterministic_gate"],
        "source_semantic_coverage": {"value": None, "status": "unavailable",
                                     "note": "needs alignment kernel"},
        "morphological_accounting": {"value": None, "status": "unavailable",
                                     "note": "needs ByT5/Vidyut"},
        "candidate_agreement": feature_vector(source=source, candidate=candidate,
                                              candidates=candidates)["D_ensemble"],
        "critical_errors_detected": {"value": None, "status": "unavailable",
                                     "note": "needs error-span detector"},
        "proof_gate": proof["deterministic_gate"],
        "gold_chrF": round(_chrF(gold, candidate), 3) if gold else None,
        "decision": "accepted" if proof["deterministic_gate"] == "PASS" else "review",
    }


if __name__ == "__main__":
    z = feature_vector(source="kramasadbhava namaḥ śivāya", candidate="Homage to Shiva",
                       gold="Homage to Shiva",
                       candidates=["Homage to Shiva", "Obeisance to Lord Shiva"],
                       parallels=[{"lang": "bo", "text": "Obeisance to Shiva"}])
    print("=== confidence feature vector z ===")
    for f in FEATURES:
        print(f"  {f:18} {z[f]}")
    print("\n=== multidimensional proof score ===")
    ps = proof_score(source="kramasadbhava namaḥ śivāya", candidate="Homage to Shiva", gold="Homage to Shiva")
    for k, v in ps.items():
        print(f"  {k:26} {v}")
