#!/usr/bin/env python3
"""check.py — the sanskritbenchy drift validator (mirrors the patalaorg/smellycock gate).

  --manifest  MANIFEST.json is valid JSON + every listed doc exists
  --refs      every doc's referenced /root/... paths resolve (best-effort)
  --data      every data file matches its canonical schema (agent/validate_data.py)
  --status    run all checks (default)

Exit 0 = pass, 1 = fail. A doc/claim that doesn't resolve is flagged (docs are a projection).
"""
from __future__ import annotations
import json, os, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "MANIFEST.json"


def check_manifest() -> list[str]:
    errors = []
    try:
        m = json.load(open(MANIFEST))
    except Exception as e:
        return [f"MANIFEST.json invalid: {e}"]
    for sec in ("docs", "implementation"):
        for k in m.get(sec, {}):
            if not (ROOT / k).exists():
                errors.append(f"manifest {sec} missing: {k}")
    return errors


def check_refs() -> list[str]:
    errors = []
    for root, _dirs, files in os.walk(ROOT):
        if ".git" in root or "__pycache__" in root:
            continue
        for fn in files:
            if not fn.endswith((".md", ".py")):
                continue
            path = os.path.join(root, fn)
            for line in open(path, encoding="utf-8", errors="ignore"):
                for ref in re.findall(r"`(/root/[^`]+|/mnt/[^`]+)`", line):
                    if not os.path.exists(ref):
                        errors.append(f"dangling ref in {os.path.relpath(path, ROOT)}: {ref}")
    return errors


def check_data() -> list[str]:
    """The strict schema gate: every data file matches its canonical contract."""
    try:
        p = subprocess.run(["python3", str(ROOT / "agent" / "validate_data.py")],
                           capture_output=True, text=True, timeout=120)
        if p.returncode != 0:
            # surface the first few violations
            return [line.strip() for line in p.stdout.splitlines()
                    if "✗" in line or "violation" in line][:10] or ["data schema violations"]
    except Exception as e:
        return [f"data gate error: {e}"]
    return []


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "--status"
    errors = []
    if mode in ("--status", "--manifest"):
        errors += check_manifest()
    if mode in ("--status", "--refs"):
        errors += check_refs()
    if mode in ("--status", "--data"):
        errors += check_data()
    if errors:
        print(f"sanskritbenchy check: FAIL ({len(errors)} issue{'s' if len(errors)!=1 else ''})")
        for e in errors[:20]:
            print(f"  ✗ {e}")
        return 1
    print("sanskritbenchy check: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
