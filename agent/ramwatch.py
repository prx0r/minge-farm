#!/usr/bin/env python3
"""agent/ramwatch.py — the RAM/CPU budget watchdog (crash prevention).

The box is 4-core / 8 GB / no swap / 2 agents. RAM is the scarcest resource and the #1 crash killer.
Run this BEFORE starting a heavy job, and WHILE it runs, to get a clear verdict on whether the box can
take it. Returns exit 0 (safe to start) or 1 (constrained — do lighter work / wait).

Usage:
  python3 agent/ramwatch.py          # check now, give a verdict
  python3 agent/ramwatch.py --json   # machine-readable
"""
from __future__ import annotations

import argparse
import json
import os
import sys


def read_mem():
    """Parse /proc/meminfo for total + available (in GiB)."""
    with open("/proc/meminfo") as f:
        d = dict(line.split(":", 1) for line in f)
    def gb(k):
        return int(d.get(k, "0 kB").strip().split()[0]) / 1024 / 1024
    return {"total_gib": round(gb("MemTotal"), 2), "available_gib": round(gb("MemAvailable"), 2)}


def read_load():
    """Load average (1-min) — informational only; the hard gate is available RAM."""
    try:
        return round(float(os.getloadavg()[0]), 2)
    except Exception:
        return 0.0


# The hard gate is AVAILABLE RAM (the user's rule): ~3 GiB is fine; worry only when it drops under 1 GiB.
SAFE_RAM = 1.0     # available >= this GiB → SAFE, safe to start a heavy job
CRITICAL_RAM = 0.4 # available <  this GiB → CRITICAL, never start (OOM risk)
# Load is ADVISORY only (the box is shared; another agent's job can spike it without OOM risk).


def verdict(mem, load):
    avail = mem["available_gib"]
    if avail >= SAFE_RAM:
        return "SAFE", f"available {avail:.2f} GiB / load {load:.2f} — RAM fine, safe to start a heavy job"
    if avail < CRITICAL_RAM:
        return "CRITICAL", f"available {avail:.2f} GiB / load {load:.2f} — DO NOT start; RAM under {CRITICAL_RAM} GiB (OOM risk)"
    return "CAUTION", f"available {avail:.2f} GiB / load {load:.2f} — RAM low; light work or wait"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    mem = read_mem(); load = read_load()
    status, note = verdict(mem, load)
    if args.json:
        print(json.dumps({"status": status, "available_gib": mem["available_gib"],
                          "load": load, "note": note}))
    else:
        print(f"RAM: {mem['available_gib']:.2f} GiB available / {mem['total_gib']:.2f} total")
        print(f"LOAD (1-min): {load:.2f} (advisory — RAM is the hard gate)")
        print(f"VERDICT: {status} — {note}")
    return 0 if status == "SAFE" else 1


if __name__ == "__main__":
    sys.exit(main())
