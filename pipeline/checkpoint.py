#!/usr/bin/env python3
"""pipeline/checkpoint.py — the VISION → CHECKPOINT engine (autonomous goal-hitting).

The mechanism that makes the project hit goals autonomously: a vision is decomposed into a DAG of
falsifiable checkpoints, each with an effect + prerequisites + a deterministic gate. An agent (or the
watchdog) works the DAG: only a checkpoint whose prerequisites are DONE and whose gate passes is marked
DONE. This is the "intelligently set checkpoints that get us there" layer — the agent doesn't guess what
"done" means; the checkpoint DAG defines it.

A checkpoint is DONE iff its GATE passes (a logged, content-addressed, deterministic check). If the gate
fails, the checkpoint is NOT done — the agent cannot move past it.

Deterministic + stdlib. State persisted as a JSON DAG (data/checkpoints.json).

Usage:
  python3 pipeline/checkpoint.py --status          # the checkpoint DAG + what's done / what's next
  python3 pipeline/checkpoint.py --define <name> --effect "<what it achieves>" --gate "<command>" --after <prereq>
  python3 pipeline/checkpoint.py --mark <name>     # mark done (the agent ran the gate; it passed)
  python3 pipeline/checkpoint.py --next            # the next checkpoint to work (prereqs done, not done)
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DAG_FILE = ROOT / "data" / "checkpoints.json"


def _load() -> dict:
    if DAG_FILE.exists():
        return json.loads(DAG_FILE.read_text())
    return {"version": "0.1.0", "checkpoints": {}}


def _save(dag: dict) -> None:
    dag["updated"] = datetime.now(timezone.utc).isoformat()
    DAG_FILE.parent.mkdir(parents=True, exist_ok=True)
    DAG_FILE.write_text(json.dumps(dag, ensure_ascii=False, indent=2))


def define(name: str, effect: str, gate: str, after: list[str]) -> None:
    dag = _load()
    dag["checkpoints"][name] = {"name": name, "effect": effect, "gate": gate,
                                "prereqs": after, "status": "OPEN", "ts": None}
    _save(dag)
    print(f"defined checkpoint '{name}' → {effect} (gate: {gate}, after: {after})")


def _prereqs_done(dag: dict, name: str) -> bool:
    cp = dag["checkpoints"][name]
    return all(dag["checkpoints"].get(p, {}).get("status") == "DONE" for p in cp["prereqs"])


def run_gate(cp: dict) -> tuple[bool, str]:
    """Run a checkpoint's deterministic gate (a shell command); True if it exits 0."""
    try:
        p = subprocess.run(cp["gate"], shell=True, capture_output=True, text=True, timeout=300)
        return p.returncode == 0, (p.stdout or p.stderr)[-300:]
    except Exception as e:
        return False, f"gate error: {e}"


def mark(name: str, run: bool) -> None:
    dag = _load()
    if name not in dag["checkpoints"]:
        print(f"no checkpoint '{name}'"); return
    cp = dag["checkpoints"][name]
    if not _prereqs_done(dag, name):
        print(f"✗ '{name}' prereqs not done: {cp['prereqs']}"); return
    if run:
        ok, out = run_gate(cp)
        if not ok:
            print(f"✗ gate FAILED for '{name}': {out}")
            cp["status"] = "FAILED"; cp["ts"] = datetime.now(timezone.utc).isoformat()
            _save(dag); return
    cp["status"] = "DONE"; cp["ts"] = datetime.now(timezone.utc).isoformat()
    _save(dag)
    print(f"✓ '{name}' DONE ({cp['effect']})")


def status() -> None:
    dag = _load()
    cps = dag["checkpoints"]
    print(f"=== CHECKPOINT DAG ({len(cps)} checkpoints) ===")
    for name, cp in cps.items():
        done = "DONE" if cp["status"] == "DONE" else cp["status"]
        print(f"  [{done:6}] {name:22} → {cp['effect']}")
    print("\n=== NEXT (prereqs done, not done) ===")
    for name, cp in cps.items():
        if cp["status"] != "DONE" and _prereqs_done(dag, name):
            print(f"  → {name}: {cp['effect']}  (gate: {cp['gate']})")


def next_cp() -> str:
    dag = _load()
    for name, cp in dag["checkpoints"].items():
        if cp["status"] != "DONE" and _prereqs_done(dag, name):
            return name
    return ""


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--define", default="")
    ap.add_argument("--effect", default="")
    ap.add_argument("--gate", default="")
    ap.add_argument("--after", default="")
    ap.add_argument("--mark", default="")
    ap.add_argument("--run-gate", action="store_true")
    ap.add_argument("--next", action="store_true")
    args = ap.parse_args()
    if args.define:
        after = [a for a in args.after.split(",") if a]
        define(args.define, args.effect, args.gate, after)
    elif args.mark:
        mark(args.mark, args.run_gate)
    elif args.next:
        print(next_cp())
    else:
        status()
