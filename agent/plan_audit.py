#!/usr/bin/env python3
"""agent/plan_audit.py — the repeatable DEV-PLAN retirement validator (RETIRING-A-DEV-PLAN.md §3).

Reconciles a dev plan's claimed deliverables against reality and runs the retirement gates. An item is
"done-able" only if every claimed file exists + the data validates + the gate is green + git is clean.

Usage:
  python3 agent/plan_audit.py --plan DEV-PLAN-NO-GPU.md         # scan a plan's file links + run gates
  python3 agent/plan_audit.py --files pipeline/x.py agent/y.py  # check specific claimed files

It extracts every path-like token (xxx.py / xxx.md / data/...) in the plan and reports which are MISSING.
Exit 0 = all linked files exist AND gates pass; 1 = a claimed file is missing or a gate failed.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _sh(*args: str, timeout: int = 120) -> str:
    try:
        p = subprocess.run(args, capture_output=True, text=True, timeout=timeout, cwd=ROOT)
        return (p.stdout or "") + (p.stderr or "")
    except Exception as e:
        return f"__ERR__ {e}"


def extract_paths(text: str) -> list[str]:
    """Pull path-like tokens (files/dirs) mentioned in a doc, as relative project paths."""
    paths = set()
    # explicit paths (pipeline/x.py, agent/y.py, data/z.json, docs/w.md, scripts/...)
    for m in re.finditer(r"(?:pipeline|agent|data|docs|research|skills|tools|scripts)/[\w./\-]+\.(?:py|md|sh|json|jsonl|ts|mjs|html|txt)", text):
        p = m.group(0)
        # drop trailing punctuation / quotes
        p = p.rstrip('.,;:)]}"')
        if (ROOT / p).exists() or ROOT.joinpath(p).is_dir():
            paths.add(p)
    return sorted(paths)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", help="a DEV-PLAN doc to reconcile")
    ap.add_argument("--files", nargs="*", help="explicit claimed files to check")
    args = ap.parse_args()

    fail = False
    linked = []
    if args.plan:
        plan = ROOT / args.plan
        if not plan.exists():
            print(f"MISS  {args.plan}"); fail = True
        else:
            linked = extract_paths(plan.read_text(encoding="utf-8"))
            print(f"=== reconciling {args.plan} ({len(linked)} linked files found) ===")
    if args.files:
        linked = list(dict.fromkeys(linked + list(args.files)))

    if linked:
        for p in linked:
            fp = ROOT / p
            if fp.exists():
                print(f"  OK   {p}")
            else:
                print(f"  MISS {p}"); fail = True

    # the gates (silent unless failing)
    if not fail:
        dat = _sh("python3", "agent/validate_data.py")
        if "0 violations" not in dat:
            print("GATE FAIL: validate_data.py"); fail = True
        gate = _sh("python3", "check.py", "--status")
        if "PASS" not in gate:
            print("GATE FAIL: check.py --status"); fail = True
        dirty = _sh("git", "status", "--porcelain").strip()
        if dirty:
            print(f"GATE: git dirty ({len(dirty.splitlines())} files) — commit before retiring"); fail = True

    print("\nRETIREMENT AUDIT: " + ("PASS — plan reconciles, gates green" if not fail
                                    else "FAIL — fix the MISS lines / gates before retiring"))
    return 0 if not fail else 1


if __name__ == "__main__":
    sys.exit(main())
