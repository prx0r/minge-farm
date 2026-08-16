# AGENT ORCHESTRATION — how a hermes agent runs the lab autonomously

*2026-08-16 · How `sanskritbenchy` is driven end-to-end by an agent (hermes) with kanban + cron + skills.
The lab is **fully agent-run**: an agent claims a kanban task, runs the step, logs the result, and the
watchdog keeps re-validating on a schedule. The human only reviews the logged numbers.*

---

## 1. THE AGENT-RUN LOOP (the closed cycle)

```
1. AGENT claims a kanban task (Phase P1–P6)         → hermes kanban claim <task>
2. AGENT loads the lab skill                         → hermes ... --skills sanskrit-benchy
3. AGENT runs the step                               → python3 agent/run.py --step <X> ...
4. AGENT reads the logged result                     → data/corpus/registries/*.jsonl
5. AGENT decides (keep/discard/hypothesize)          → per the ONE RULE (logged number on fixed gold)
6. AGENT comments the kanban task + completes it     → hermes kanban comment/complete
   └── WATCHDOG (cron) re-validates on schedule → posts summary → repeat
```

## 2. THE ORCHESTRATION LAYER (`agent/`)

| File | What it does |
|---|---|
| `agent/run.py` | the single entry point for ANY lab step (validate/eval/hypothesis/proof/report/watchdog). Logs every run to `data/corpus/registries/agent-runs.jsonl`. |
| `agent/watchdog.py` | a bounded autonomous cycle: validate → hypothesize → report, logged to `watchdog.jsonl`. Small samples (n=2), box-safe. |

**Usage:**
```bash
cd /root/sanskritbenchy
python3 agent/run.py --step validate --n 2 --m 3 --test mitrasamgraha    # the first proof (hermes, no torch)
python3 agent/run.py --step validate --test frontier:saamayik            # external gold
python3 agent/run.py --step hypothesis --rounds 1 --n 3                  # the self-improvement loop
python3 agent/run.py --step proof --source "…" --candidate "…"           # the Pāṭala proof gate
python3 agent/run.py --step report                                       # the leaderboard
python3 agent/watchdog.py --test mitrasamgraha                            # one full cycle
```

## 3. THE HERMES SKILLS (loaded at runtime via `--skills`)

- `skills/sanskrit-benchy/SKILL.md` — the lab driver skill: the command map, the run loop, the honest rules.
- Load it: `hermes ... --skills /root/sanskritbenchy/skills/sanskrit-benchy`
- Verified working: hermes loaded it and listed the lab files correctly in a live `-z` call.

## 4. THE KANBAN BOARD (`sanskritbenchy`)

Tracked Phases (dependency chain P1→P2→…→P6):
| Task | Phase | Gate |
|---|---|---|
| `t_2834010d` | **P1** first Kendall's-tau | logged tau (chrF vs bleu vs semantic-judge) on our + frontier gold |
| `t_c4d8b8ea` | **P2** COMET baseline | COMET tau vs chrF vs ours (torch box) |
| `t_758e7ab0` | **P3** school/period conditioning | tau(school-conditioned)>tau(not); *vimarśa* works |
| `t_377425f2` | **P4** Sanskrit DA/MQM gold | real versioned human-judgment set |
| `t_8ddf4172` | **P5** crypto-commitment proof | verifiable integrity-only commitment |
| `t_42b9d107` | **P6** persona product | end-to-end verified+committed persona translation |

Commands:
```bash
hermes kanban list                       # see tasks
hermes kanban claim <task>               # an agent claims a task
hermes kanban comment <task> "result"    # log the outcome
hermes kanban complete <task>            # done (gate passed)
hermes kanban show <task>                # full history
```

## 5. THE WATCHDOG (cron — autonomous re-validation)

- **Job:** `sanskritbenchy-daily-watchdog` — runs `sanskritbenchy-watchdog.sh` daily at 04:00 UTC.
- **Mode:** `--no-agent` (the script IS the job; its stdout is delivered verbatim). Classic watchdog pattern.
- **Wrapper:** `~/.hermes/scripts/sanskritbenchy-watchdog.sh` → runs `agent/watchdog.py --test mitrasamgraha
  --rounds 1 --n 2` → logs + prints a short summary.
- **Scheduler:** the hermes gateway is running (PID 11654), so cron fires automatically.
- **To run manually:** `hermes cron run sanskritbenchy-daily-watchdog` or `python3 agent/watchdog.py`.

## 6. THE EVIDENCE LEDGERS (what an agent reads to decide)

| Registry | What it holds |
|---|---|
| `data/corpus/registries/experiments.jsonl` | the logged translation experiments (chrF/bleu/semantic/proof) |
| `data/corpus/registries/hypotheses.jsonl` | every hypothesis tried + kept/discarded |
| `data/corpus/registries/agent-runs.jsonl` | every `agent/run.py` step |
| `data/corpus/registries/watchdog.jsonl` | every watchdog cycle |

## 7. THE ADVANCED HERMES FEATURES WE USE + COULD USE

| Feature | Status | Use |
|---|---|---|
| **kanban** | ✅ set up (board + 6 tasks + links) | task tracking + dependency chain |
| **cron** | ✅ daily watchdog registered | autonomous re-validation |
| **project** | ✅ `sanskritbenchy` project + board bound | deterministic worktree/branch convention |
| **skills** | ✅ `sanskrit-benchy` skill | the lab driver (loaded via `--skills`) |
| **moa** | ⬜ available | mixture-of-agents judge (multiple models grade translations) |
| **mcp serve** | ⬜ available | expose the lab's metrics/proofs to other agents |
| **hooks** | ⬜ available | auto-run `check.py` after a change |
| **send** | ⬜ available | deliver watchdog results to telegram/discord |

## 8. THE RULES (never violate — the anti-theatre guard)

1. **A result is real only when it is a logged number on fixed gold, resolved to a reproducible
   experiment.** If it isn't in the registry, it isn't decided.
2. **Box rules:** 8GB/4-core, ~2GB free. Run small samples (n=2–3), one job at a time, background long runs.
   Never two heavy jobs at once.
3. **The crypto layer proves integrity, never quality.**
4. **Never fabricate a result.** A failed step is logged as failed.
5. **Reuse, don't rebuild** (COMET, MTME, MQM, ezkl, risc0 — see `repos/README.md`).

---

*The lab is now fully agent-run: a hermes agent claims a kanban task, runs `agent/run.py`, reads the logged
result, and completes it; the daily watchdog keeps re-validating autonomously. The human reviews the logged
numbers. Next action: run `agent/run.py --step validate --n 2 --m 3 --test mitrasamgraha` to log the first
real Kendall's-tau and close P1.*
