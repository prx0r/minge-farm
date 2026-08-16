# METASTRUCTURE — the reusable agentic operating system (what sanskritbenchy taught us)

*2026-08-16 · The complete, reusable pattern for building an agent-runnable, self-organizing, handover-able
project with hermes. This is the "operating system" distilled from the sanskritbenchy build — the objective
structure + conventions + gates + lifecycle that ANY project can adopt so an agent works autonomously,
stays organized, and hands over cleanly. The reusable scaffolding is packaged in `agentic-infra/` (the
sibling project).*

---

## 1. THE PRINCIPLE (one line)

> **A project is agent-runnable when it has (1) a canonical structure an agent always finds, (2) a strict
> "how to work" discipline, (3) a machine-verifiable gate, (4) a live checkpoint DAG for autonomous
> goal-hitting, and (5) a canonical handover so a fresh agent gets full context in one read.**

---

## 2. THE CANONICAL STRUCTURE (every project has exactly this)

```
<project>/
  AGENTS.md            — the governing rules + the anti-mess standard (timestamped·logged·content-addressed·registered)
  CODING-AGENT.md      — the strict operational discipline (no-timeout, file lifecycle, review, test)
  VISION.md            — the goal + the checkpointed roadmap + the granular attainment path
  GOALS.md             — the concrete checkpoints (each falsifiable)
  DEV-PLAN-<X>.md      — the current dev plan(s) — update, don't proliferate
  HANDSOVER-TEMPLATE.md — the canonical handover spec
  HANDSOVER-YYYY-MM-DD-<topic>.md — the current handover (highest date = current; old kept as history)
  MANIFEST.json        — the machine resolver (every doc/script → id/owner/validator)
  check.py             — the drift gate (manifest + refs + data)
  CANONICAL-DATA-SPEC.md — the schemas (every data contract)
  INFRA-REQUIREMENTS.md — what's needed to complete the vision
  agent/               — run.py · verify.py · audit.py · trace.py · memory.py · ramwatch.py
  pipeline/            — run_recorder (content-addr) · schemas · checkpoint (DAG) · the domain kernels
  skills/<name>/       — the hermes skill
```

---

## 3. THE CONVENTIONS (strict)

| Concern | Rule |
|---|---|
| **Timestamps** | every note/handover/doc carries a date; `HANDSOVER-YYYY-MM-DD-*.md` |
| **Canonical places** | ONE dev plan (per hardware), ONE current handover, ONE checkpoint DAG, ONE schema spec — update, don't duplicate |
| **File lifecycle** | new → current → stale (fix or mark `> ⚠️ STALE`) → legacy (keep, `> **SUPERSEDED**`, never delete) |
| **Registration** | every doc/script → MANIFEST entry or `check.py` flags it |
| **Naming** | kernels `snake_case.py` · agent scripts `dash/snake.py` · data `snake_case.ext` · docs `TITLE-PURPOSE.md` |

---

## 4. THE MACHINE-VERIFIABLE GATE (every project)

```
python3 check.py --status        # PASS = docs registered + data validates
python3 agent/validate_data.py   # the strict data gate (every file vs its schema)
python3 agent/ramwatch.py        # SAFE (box budget)
```

---

## 5. THE AUTONOMOUS GOAL-HITTING (the checkpoint DAG)

A vision decomposes into a **checkpoint DAG** (`pipeline/checkpoint.py`): each checkpoint has an effect +
prerequisites + a **deterministic gate**. An agent works the NEXT checkpoint (prereqs done, not done); it's
marked DONE only when the gate PASSES. **The agent doesn't guess what "done" means — the DAG defines it.**

```
VISION → checkpoint DAG (effect + gate per step) → agent works the NEXT
  → gate PASSES → mark DONE → next
  → gate FAILS → NOT done → the agent CANNOT move past it
$ python3 agent/run.py --step checkpoints   # see the live DAG + the next gate
```

---

## 6. THE VERIFICATION SPINE (the anti-hallucination layer)

| Piece | What it proves |
|---|---|
| `run_recorder.py` | content-addressed run records + nanopublication + eigenius 4-kind ladder (Declared/Observed/Derived/Verified) |
| `verify.py` | proof gate + gold anti-hallucination → VERIFIED kind |
| `audit.py` | golden-file recompute on fixed gold (fail on mismatch) |
| `trace.py` | every run/experiment, greppable |
| `schemas.py` + `validate_data.py` | every data file matches its canonical schema |
| `memory.py` (DML) | deterministic temporal memory (anti-regression) |
| `ramwatch.py` | the RAM/CPU budget watchdog |

**The core:** the agent proposes; the system verifies. The scorer ≠ the generator.

---

## 7. THE AGENT-RUN ORCHESTRATOR (every project has one)

```
python3 agent/run.py --step <X>   # every step: logs to the trace + content-addresses the result
  --step checkpoints · validate · verify · audit · report · trace · memory · ramwatch
```
An agent (or cron) calls `run.py`; it appends to `data/runs/agent-steps.jsonl` (the centralized trace) and
content-addresses the result. **If it isn't in the trace, it didn't happen.**

---

## 8. THE HANDOVER (the canonical spec)

`HANDSOVER-TEMPLATE.md` — every handover MUST have: one-line state · project · read order · current state
(DONE table) · live checkpoint DAG · dev plans · verified results · data · gates · gaps · infra · recent
changes · git state · the smoke test · the sign-off. A handover is the complete orientation, not a progress
log.

---

## 9. HOW TO STAND UP A NEW PROJECT (the checklist)

1. Copy `agentic-infra/` (the reusable scaffolding) as the skeleton.
2. Fill `VISION.md` (the goal) → decompose into `pipeline/checkpoint.py` gates.
3. Write `GOALS.md` (the checkpoints) + `DEV-PLAN-*.md` (per hardware).
4. Define the schemas (`pipeline/schemas.py`) + register docs (`MANIFEST.json`).
5. Wire the domain kernels into `agent/run.py` + the skill.
6. Run the gate → the project is agent-runnable.

---

## 10. THE ONE-LINE SUMMARY

> **Timestamped · logged · content-addressed · registered · gated.** Every project adopts the same
> structure, conventions, verification spine, checkpoint DAG, and handover template — so ANY agent can
> walk in, run the smoke test, see the next gate, work autonomously, and hand over cleanly. That is the
> reusable agentic operating system.
