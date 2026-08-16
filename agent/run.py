#!/usr/bin/env python3
"""agent/run.py — the AGENT-RUN orchestrator for sanskritbenchy.

A single entry point an agent (or the watchdog) calls to run ANY lab step, with kanban awareness:
  - it claims/completes the relevant kanban task
  - runs the underlying lab script
  - logs the result to the experiment registry
  - posts a comment / updates the task

Designed to be driven by hermes (`hermes chat` with the sanskritbenchy skill) OR by cron (watchdog).

Usage:
  python3 agent/run.py --step validate --n 2 --m 3 --test mitrasamgraha
  python3 agent/run.py --step eval --n 5 --judge
  python3 agent/run.py --step hypothesis --rounds 1 --n 3
  python3 agent/run.py --step proof --source "kramasadbhava namaḥ" --candidate "Homage to Shiva"
  python3 agent/run.py --step report
  python3 agent/run.py --step watchdog --loop           # run a full watchdog cycle (validate→hypothesize→report)
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))
sys.path.insert(0, str(ROOT))

# kanban board (hermes kanban) — the active board is 'sanskritbenchy'
BOARD = "sanskritbenchy"


def _sh(*args: str, timeout: int = 600) -> str:
    """Run a shell command (background-safe), return stdout."""
    try:
        p = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        return (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired:
        return f"__TIMEOUT__ {' '.join(args)}"


def _kanban(cmd: str, *args: str) -> str:
    return _sh("hermes", "kanban", cmd, *args)


def log_line(record: dict) -> Path:
    """Append a machine-readable result to the lab registry (centralized trace)."""
    reg = ROOT / "data" / "corpus" / "registries" / "agent-runs.jsonl"
    reg.parent.mkdir(parents=True, exist_ok=True)
    record["ts"] = datetime.now(timezone.utc).isoformat()
    with open(reg, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    # also append to the centralized agent-steps trace (the anti-mess ledger)
    step_reg = ROOT / "data" / "runs" / "agent-steps.jsonl"
    step_reg.parent.mkdir(parents=True, exist_ok=True)
    with open(step_reg, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return reg


def _record_run(step: str, gold, config: dict, metrics: dict, assertion: str = "") -> dict:
    """Persist a content-addressed run record (the provenance ledger) alongside the registry row."""
    from run_recorder import RunRecorder
    return RunRecorder().record(step=step, gold=gold, config=config, metrics=metrics,
                                assertion=assertion)


# ── the lab steps ───────────────────────────────────────────────────────────
def step_validate(n: int, m: int, test: str) -> dict:
    out = _sh("python3", str(ROOT / "pipeline" / "validate_benchmark.py"),
              "--n", str(n), "--m", str(m), "--test", test, timeout=900)
    rec = {"step": "validate", "test": test, "n": n, "m": m, "output": out[-2000:]}
    log_line(rec)
    print(out)
    return rec


def step_eval(n: int, judge: bool, test: str) -> dict:
    args = ["python3", str(ROOT / "tools" / "eval_mitrasamgraha.py"), "--n", str(n)]
    if judge:
        args.append("--judge")
    out = _sh(*args, timeout=900)
    rec = {"step": "eval", "test": test, "n": n, "judge": judge, "output": out[-2000:]}
    log_line(rec)
    print(out)
    return rec


def step_hypothesis(rounds: int, n: int, test: str) -> dict:
    out = _sh("python3", str(ROOT / "pipeline" / "hypothesis_lab.py"),
              "--loop", str(rounds), "--n", str(n), "--test", test, timeout=900)
    rec = {"step": "hypothesis", "rounds": rounds, "n": n, "test": test, "output": out[-2000:]}
    log_line(rec)
    print(out)
    return rec


def step_proof(source: str, candidate: str) -> dict:
    from pipeline.translation_proof import verify_translation
    p = verify_translation(source, candidate)
    rec = {"step": "proof", "source": source, "candidate": candidate,
           "deterministic_gate": p["deterministic_gate"], "blocking": p["blocking"],
           "result_id": p["lineage"]["result_id"]}
    log_line(rec)
    # content-address the proof as a run record (nanopublication: assertion + evidence + provenance)
    try:
        _record_run(step="proof", gold=[{"source": source, "gold": candidate}],
                    config={"method": "translation_proof", "candidate": candidate},
                    metrics={"deterministic_gate": p["deterministic_gate"]},
                    assertion=f"source '{source}' → candidate '{candidate}' "
                              f"is {p['deterministic_gate']} ({', '.join(p['blocking']) or 'all checks pass'})")
    except Exception as e:
        print(f"  (run record skipped: {e})")
    print(json.dumps(p, ensure_ascii=False, indent=2))
    return rec


def step_report() -> dict:
    out = _sh("python3", str(ROOT / "pipeline" / "experiment_lab.py"), "--report", timeout=120)
    rec = {"step": "report", "output": out[-2000:]}
    log_line(rec)
    print(out)
    return rec


def step_watchdog(validate_test: str, rounds: int, n: int) -> dict:
    """A full autonomous cycle: validate → hypothesize → report → kanban comment."""
    print(f"=== WATCHDOG CYCLE {datetime.now(timezone.utc).isoformat()} ===")
    v = step_validate(2, 3, validate_test)
    h = step_hypothesis(rounds, n, validate_test)
    r = step_report()
    # kanban: comment on the P1 task with the result (best-effort)
    summary = f"watchdog: validate={validate_test} → hypothesis rounds={rounds} → report done"
    _kanban("comment", "t_2834010d", summary)  # P1 task
    rec = {"step": "watchdog", "validate": validate_test, "rounds": rounds, "n": n,
           "summary": summary}
    log_line(rec)
    return rec


def step_benchmark_registry() -> dict:
    """Build the legitimate content-addressed benchmark registry (the fixed gold)."""
    out = _sh("python3", str(ROOT / "pipeline" / "benchmark_registry.py"), timeout=120)
    rec = {"step": "benchmark_registry", "output": out[-2000:]}
    log_line(rec)
    print(out)
    return rec


def step_benchmark(n: int, max_chars: int, dry: bool) -> dict:
    """Run the progressive-difficulty benchmark: dealradar picks model → hermes translates → proof gate."""
    import sys as _sys
    _sys.path.insert(0, str(ROOT / "pipeline"))
    _sys.path.insert(0, str(ROOT / ".." / "dealradar" / "app"))
    from benchmark_runner import run_benchmark
    res = run_benchmark(n_per_school=n, max_chars=max_chars, dry_run=dry)
    rec = {"step": "benchmark", "n_per_school": n, "max_chars": max_chars, "dry": dry,
           "n_passages": res.get("n_passages"), "run_signature": res.get("run_signature")}
    log_line(rec)
    return rec


def step_sanskrit_texts() -> dict:
    """Index the DCS/GRETIL progressive-difficulty source texts."""
    out = _sh("python3", str(ROOT / "pipeline" / "sanskrit_texts.py"), timeout=120)
    rec = {"step": "sanskrit_texts", "output": out[-2000:]}
    log_line(rec)
    print(out)
    return rec


def step_benchmark_report() -> dict:
    """The per-school × per-tier × term-density benchmark leaderboard."""
    out = _sh("python3", str(ROOT / "tools" / "sanskrit_benchmark.py"), "--report", timeout=120)
    rec = {"step": "benchmark_report", "output": out[-2000:]}
    log_line(rec)
    print(out)
    return rec


def step_gold() -> dict:
    """The fixed gold control summary (sanskrit_gold.py)."""
    out = _sh("python3", str(ROOT / "pipeline" / "sanskrit_gold.py"), timeout=120)
    rec = {"step": "gold", "output": out[-2000:]}
    log_line(rec)
    print(out)
    return rec


def step_comet() -> dict:
    """COMET learned-metric adapter (Phase B — needs torch; fails cleanly if absent)."""
    out = _sh("python3", str(ROOT / "pipeline" / "comet_scorer.py"), timeout=120)
    rec = {"step": "comet", "output": out[-2000:]}
    log_line(rec)
    print(out)
    return rec


def step_frontier() -> dict:
    """The imported frontier benchmark datasets (Sāmayik, Itihāsa)."""
    out = _sh("python3", str(ROOT / "pipeline" / "frontier_gold.py"), timeout=120)
    rec = {"step": "frontier", "output": out[-2000:]}
    log_line(rec)
    print(out)
    return rec


def step_verify(source: str, candidate: str, gold: str) -> dict:
    """The full verification gate (proof gate + gold anti-hallucination + content-addressed record)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("verify", ROOT / "agent" / "verify.py")
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    r = mod.verify_translation_claim(source, candidate, gold)
    rec = {"step": "verify", "source": source, "candidate": candidate[:60],
           "deterministic_gate": r["deterministic_gate"], "gold_ok": r["gold_ok"],
           "verified": r["verified"], "run_signature": r["run_signature"]}
    log_line(rec)
    print(f"verify: gate={r['deterministic_gate']} gold_ok={r['gold_ok']} "
          f"→ {'VERIFIED' if r['verified'] else 'NOT verified'} (sig {r['run_signature']})")
    return rec


STEPS = {
    "validate": step_validate, "eval": step_eval, "hypothesis": step_hypothesis,
    "proof": step_proof, "report": step_report, "watchdog": step_watchdog,
    "benchmark": step_benchmark, "benchmark_registry": step_benchmark_registry,
    "sanskrit_texts": step_sanskrit_texts, "benchmark_report": step_benchmark_report,
    "gold": step_gold, "comet": step_comet, "frontier": step_frontier,
    "verify": step_verify,
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--step", required=True, choices=list(STEPS))
    ap.add_argument("--n", type=int, default=3)
    ap.add_argument("--m", type=int, default=3)
    ap.add_argument("--test", default="mitrasamgraha")
    ap.add_argument("--judge", action="store_true")
    ap.add_argument("--rounds", type=int, default=1)
    ap.add_argument("--source", default="")
    ap.add_argument("--candidate", default="")
    ap.add_argument("--gold", default="")
    ap.add_argument("--loop", action="store_true")
    ap.add_argument("--max-chars", type=int, default=1500)
    args = ap.parse_args()

    if args.step == "validate":
        step_validate(args.n, args.m, args.test)
    elif args.step == "eval":
        step_eval(args.n, args.judge, args.test)
    elif args.step == "hypothesis":
        step_hypothesis(args.rounds, args.n, args.test)
    elif args.step == "proof":
        if not args.source or not args.candidate:
            print("--step proof needs --source and --candidate"); return 2
        step_proof(args.source, args.candidate)
    elif args.step == "report":
        step_report()
    elif args.step == "watchdog":
        step_watchdog(args.test, args.rounds, args.n)
    elif args.step == "benchmark":
        step_benchmark(args.n, args.max_chars, False)
    elif args.step == "benchmark_registry":
        step_benchmark_registry()
    elif args.step == "sanskrit_texts":
        step_sanskrit_texts()
    elif args.step == "benchmark_report":
        step_benchmark_report()
    elif args.step == "gold":
        step_gold()
    elif args.step == "comet":
        step_comet()
    elif args.step == "frontier":
        step_frontier()
    elif args.step == "verify":
        if not args.source or not args.candidate:
            print("--step verify needs --source and --candidate"); return 2
        step_verify(args.source, args.candidate, args.gold)
    return 0


if __name__ == "__main__":
    sys.exit(main())
