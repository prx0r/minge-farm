---
name: sanskrit-benchy
description: "Drive the Sanskrit benchmark science lab: run experiments, hypotheses, Kendall's-tau validation, Pāṭala proofs, and the watchdog — all kanban-aware."
version: 1.0.0
date: 2026-08-16
author: sanskritbenchy
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [Sanskrit, Benchmark, MT, COMET, Science, ML]
    related_skills: [research, arxiv]
---

# Sanskrit Benchmark Science Lab (sanskritbenchy)

Drive the lab at `/root/sanskritbenchy`. Every claim must be a logged number on fixed gold (the ONE RULE).
The board is `sanskritbenchy` (hermes kanban); the project is `sanskritbenchy`.

## The lab map (what each command does)

| Command | What it does |
|---|---|
| `python3 agent/run.py --step validate --n 2 --m 3 --test mitrasamgraha` | Kendall's-tau meta-eval (does our metric beat chrF?) |
| `python3 agent/run.py --step validate --test frontier:saamayik` | same on external Sāmayik gold |
| `python3 agent/run.py --step eval --n 5 --judge` | Mitrasamgraha eval (chrF/bleu/semantic-judge) |
| `python3 agent/run.py --step hypothesis --rounds 1 --n 3` | observe→hypothesize→test→keep loop |
| `python3 agent/run.py --step proof --source "…" --candidate "…"` | the deterministic Pāṭala proof gate |
| `python3 agent/run.py --step report` | the experiment leaderboard |
| `python3 agent/watchdog.py --test mitrasamgraha` | a full autonomous cycle (validate→hypothesize→report) |

## How to run a real experiment (the standard loop)

```bash
cd /root/sanskritbenchy

# 1. check the gate first
python3 check.py --status

# 2. run a small real validation (hermes model, no torch) — the first proof
python3 agent/run.py --step validate --n 2 --m 3 --test mitrasamgraha

# 3. propose hypotheses from what failed
python3 pipeline/hypothesis_lab.py --propose

# 4. run the hypothesis loop
python3 agent/run.py --step hypothesis --rounds 1 --n 3

# 5. see the leaderboard
python3 agent/run.py --step report
```

## Kanban awareness

- The board `sanskritbenchy` tracks Phases P1–P6 (P1 = first tau, P2 = COMET, P3 = school/period, P4 =
  DA/MQM gold, P5 = crypto proof, P6 = product).
- `hermes kanban list` to see tasks; `hermes kanban comment <task> "…"` to log a result; claim/complete
  tasks as you pass their gates.
- The watchdog posts a summary to the P1 task each cycle.

## The honest rules (never violate)

1. **No claim of "better" without a logged Kendall's-tau vs human gold on the same fixed data.** Log to
   `data/corpus/registries/experiments.jsonl` (via the lab) or `agent-runs.jsonl` (via `agent/run.py`).
2. **No "trained COMET" before the Phase 4 DA/MQM gold exists.**
3. **The crypto layer proves integrity, never quality** (see `research/DEEP-DIVE-COMET-CRYPTO-VERIFICATION.md`).
4. **Box rules:** 8GB/4-core, ~2GB free. Run SMALL samples (n=2–3), one job at a time, background long runs.
   Never run two heavy jobs at once.
5. **Never fabricate a result.** A failed step is logged as failed.

## How to read the results

- `data/corpus/registries/experiments.jsonl` — the logged translation experiments (chrF/bleu/semantic).
- `data/corpus/registries/agent-runs.jsonl` — every `agent/run.py` step (the orchestration ledger).
- `data/corpus/registries/watchdog.jsonl` — every watchdog cycle.
- `research/HOW-WE-BEAT-AND-IMPROVE-THE-BENCHMARK.md` — what the tau number means.
