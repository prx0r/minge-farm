#!/usr/bin/env python3
"""server_p1.py — Pāṭala 1 server: Audit + Translate + Bench

Audit: instant (pure Python, zero tokens)
Translate: 10-25s (calls mimo-v2.5 via API)
Bench: batched (not all 5,601 at once)

Usage:
  python3 server_p1.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "pipeline"))

try:
    from fastapi import FastAPI
    from pydantic import BaseModel
    import uvicorn
    app = FastAPI(title="Pāṭala 1 — Verified Translation Network")
except ImportError:
    print("pip install fastapi uvicorn")
    sys.exit(1)


class AuditRequest(BaseModel):
    source: str
    candidate: str

class TranslateRequest(BaseModel):
    source: str
    max_tokens: int = 30

class BenchRequest(BaseModel):
    n: int = 5


@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0", "products": ["audit", "translate", "bench"]}


@app.post("/audit")
def audit(req: AuditRequest):
    """Instant audit — pure Python, zero tokens."""
    from pipeline.translation_proof import verify_translation
    start = time.time()
    proof = verify_translation(req.source, req.candidate)
    checks = {k: {"PASS": v["PASS"], "reason": v["reason"]} for k, v in proof["checks"].items()}
    return {
        "product": "audit",
        "checks": checks,
        "gate": proof["deterministic_gate"],
        "blocking": proof.get("blocking", []),
        "lineage": proof.get("lineage", {}),
        "duration_s": round(time.time() - start, 3),
        "tokens": 0,
    }


@app.post("/translate")
def translate(req: TranslateRequest):
    """Translate Sanskrit → English via mimo-v2.5."""
    from pipeline.model import chat
    start = time.time()
    translation = chat(
        'You are a Sanskrit-to-English translator. Output ONLY the English translation, no explanation.',
        req.source,
        max_tokens=req.max_tokens,
    )
    t_time = time.time() - start

    # Auto-audit
    from pipeline.translation_proof import verify_translation
    proof = verify_translation(req.source, translation)

    return {
        "product": "translate",
        "source": req.source,
        "translation": translation.strip(),
        "gate": proof["deterministic_gate"],
        "checks": {k: v["PASS"] for k, v in proof["checks"].items()},
        "duration_s": round(t_time, 3),
    }


@app.post("/bench")
def bench(req: BenchRequest):
    """Run benchmark on gold subset."""
    from pipeline.sanskrit_gold import clean_exemplars
    from pipeline.experiment_lab import bleu1
    from pipeline.translation_proof import verify_translation
    from pipeline.model import chat

    gold = clean_exemplars()[:req.n]
    results = []
    total_tokens = 0

    for g in gold:
        src = g["source"]
        gold_text = g["gold"]

        # Translate
        start = time.time()
        trans = chat(
            'You are a Sanskrit-to-English translator. Output ONLY the translation.',
            src, max_tokens=30,
        )
        t_time = time.time() - start

        # Score
        b = bleu1(gold_text, trans.strip())
        proof = verify_translation(src, trans)
        gate = proof["deterministic_gate"]

        results.append({
            "source": src[:50],
            "gold": gold_text[:50],
            "translation": trans.strip()[:50],
            "bleu": round(b, 4),
            "gate": gate,
        })

    avg_bleu = sum(r["bleu"] for r in results) / len(results) if results else 0
    pass_rate = sum(1 for r in results if r["gate"] == "PASS") / len(results) if results else 0

    return {
        "product": "bench",
        "n": len(results),
        "avg_bleu": round(avg_bleu, 4),
        "pass_rate": round(pass_rate, 3),
        "results": results,
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8903)
