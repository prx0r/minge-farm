# RECIPES — every agent command + how to expand the lab

*2026-08-16 · The complete recipe book for driving sanskritbenchy (and dealradar) as an agent. Every
command, what it does, and the exact recipe sequences. Plus how to properly expand the lab with new
capabilities. Read `HOW-IT-WORKS.md` first for the mechanisms.*

---

## 1. THE ORCHESTRATOR (`agent/run.py`) — every step, logged + content-addressed

| Step | Command | What it does |
|---|---|---|
| **validate** | `python3 agent/run.py --step validate` | run the test suite (the gate) |
| **eval** | `python3 agent/run.py --step eval --n 5 --judge` | Mitrasamgraha eval (chrF/bleu/semantic-judge) |
| **hypothesis** | `python3 agent/run.py --step hypothesis --rounds 1 --n 3` | observe→hypothesize→test→keep loop |
| **proof** | `python3 agent/run.py --step proof --source "…" --candidate "…"` | the deterministic Pāṭala proof gate |
| **verify** | `python3 agent/run.py --step verify --source "…" --candidate "…" --gold "…"` | the FULL verification (proof + gold anti-hallucination + content-address) |
| **report** | `python3 agent/run.py --step report` | the experiment leaderboard |
| **benchmark** | `python3 agent/run.py --step benchmark --n 1` | progressive-difficulty benchmark (dealradar picks model → translate → proof) |
| **benchmark_registry** | `python3 agent/run.py --step benchmark_registry` | build the legitimate content-addressed registry |
| **sanskrit_texts** | `python3 agent/run.py --step sanskrit_texts` | index the 254 DCS/GRETIL source texts |
| **benchmark_report** | `python3 agent/run.py --step benchmark_report` | per-school × per-tier leaderboard |
| **gold** | `python3 agent/run.py --step gold` | the fixed gold control summary |
| **comet** | `python3 agent/run.py --step comet` | COMET learned metric (needs torch) |
| **frontier** | `python3 agent/run.py --step frontier` | the imported frontier datasets (Sāmayik/Itihāsa) |
| **watchdog** | `python3 agent/run.py --step watchdog` | a full validate→hypothesize→report cycle |

> Every step appends to the centralized trace (`agent/trace.py --recent`). **If it isn't in the trace,
> it didn't happen.**

## 2. THE VERIFICATION TOOLS

| Tool | Command | What it proves |
|---|---|---|
| `agent/verify.py` | `python3 agent/verify.py --source "…" --candidate "…" --gold "…"` | proof gate + gold anti-hallucination + content-addressed record |
| `agent/verify.py --registry` | `python3 agent/verify.py --registry` | every run has a valid signature + nanopublication |
| `agent/validate_data.py` | `python3 agent/validate_data.py` | **validate every data file against its canonical schema** (the strict data gate) |
| `agent/audit.py` | `python3 agent/audit.py --bench suite` | golden-file recompute on fixed gold, fail on mismatch |
| `agent/audit.py --list` | `python3 agent/audit.py --list` | list all content-addressed runs |
| `agent/trace.py` | `--recent / --steps / --step X / --search <q> / --all` | query every run/experiment/log |
| `agent/ramwatch.py` | `python3 agent/ramwatch.py` | the RAM/CPU budget verdict (crash prevention) |
| `agent/paper_build.py` | `python3 agent/paper_build.py` | number-inject the report (numbers from logs, not prose) |

## 3. THE HERMES FEATURES

| Feature | Command | Use |
|---|---|---|
| **Skill** | `hermes ... --skills /root/sanskritbenchy/skills/sanskrit-benchy` | the lab driver |
| **Kanban** | `hermes kanban list / claim / request-review --summary / promote --reason / swarm` | task + review-gate tracking |
| **Cron** | `hermes cron create ... --script ... --no-agent` | the daily watchdog |
| **Hooks** | `hooks:` block in `~/.hermes/config.yaml` | auto-run verify on task-complete |
| **MCP serve** | `hermes mcp serve` | expose the lab's verified tools to other agents |
| **Memory** | `hermes memory` / built-in MEMORY.md | persist decisions (anti-regression) |
| **DML memory** | `python3 agent/run.py --step memory --search <q>` | the deterministic temporal memory (event-sourced decisions) |
| **Tree search** | `python3 agent/run.py --step tree_search` | metric-grounded strategy search (AIDE) |
| **Re-render** | `python3 agent/run.py --step render --n 4` | re-render a passage into equally-valid translations |
| **Fine-tune data** | `python3 agent/run.py --step finetune --n 5` | build LoRA-ready register-pair data |
| **Engram** | `~/engram` (installed on hermes) | learn/review/coach — the blind-assessor memory |
| **moa** | `/moa <prompt>` | ensemble grading (multiple models) |

## 4. THE STANDARD RECIPES

### Recipe A — prove the metric beats chrF (the first real number)
```bash
cd /root/sanskritbenchy
python3 agent/run.py --step validate                      # gate first
python3 agent/run.py --step benchmark --n 1              # or eval --n 10 --judge
python3 agent/verify.py --registry                       # every result is content-addressed
python3 agent/trace.py --recent                          # see it logged
```
> Read the tau in the output; if our metric > chrF, that's the proof. Log it as a nanopublication.

### Recipe B — the full progressive-difficulty benchmark
```bash
cd /root/sanskritbenchy
python3 agent/run.py --step benchmark_registry           # the fixed gold (content-addressed)
python3 agent/run.py --step sanskrit_texts               # index the source texts
python3 agent/run.py --step benchmark --n 2              # dealradar picks model per tier → translate → proof
python3 agent/run.py --step benchmark_report             # per-school × per-tier leaderboard
```

### Recipe C — verify a specific translation is faithful (the Pāṭala proof)
```bash
cd /root/sanskritbenchy
python3 agent/run.py --step verify --source "śivāya namaḥ" --candidate "Homage to Shiva" --gold "Homage to Shiva"
# → VERIFIED (proof gate PASS + gold chrF match + content-addressed record)
```

### Recipe D — audit for theater (the anti-mess check)
```bash
cd /root/sanskritbenchy
python3 agent/audit.py --list          # every result has a content-addressed signature
python3 agent/audit.py --bench suite   # recompute on fixed gold; must match golden
python3 agent/trace.py --all           # every run is logged
```
> Any number with no run record / failing the golden audit is flagged as theater.

### Recipe E — check the box can take a heavy job (crash prevention)
```bash
python3 agent/ramwatch.py   # SAFE (avail ≥1GiB, load <3) / CAUTION / CRITICAL
```

### Recipe F — the full re-render → fine-tune → verify flow (the product vision)
```bash
cd /root/sanskritbenchy
python3 agent/run.py --step checkpoints      # the vision→checkpoint DAG (what's next)
python3 agent/run.py --step render --n 4     # re-render a passage → equally-valid set
python3 agent/run.py --step finetune --n 5   # build LoRA-ready register-pair data
python3 agent/run.py --step verify --source "…" --candidate "…" --gold "…"   # VERIFIED kind
python3 agent/run.py --step tree_search      # metric-grounded strategy search (improve the render)
python3 agent/run.py --step memory --search <q>   # remember/query past decisions
```
> This is the autonomous product loop: vision → checkpoint → re-render (equally-valid) → fine-tune data →
> verify → strategy-improve → remember.

### Recipe G — expand the lab with a new capability (the proper way)
1. Write the new module in `pipeline/` (deterministic, stdlib, stream — never bulk-load).
2. Add a `step_<name>` in `agent/run.py` + register it in `STEPS` + `main()` dispatch.
3. Register it in `MANIFEST.json` (`implementation` entry with a validator).
4. Add a test (in `agent/run.py --step validate` or a test file).
5. Run `check.py --status` + `trace.py --all` to confirm it's registered + logged.
6. Update the skill (`skills/sanskrit-benchy/SKILL.md`) so the agent knows the new command.
7. Timestamp + log: any note carries a date; any run goes through the orchestrator.

## 5. HOW TO EXPAND THE LAB PROPERLY (the growth path)

### The 5-rule expansion checklist
1. **New capability → new module + orchestrator step + MANIFEST entry + skill line.** Nothing is "real"
   until it's agent-callable (`agent/run.py`), registered, and logged.
2. **New data → import via a loader + content-address it.** Gold is the fixed truth; never inline data in
   a doc.
3. **New metric → wire it into `benchmark_runner` + `verify`.** Compare its tau vs chrF/bleu on the SAME
   fixed gold.
4. **New claim → a logged number on fixed gold, or it's theater.** Run `verify.py` + `audit.py`.
5. **New doc → register in MANIFEST + timestamp + reference, don't copy.**

### The roadmap (from GOALS.md)
- **Phase 1**: first real Kendall's-tau (validate + audit). ⬜ immediate.
- **Phase 2**: COMET baseline (needs torch/GPU box).
- **Phase 3**: school/period conditioning (the *vimarśa* test).
- **Phase 4**: Sanskrit DA/MQM human gold (the long-term asset).
- **Phase 5**: crypto-commitment proof of translation (hash/Merkle + attestation).
- **Phase 6**: persona-translation product (per-persona LoRA + verify + license).

### To add a hermes skill for a new project
1. Write `skills/<name>/SKILL.md` (frontmatter: name, description, date, tags + body: command map, rules).
2. Verify it loads: `hermes ... --skills <path>` and ask it to read the skill.
3. Register in that project's `MANIFEST.json` + `AGENTS.md`.

---

*Every recipe ends the same way: a logged, content-addressed result in the trace, verified by a
deterministic gate, on fixed gold. If a recipe doesn't produce that, it isn't done.*
