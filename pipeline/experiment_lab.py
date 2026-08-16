#!/usr/bin/env python3
"""pipeline/experiment_lab.py — the TRANSLATION SCIENCE LAB (the experiment framework).

Per `domains/translation/LAB.md` (smellycock): make a hypothesis per layer → run it on a FIXED test set
under a CONFIG → measure → compare → keep the winner. Every run is a named, labeled experiment stored
durably in the registry + comparable via --report.

The lab runs on the REAL gold data:
  - kramasadbhava gold_records (23) — the deterministic fixed test set (source_text → gold stages)
  - IPVV published passages (55) — the C1 exemplars (source → l2_text) for the control gold
  - Mitrasamgraha test (5,552) — the post-corrected translation gold (source → english)

Experiment naming (per spec): EXP-<LAYER>-<config_key>-<data_hash>-<ts>

Registry (the truth): data/corpus/registries/experiments.jsonl (streamed append).

Quality axis: chrF + bleu (surface) + semantic_fidelity (LLM-judge 0-1, optional) + proof checks.

Usage:
  python3 pipeline/experiment_lab.py --list-configs
  python3 pipeline/experiment_lab.py --layer L2 --config l2-flash --n 5 --dry-run     # no model calls
  python3 pipeline/experiment_lab.py --layer L2 --config l2-flash --n 5               # real run
  python3 pipeline/experiment_lab.py --report                                          # compare logged
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))

REGISTRY = ROOT / "data" / "corpus" / "registries" / "experiments.jsonl"
REPORTS = ROOT / "data" / "corpus" / "experiment-reports"
GOLD_RECORDS = ROOT / "pipeline" / "gold_records"
IPVV_GOLDS = ROOT / "data" / "published" / "ipvv"
MITRA_TEST = ROOT / "data" / "benchmarks" / "mitrasamgraha" / "test.jsonl"

DEFAULT_MODEL = "deepseek-v4-flash"

# the fixed test-set sources the lab can score against (control variable)
TEST_SOURCES = {
    "kramasadbhava": {  # the spec's fixed test work
        "label": "kramasadbhava gold_records (23) — deterministic",
        "load": lambda: _load_kramasadbhava(),
    },
    "ipvv": {
        "label": "IPVV published C1 passages (55) — the scholarly control",
        "load": lambda: _load_ipvv(),
    },
    "ipvv-trunc": {
        "label": "IPVV passages truncated to 400 chars (usable for candidate production)",
        "load": lambda: _load_ipvv(max_src_chars=400),
    },
    "mitrasamgraha": {
        "label": "Mitrasamgraha test (5,552) — the post-corrected translation gold",
        "load": lambda: _load_mitra(),
    },
}


def _register_frontier():
    """Register the imported frontier benchmark datasets (Sāmayik, Itihāsa) as test sources."""
    try:
        from frontier_gold import load_frontier, TEST_SETS
    except Exception:
        return
    for name, cfg in TEST_SETS.items():
        TEST_SOURCES[f"frontier:{name}"] = {
            "label": cfg["label"],
            "load": lambda name=name: load_frontier(name),
        }


_register_frontier()

# the config / hypothesis matrix (per LAB.md §3)
CONFIGS = {
    "l2-flash": {"layer": "L2", "model": "deepseek-v4-flash", "hypothesis": "flash baseline L2"},
    "l2-pro": {"layer": "L2", "model": "deepseek-v4-pro", "hypothesis": "pro L2 (quality-critical)"},
    "t1-flash": {"layer": "T1", "model": "deepseek-v4-flash", "hypothesis": "flash T1 gloss"},
    "c1-flash": {"layer": "C1", "model": "deepseek-v4-flash", "hypothesis": "flash C1 commentary"},
}


# ── data loaders ─────────────────────────────────────────────────────────────
def _load_kramasadbhava():
    rows = []
    for f in sorted(GOLD_RECORDS.glob("*.json")):
        g = json.load(open(f))
        stages = g.get("stages", {})
        # gold is often {close_translation: ...} or a plain string; the records only carry T1
        gold = stages.get("L2") or stages.get("l2") or stages.get("T1") or stages.get("t1")
        if isinstance(gold, dict):
            gold = gold.get("close_translation") or gold.get("translation") or str(gold)
        if isinstance(gold, list):  # some stages hold a list of glosses
            gold = " ".join(str(x) for x in gold)
        src = g.get("source", {}).get("source_text", "")
        if src and gold and not str(gold).startswith("{"):
            rows.append({"source": src,
                         "gold": gold if isinstance(gold, str) else str(gold),
                         "passage_id": g.get("passage_id", f.name)})
    return rows


def _load_ipvv(max_src_chars: int | None = None):
    rows = []
    for f in sorted(IPVV_GOLDS.glob("pt-passage-*.json")):
        g = json.load(open(f))
        src = g.get("source") or g.get("source_text") or ""
        if isinstance(src, dict):
            src = src.get("text", "")
        gold = g.get("l2_text") or g.get("l2") or ""
        if src and gold:
            src = str(src)
            if max_src_chars:
                src = src[:max_src_chars]
            rows.append({"source": src,
                         "gold": gold if isinstance(gold, str) else str(gold),
                         "passage_id": g.get("id", f.name)})
    return rows


def _load_mitra():
    rows = []
    for line in open(MITRA_TEST, encoding="utf-8"):
        line = line.strip()
        if line:
            d = json.loads(line)
            rows.append({"source": d["sanskrit"], "gold": d["english"],
                         "passage_id": "mitra"})
    return rows


# ── metrics ──────────────────────────────────────────────────────────────────
def _char_ngrams(s: str, n: int):
    s = re.sub(r"\s+", "", s)
    return [s[i:i + n] for i in range(len(s) - n + 1)]


def chrF(reference: str, candidate: str) -> float:
    if not reference or not candidate:
        return 0.0
    prec = rec = 0.0
    for n in (1, 2, 3):
        rg = set(_char_ngrams(reference, n)); cg = set(_char_ngrams(candidate, n))
        if not rg or not cg:
            continue
        inter = len(rg & cg)
        prec += inter / len(cg); rec += inter / len(rg)
    if prec == 0 or rec == 0:
        return 0.0
    return round(2 * (prec * rec) / (prec + rec) / 3.0, 4)


def bleu1(reference: str, candidate: str) -> float:
    import math
    rt = reference.split(); ct = candidate.split()
    if not rt or not ct:
        return 0.0
    hits = sum(1 for t in ct if t in set(rt))
    bp = math.exp(min(0, 1 - len(rt) / len(ct)))
    return round(bp * hits / len(ct), 4)


def semantic_fidelity(model: str, reference: str, candidate: str) -> tuple[int, str]:
    """LLM-as-judge 0-1 semantic fidelity (the quality axis). Returns (fidelity, judgment)."""
    from model import chat
    import os as _os
    timeout = int(_os.environ.get("SB_JUDGE_TIMEOUT", "120"))
    system = ("You are a strict Sanskrit translation judge. Rate how faithfully the CANDIDATE "
              "preserves the MEANING of the GOLD reference. Score 1-5 where 5=exact. Return exactly "
              "JSON: {\"fidelity\": <1-5>, \"judgment\": \"<why>\"}.")
    raw = chat(system, f"GOLD: {reference}\n\nCANDIDATE: {candidate}", model=model, timeout=timeout)
    import json as _json
    try:
        raw = re.sub(r"```(?:json)?", "", raw)
        m = re.search(r"\{.*\}", raw, re.S)
        d = _json.loads(m.group(0)) if m else {}
        fid = max(1, min(5, int(d.get("fidelity", 0))))
        return (fid / 5.0, str(d.get("judgment", ""))[:160])
    except Exception:
        return (0.0, f"__PARSE__ {str(raw)[:40]}")


# ── the translation call ─────────────────────────────────────────────────────
def translate(model: str, source: str) -> str:
    from model import chat
    system = ("You are a careful Sanskrit scholar-translator. Translate this Sanskrit into accurate, "
              "natural English. Preserve meaning; do not add interpretation. Output only the translation.")
    raw = chat(system, f"Translate:\n{source}", model=model, timeout=90)
    return (raw or "").strip().strip('"').strip()


# ── experiment id + registry ─────────────────────────────────────────────────
def _data_hash(rows) -> str:
    h = hashlib.sha256(json.dumps([r["source"] for r in rows], ensure_ascii=False).encode()).hexdigest()[:12]
    return h


def _experiment_id(layer, config_key, data_hash) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    return f"EXP-{layer}-{config_key}-{data_hash}-{ts}"


def log_experiment(record: dict) -> None:
    REGISTRY.parent.mkdir(parents=True, exist_ok=True)
    with open(REGISTRY, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    # auto-report (the machine-readable schema, per the science-lab upgrade)
    REPORTS.mkdir(parents=True, exist_ok=True)
    with open(REPORTS / f"{record['experiment_id']}-report.json", "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)


# ── the main run ─────────────────────────────────────────────────────────────
def run_experiment(layer, config_key, source_name, n, model, judge, dry_run):
    cfg = CONFIGS[config_key]
    model = model or cfg["model"]
    rows = TEST_SOURCES[source_name]["load"]()
    rows = rows[:n] if n else rows
    dh = _data_hash(rows)
    exp_id = _experiment_id(layer, config_key, dh)
    print(f"=== {exp_id} ===")
    print(f"  layer={layer} config={config_key} ({cfg['hypothesis']})")
    print(f"  test={source_name} rows={len(rows)} data_hash={dh} model={model}")

    if dry_run:
        for r in rows[:3]:
            print(f"  [sample] {r['passage_id']}: src={r['source'][:40]}… gold={r['gold'][:40]}…")
        print("  DRY-RUN (no model calls)")
        return 0

    results = []
    for i, r in enumerate(rows):
        t0 = time.time()
        try:
            cand = translate(model, r["source"])
        except Exception as e:
            cand = f"__ERROR__ {e}"
        dt = round(time.time() - t0, 2)
        row = {
            "passage_id": r["passage_id"],
            "source": r["source"][:300], "gold": r["gold"][:300], "candidate": cand[:300],
            "chrF": chrF(r["gold"], cand), "bleu1": bleu1(r["gold"], cand),
            "latency_s": dt,
        }
        # the deterministic PĀṬALA PROOF gate (verifiable, no model)
        if not cand.startswith("__ERROR__"):
            from translation_proof import verify_translation
            proof = verify_translation(r["source"], cand, gold=r["gold"])
            row["proof_gate"] = proof["deterministic_gate"]
            row["proof_blocking"] = proof["blocking"]
        if judge and not cand.startswith("__ERROR__"):
            fid, judg = semantic_fidelity(model, r["gold"], cand)
            row["semantic_fidelity"] = fid; row["judgment"] = judg
        results.append(row)
        print(f"  [{i+1}/{len(rows)}] chrF={row['chrF']:.3f} bleu={row['bleu1']:.3f} "
              f"fid={row.get('semantic_fidelity','-')} ({dt}s)")

    judged = [x for x in results if "semantic_fidelity" in x]
    proved = [x for x in results if x.get("proof_gate") == "PASS"]
    avg_chrf = sum(x["chrF"] for x in results) / len(results)
    avg_bleu = sum(x["bleu1"] for x in results) / len(results)
    avg_fid = (sum(x["semantic_fidelity"] for x in judged) / len(judged)) if judged else None

    record = {
        "experiment_id": exp_id, "layer": layer, "config_key": config_key,
        "model": model, "test": source_name, "data_hash": dh, "n": len(results),
        "date": datetime.now(timezone.utc).isoformat(),
        "avg_chrF": round(avg_chrf, 4), "avg_bleu1": round(avg_bleu, 4),
        "avg_semantic": round(avg_fid, 3) if avg_fid is not None else None,
        "proof_pass_rate": round(len(proved) / len(results), 3) if results else None,
        "total_time_s": round(sum(x["latency_s"] for x in results), 1),
        "hypothesis": cfg["hypothesis"], "rows": results,
    }
    log_experiment(record)
    print(f"\n  RESULT: chrF={avg_chrf:.4f} bleu={avg_bleu:.4f} semantic={record['avg_semantic']} "
          f"proof_pass={record['proof_pass_rate']}")
    print(f"  logged: {REGISTRY}")
    return 0


def report():
    if not REGISTRY.exists():
        print("  no experiments logged yet"); return 0
    print(f"{'EXP ID':12} {'layer':6} {'model':20} {'n':>4} {'chrF':>7} {'bleu':>7} {'sem':>6}")
    print("-" * 70)
    for line in open(REGISTRY, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        # only the translation-science experiments carry the metric keys; skip the ingest/download rows
        if "avg_chrF" not in r or "n" not in r:
            continue
        print(f"{r['experiment_id'][-12:]:12} {r['layer']:6} {r['model']:20} {r['n']:>4} "
              f"{r['avg_chrF']:>7.3f} {r['avg_bleu1']:>7.3f} "
              f"{str(r['avg_semantic']):>6}")
    return 0


def sweep(layer, test, n, trials, target, dry_run):
    """The Optuna-style auto-sweep: propose configs → run each → score by target → keep BEST.

    Prunes 0-quality/slow trials (burn-conscious). The registry keeps the full history so the study
    learns from prior trials. target in {quality, speed}."""
    import random
    rng = random.Random(42)
    best = None
    print(f"=== SWEEP {layer} on {test} ({trials} trials, target={target}) ===")
    for t in range(trials):
        # propose a config: vary the model (flash/pro) + judge on/off
        model = rng.choice(["deepseek-v4-flash", "deepseek-v4-pro"])
        judge = (target == "quality")  # judge pass only when targeting quality (burn-conscious)
        cfg_key = "l2-flash" if "flash" in model else "l2-pro"
        print(f"\n--- Trial {t+1}: model={model} judge={judge} ---")
        if dry_run:
            print("  DRY-RUN")
            continue
        try:
            run_experiment(layer, cfg_key, test, n, model, judge, False)
        except Exception as e:
            print(f"  trial failed: {e}")
            continue
        # pick the best by the target
        rows = [json.loads(l) for l in open(REGISTRY) if l.strip()]
        last = rows[-1]
        score = (last.get("avg_semantic") or last["avg_chrF"]) if target == "quality" else \
                (last.get("total_time_s") and -last["total_time_s"])
        if best is None or score > best[0]:
            best = (score, last["experiment_id"], model)
    if best:
        print(f"\n=== BEST ({target}): {best[1]} model={best[2]} score={best[0]:.3f} ===")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--layer", default="L2", choices=["T1", "ARGMAP", "L2", "L200", "C1"])
    ap.add_argument("--config", default="l2-flash", choices=list(CONFIGS.keys()))
    ap.add_argument("--test", default="mitrasamgraha", choices=list(TEST_SOURCES.keys()))
    ap.add_argument("--n", type=int, default=5)
    ap.add_argument("--model", default=None)
    ap.add_argument("--judge", action="store_true", help="add the LLM semantic-fidelity pass")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--report", action="store_true", help="compare all logged experiments")
    ap.add_argument("--list-configs", action="store_true")
    ap.add_argument("--sweep", action="store_true", help="Optuna-style auto-sweep over configs")
    ap.add_argument("--trials", type=int, default=3)
    ap.add_argument("--target", choices=["quality", "speed"], default="quality")
    args = ap.parse_args()

    if args.report:
        return report()
    if args.list_configs:
        for k, c in CONFIGS.items():
            print(f"  {k}: {c['hypothesis']} (model={c['model']})")
        return 0
    if args.sweep:
        return sweep(args.layer, args.test, args.n, args.trials, args.target, args.dry_run)
    return run_experiment(args.layer, args.config, args.test, args.n,
                          args.model, args.judge, args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
