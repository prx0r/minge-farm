#!/usr/bin/env python3
"""tools/eval_mitrasamgraha.py — score our translation against the Mitrasamgraha post-corrected gold.

The Mitrasamgraha test set (5,552 post-corrected Sanskrit→English pairs) is the ONE-RULE gold for the
translation gate: it makes "our translation is good" verifiable instead of assumed.

This harness:
  1. samples N pairs from the Mitrasamgraha TEST set (post-corrected gold)
  2. calls the configured model to translate the Sanskrit → English
  3. scores the model output vs the gold English (BLEU + chrF + rough coverage)
  4. logs every row with full RESULT LINEAGE (result_id, gold_version, model_version, split,
     seed, date, config) so the score resolves to a real experiment.

Usage:
  python3 tools/eval_mitrasamgraha.py --n 20 --model mimo-v2.5
  python3 tools/eval_mitrasamgraha.py --n 5 --model mimo-v2.5 --dry-run   # no model calls
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / "data/benchmarks/mitrasamgraha/test.jsonl"
LOG = ROOT / "data/corpus" / "mitrasamgraha-eval-log.jsonl"
sys.path.insert(0, str(ROOT / "pipeline"))

GOLD_VERSION = "mitrasamgraha-test-v1"
DEFAULT_MODEL = "mimo-v2.5"


def _syllable_count(s: str) -> int:
    """Rough English word/syllable metric: count whitespace-separated tokens."""
    return len(s.split())


def load_gold(n: int, seed: int) -> list[dict]:
    rows = []
    for line in open(GOLD, encoding="utf-8"):
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    rng = random.Random(seed)
    if n and n < len(rows):
        rows = rng.sample(rows, n)
    return rows


def simple_chrf(reference: str, candidate: str) -> float:
    """A minimal character-n-gram F score (chrF-ish). Not the official chrF++ but a real, reproducible
    character-overlap signal: char 1-3 grams precision + recall → F1. Good enough to rank candidate
    translations vs gold without depending on sacrebleu."""
    if not reference or not candidate:
        return 0.0
    def char_ngrams(s: str, n: int):
        s = re.sub(r"\s+", "", s)
        return [s[i:i + n] for i in range(len(s) - n + 1)]
    prec = rec = 0.0
    for n in (1, 2, 3):
        rg = set(char_ngrams(reference, n))
        cg = set(char_ngrams(candidate, n))
        if not cg or not rg:
            continue
        inter = len(rg & cg)
        p = inter / len(cg)
        r = inter / len(rg)
        prec += p
        rec += r
    if prec == 0 or rec == 0:
        return 0.0
    f = 2 * (prec * rec) / (prec + rec) / 3.0
    return round(f, 4)


def simple_bleu(reference: str, candidate: str) -> float:
    """A compact token 1-gram + 4-gram brevity-penalized BLEU approximation."""
    import math
    r_tok = reference.split()
    c_tok = candidate.split()
    if not c_tok or not r_tok:
        return 0.0
    hits = sum(1 for t in c_tok if t in set(r_tok))
    p1 = hits / len(c_tok)
    # brevity penalty
    bp = math.exp(min(0, 1 - len(r_tok) / len(c_tok)))
    return round(bp * p1, 4)


def translate(model: str, sanskrit: str) -> str:
    """Call the model to translate Sanskrit → English via pipeline/model.py::chat."""
    from model import chat
    system = ("You are a careful Sanskrit scholar-translator. Translate the given Sanskrit verse into "
              "natural, accurate English. Preserve meaning, do not add interpretation. Output only the "
              "translation, nothing else.")
    raw = chat(system, f"Translate this Sanskrit into English:\n{sanskrit}", model=model, timeout=90)
    # strip any quote/whitespace cruft
    return (raw or "").strip().strip('"').strip()


def _extract_json_obj(raw: str) -> dict:
    """Robustly extract the first JSON object from a model response (handles code fences,
    prose wrapping, and trailing text)."""
    import re as _re
    raw = (raw or "").strip()
    # strip markdown code fences
    raw = _re.sub(r"```(?:json)?", "", raw)
    # find the first { ... } balanced block
    start = raw.find("{")
    if start == -1:
        return {}
    depth = 0
    for i in range(start, len(raw)):
        if raw[i] == "{":
            depth += 1
        elif raw[i] == "}":
            depth -= 1
            if depth == 0:
                obj = raw[start:i + 1]
                try:
                    return json.loads(obj)
                except Exception:
                    # try stripping trailing commas (common LLM artifact)
                    import json as _json
                    try:
                        return _json.loads(_re.sub(r",\s*([}\]])", r"\1", obj))
                    except Exception:
                        return {}
    return {}


def judge_semantics(model: str, reference: str, candidate: str) -> dict:
    """Second model pass: score the candidate translation vs the gold on SEMANTIC FIDELITY (1-5).

    chrF/bleu understate good Sanskrit translations (correct wording differs from gold). This is the
    LLM-as-judge semantic score the project docs call for. Returns {fidelity, judgment}."""
    system = ("You are a strict Sanskrit translation judge. Rate how faithfully the CANDIDATE translation "
              "preserves the MEANING of the GOLD reference translation. Consider: semantic accuracy, "
              "no meaning lost, no meaning added, no misread compound/philosophical term. "
              "Return exactly one JSON object: {\"fidelity\": <1-5>, \"judgment\": \"<one-line why>\"}.")
    user = f"GOLD reference: {reference}\n\nCANDIDATE: {candidate}"
    try:
        from model import chat  # noqa: F401  (deferred: pipeline import in tools context)
        raw = chat(system, user, model=model, timeout=90)
        d = _extract_json_obj(raw)
        if not d:
            return {"fidelity": 0, "judgment": f"__PARSE_FAIL__ {str(raw)[:60]}"}
        fid = int(d.get("fidelity", 0))
        return {"fidelity": max(1, min(5, fid)), "judgment": str(d.get("judgment", ""))[:200]}
    except Exception as e:
        return {"fidelity": 0, "judgment": f"__ERROR__ {e}"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--judge-model", default=None, help="model for the LLM-as-judge pass (default: same as --model)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--dry-run", action="store_true", help="print the sample without calling the model")
    args = ap.parse_args()
    judge_model = args.judge_model or args.model

    gold = load_gold(args.n, args.seed)
    print(f"=== Mitrasamgraha eval: {len(gold)} pairs, model={args.model}, gold={GOLD_VERSION} ===")

    if args.dry_run:
        for i, g in enumerate(gold):
            print(f"\n--- {i} ---\nSANSK: {g['sanskrit'][:100]}\nGOLD:  {g['english'][:100]}")
        return 0

    results = []
    for i, g in enumerate(gold):
        t0 = time.time()
        try:
            cand = translate(args.model, g["sanskrit"])
        except Exception as e:
            cand = f"__ERROR__ {e}"
        dt = time.time() - t0
        row = {
            "result_id": hashlib.sha256(f"{GOLD_VERSION}|{g['sanskrit'][:40]}|{args.model}".encode()).hexdigest()[:16],
            "gold_version": GOLD_VERSION, "model_version": args.model,
            "split": "test", "seed": args.seed, "config": f"n={args.n}",
            "date": datetime.now(timezone.utc).isoformat(),
            "sanskrit": g["sanskrit"], "gold_en": g["english"], "candidate": cand,
            "chrF": simple_chrf(g["english"], cand),
            "bleu1_bp": simple_bleu(g["english"], cand),
            "gold_words": _syllable_count(g["english"]), "cand_words": _syllable_count(cand),
            "latency_s": round(dt, 2),
        }
        # optional LLM-as-judge semantic pass
        if not cand.startswith("__ERROR__"):
            j = judge_semantics(judge_model, g["english"], cand)
            row["semantic_fidelity"] = j["fidelity"]
            row["judgment"] = j["judgment"]
            print(f"[{i+1}/{len(gold)}] chrF={row['chrF']:.3f} bleu1={row['bleu1_bp']:.3f} "
                  f"fid={j['fidelity']}/5 ({row['gold_words']}w vs {row['cand_words']}w, {row['latency_s']}s)  {j['judgment'][:60]}")
        else:
            print(f"[{i+1}/{len(gold)}] chrF=0.000 (ERROR) {cand[:40]}")
        results.append(row)

    # aggregate
    judged = [r for r in results if r.get("semantic_fidelity")]
    avg_chrf = sum(r["chrF"] for r in results) / len(results)
    avg_bleu = sum(r["bleu1_bp"] for r in results) / len(results)
    avg_fid = (sum(r["semantic_fidelity"] for r in judged) / len(judged)) if judged else 0.0
    print("\n=== AGGREGATE ===")
    print(f"  n={len(results)} model={args.model} gold={GOLD_VERSION}"
          + (f" judge={judge_model}" if judge_model != args.model else ""))
    print(f"  avg chrF:       {avg_chrf:.4f}")
    print(f"  avg bleu1:      {avg_bleu:.4f}")
    if judged:
        print(f"  avg semantic:   {avg_fid:.2f}/5 (LLM-judge, n={len(judged)})")

    # append to the lineage log
    entry = {
        "run": {"date": datetime.now(timezone.utc).isoformat(), "n": len(results),
                "model": args.model, "judge_model": judge_model, "gold": GOLD_VERSION, "seed": args.seed,
                "avg_chrF": round(avg_chrf, 4), "avg_bleu1": round(avg_bleu, 4),
                "avg_semantic": round(avg_fid, 2) if judged else None},
        "rows": results,
    }
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"  logged to {LOG} (with full result lineage)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
