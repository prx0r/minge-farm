# AGENTS.md — sanskritbenchy (the Sanskrit benchmark science lab)

*2026-08-16 · The governing file for any agent working in this project. Read this FIRST, then
`VISION.md`, then `CODING-AGENT.md` (the strict operational discipline: no-timeout backgrounding, file
conventions, the review protocol, testing + monitoring), then `AGENTS.md` at the repo root for the box
rules. This file defines the ONE RULE and the **deterministic anti-mess standard**: timestamped build
notes, a centralized run/experiment trace, and content-addressed provenance for every number.*

---

## 0. THE ONE RULE (everything else follows)

> **Nothing is "real" because a file exists. It is real only when an independently defined task,
> human-grounded gold, and a reproducible, LOGGED gate show it does what it claims.** A headline number is
> real only when it is a machine-computed value in a content-addressed run record on fixed gold.

## 1. THE DETERMINISTIC ANTI-MESS STANDARD (mandatory)

### 1.1 Every build note is TIMESTAMPED
- Any note, handover, or build record you create **must** carry a timestamp in the filename or header:
  `HANDSOVER-YYYY-MM-DD.md` or `*YYYY-MM-DD*` in the first lines.
- Never leave an undated note. If you add content to an existing doc, add a `*updated YYYY-MM-DD*` line.
- **Rule:** a note without a timestamp does not exist as a build record.

### 1.2 Every hermes run + experiment is TRACKED with a log
- Every agent step must go through `agent/run.py --step X` — which logs to **`data/runs/agent-steps.jsonl`**
  (the centralized trace) automatically.
- Every experiment must be logged to **`data/corpus/registries/experiments.jsonl`** (via the lab) with a
  timestamped `experiment_id`.
- The watchdog logs to **`data/runs/watchdog.jsonl`**.
- **Query them with one command:** `python3 agent/trace.py --recent / --steps / --search <q> / --all`.
- **Rule:** if it isn't in the trace, it didn't happen. Every run must resolve to a timestamped log line.

### 1.3 Every NUMBER is content-addressed + provenance-carrying
- Every headline number must be a machine-computed value in a content-addressed run record
  (`run_recorder.py` → `run_signature = sha256(gold ‖ code ‖ config) → out_hash`), carrying a
  **nanopublication** `{assertion, evidence, provenance}`.
- **Rule:** a number with no content-addressed run record is theater. `agent/audit.py` enforces this by
  recomputing on fixed gold and failing on mismatch.

### 1.4 Every doc is REGISTERED in the MANIFEST
- Every doc/script/kernel gets a `MANIFEST.json` entry (id + owner + validator) or `check.py` flags it.
- **Rule:** `python3 check.py --status` must PASS after any change.

### 1.5 One concern = one doc; reference, don't copy
- Don't create a sibling doc that duplicates an existing role — extend the existing one.
- Point at the real code/data; don't copy it into a doc.

## 2. THE WORKFLOW (mandatory before/after any change)

```bash
# 1. gate first
python3 check.py --status

# 2. run the step via the orchestrator (logs to the trace automatically)
python3 agent/run.py --step validate
python3 agent/run.py --step benchmark --n 1        # dealradar picks model → hermes → proof gate
python3 agent/run.py --step proof --source "…" --candidate "…"

# 3. verify the result is logged + content-addressed
python3 agent/trace.py --recent
python3 agent/audit.py --list

# 4. after any change, re-run the gate
python3 check.py --status
```

## 3. THE GATE (before claiming anything done)

```bash
cd /root/sanskritbenchy
python3 check.py --status        # PASS = every doc/script resolves
PYTHONPATH=. python3 pipeline/sanskrit_gold.py   # the fixed gold runs
python3 agent/trace.py --all     # every run is logged + greppable
```

## 4. THE BOX RULES (from the root AGENTS.md — non-negotiable)

- **Never `sleep` to wait** — background long jobs (`setsid nohup … &`), note the PID, do real work.
- **Never `pkill`** — find the exact PID, `kill <PID>`.
- **RAM is the scarcest resource** (4-core / 8GB / no swap, 2 agents) — run SMALL samples (n=2–3), one job
  at a time, ~2GB free. Stream, never bulk-load.
- **CHECK the budget before + during any heavy job** (`agent/ramwatch.py` or `free -h | head -2 && uptime`):
  - **GOOD to start a job:** available RAM ≥ 1 GiB (e.g. ~3 GiB is fine). Load is advisory, not a gate.
  - **DO NOT start:** available < ~400-500 MiB (real OOM risk; a new job can kill both agents).
  - **If available < ~400 MiB while running, KILL the job by PID and let the box recover.**
  - Never run two RAM-heavy jobs at once (e.g. a hermes batch + an index build) — serialize.
- **The crypto layer proves integrity, never quality.**
- **Reuse, don't rebuild** (COMET, MTME, MQM, ezkl, risc0 — see `repos/README.md`).

## 5. THE STANDARD IN ONE SENTENCE

> **Timestamped, logged, content-addressed, registered.** Every build note is dated; every hermes run and
> experiment is in the trace; every number is a content-addressed nanopublication on fixed gold; every doc
> is in the MANIFEST; and `check.py` + `trace.py` + `audit.py` enforce it all deterministically — so the
> project can't get messy even if an agent forgets. RAM/CPU is budgeted before every heavy job so the box
> doesn't crash.
