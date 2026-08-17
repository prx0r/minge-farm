# THE INTEGRATION MAP — hermes-native build + our lab additions, one system

*2026-08-16 · How everything integrates into ONE agent-manageable system: the hermes-native orchestration
(the pieces hermes ships) + our lab additions (the Sanskrit-benchmark science layer + the verification
spine). This doc explains the boundary between the two and how they compose. Read `HOW-IT-WORKS.md` for
the mechanisms; read this for the full integration.*

---

## 1. THE ONE-LINE ARCHITECTURE

> **Hermes is the ORCHESTRATOR (who does what, when, review-gates, memory). Our lab layer is the
> EXECUTION + VERIFICATION (the Sanskrit-benchmark science, the crypto/provenance spine). Hermes drives
> the lab; the lab verifies its own output so Hermes can't hallucinate.**

```
HERMES-NATIVE (orchestration)          OUR ADDITIONS (execution + verification)
┌─────────────────────────────┐        ┌──────────────────────────────────────┐
│ kanban (tasks + review-gates)│        │ agent/run.py (every step, logged)     │
│ cron (watchdog schedule)     │──────▶ │ pipeline/* (gold, benchmark, render,   │
│ skills (sanskrit-benchy)     │ drives  │          finetune, tree_search, proof)│
│ memory/Engram (learn/review) │        │ agent/{verify,audit,trace,memory}.py   │
│ mcp serve (expose to agents) │        │      (the anti-hallucination spine)    │
└─────────────────────────────┘        └──────────────────────────────────────┘
```

---

## 2. THE HERMES-NATIVE BUILD (what hermes ships — we USE, not reinvent)

| Hermes feature | What it does | How we use it |
|---|---|---|
| **kanban board** `sanskritbenchy` | task tracking + review-gates (claim/request-review/promote) | tracks the Phase 1-7 checkpoints; the agent works the NEXT task |
| **cron** (`sanskritbenchy-daily-watchdog`) | scheduled jobs | the daily validate→hypothesize→report watchdog |
| **skills** (`sanskrit-benchy`) | the agent's "how-to" | the lab driver — loaded via `--skills`, tells the agent the command map + rules |
| **Engram** (installed at `~/engram`) | spaced-repetition + blind assessor | the learn/review memory layer (307/307 self-tests) |
| **memory** (built-in MEMORY.md) | persists decisions | anti-regression |
| **mcp serve** | expose the agent to other agents | (available) expose the lab's verified tools |
| **moa** | ensemble grading | (available) multiple models grade a translation |
| **hooks** | auto-run scripts on events | (available) auto-run verify on task-complete |

**The key point:** we adopt hermes' orchestration as-is — we do NOT reimplement kanban/cron/skills/memory.
Hermes is the brain that *decides* and *coordinates*.

---

## 3. OUR LAB ADDITIONS (the execution + verification layer we built)

### 3.1 The orchestrator (`agent/run.py`) — every step, logged + content-addressed
The single entry point an agent (or cron) calls. 19 steps, each appends to the centralized trace:

```
validate · eval · hypothesis · proof · verify · report · benchmark · benchmark_registry ·
sanskrit_texts · benchmark_report · gold · comet · frontier · watchdog ·
checkpoints (vision→DAG) · render (re-render) · finetune (fine-tune data) ·
tree_search (AIDE) · memory (DML decisions)
```

### 3.2 The pipeline (`pipeline/`) — the Sanskrit-benchmark science
- **Gold:** `sanskrit_gold.py` (5,601 exemplars) + `frontier_gold.py` (Sāmayik/Itihāsa) + `sanskrit_texts.py`
  (254 DCS/GRETIL, school/period-tagged)
- **Benchmark:** `benchmark_registry.py` (content-addressed) + `benchmark_runner.py` (dealradar picks model)
- **Product vision:** `renderer.py` (re-render equally-valid) + `finetune_builder.py` (LoRA pairs) +
  `tree_search.py` (AIDE strategy search)
- **Model:** `model.py` (hermes → mimo-v2.5, 1M ctx)

### 3.3 The verification spine (`agent/` + `run_recorder.py`) — the anti-hallucination
- **`run_recorder.py`** — content-addressed records + nanopublication + **eigenius 4-kind ladder**
- **`translation_proof.py`** — the deterministic Pāṭala gate + **CITATION_GROUNDING** (darshana-graph rule)
- **`verify.py`** — proof gate + gold anti-hallucination → VERIFIED kind
- **`audit.py`** — golden-file recompute (fail on mismatch)
- **`trace.py`** — every run, greppable
- **`memory.py`** — DML deterministic temporal memory
- **`ramwatch.py`** — the RAM/CPU budget watchdog
- **`paper_build.py`** — number-inject report from logs

---

## 4. HOW THEY INTEGRATE (the composition rules)

### 4.1 Hermes drives → the lab executes → the lab verifies → Hermes can't hallucinate

```
hermes kanban claim <task>            (Hermes decides WHAT)
   ↓
hermes --skills sanskrit-benchy       (Hermes loads the HOW)
   ↓
python3 agent/run.py --step X         (the lab EXECUTES, logs to trace)
   ↓
run_recorder → proof gate → verify    (the lab VERIFIES: content-addressed + VERIFIED kind)
   ↓
hermes kanban request-review / promote --reason   (Hermes records the gate-passed result)
```

**The boundary is clean:** Hermes never decides whether a number is true — the lab's deterministic gates
do. Hermes *proposes and coordinates*; the lab *verifies*. This is the anti-circularity that makes it
trustworthy.

### 4.2 The two memory systems (complementary, not redundant)
- **Hermes memory** (MEMORY.md / Engram) — the *agent's* memory of how to work + what to learn.
- **Our DML memory** (`agent/memory.py`) — the *lab's* auditable record of past decisions/metrics
  (anti-regression: don't re-litigate a decided checkpoint).
They compose: Engram teaches the operator, DML remembers the lab's decisions.

### 4.3 The watchdog (cron) is the autonomous heartbeat
`hermes cron` fires the daily watchdog → `agent/run.py --step watchdog` → validate/hypothesize/report →
everything logged. This is Hermes *scheduling* our lab to keep itself honest on a schedule.

### 4.4 dealradar (a sibling project) feeds the model choice
`benchmark_runner.py` calls dealradar's `routing.recommend(task, min_quality)` to pick the best model per
difficulty tier. dealradar and sanskritbenchy are separate projects that compose: dealradar = "which
model," sanskritbenchy = "how well on Sanskrit."

---

## 5. THE FULL STACK, ONE DIAGRAM

```
                    ┌────────── HERMES (orchestrator) ──────────┐
                    │ kanban · cron · skills · memory · Engram   │
                    │   (decides WHAT, WHO, WHEN; reviews)       │
                    └───────────────┬────────────────────────────┘
                                    │  drives via agent/run.py
                    ┌───────────────▼────────────────────────────┐
                    │         OUR LAB (execution + verification)  │
                    │                                            │
                    │  GOLD ──► benchmark ──► render ──► finetune │
                    │  (fixed)   (verify)   (re-render) (LoRA data)│
                    │             │  ▲                           │
                    │             ▼  │  tree_search (AIDE)       │
                    │       run_recorder + proof gate + verify   │
                    │       (content-addressed · eigenius kind · │
                    │        CITATION_GROUNDING · gold audit)    │
                    │                                            │
                    │  trace.py (every run) · memory.py (DML)    │
                    │  ramwatch.py (box safety) · paper_build.py │
                    └────────────────┬───────────────────────────┘
                                     │  feeds (dealradar picks the model)
                    ┌────────────────▼───────────────────────────┐
                    │  DEALRADAR (sibling project)               │
                    │  routing.recommend(task) → best model      │
                    └────────────────────────────────────────────┘
```

---

## 6. WHAT'S HERMES-NATIVE vs OURS (the honest boundary)

| Concern | Hermes-native (use as-is) | Ours (built) | Why |
|---|---|---|---|
| Task orchestration | ✅ kanban | — | Hermes owns this |
| Scheduling | ✅ cron | — | Hermes owns this |
| Agent "how-to" | ✅ skills | `skills/sanskrit-benchy` | our skill content, hermes loads it |
| Memory/learning | ✅ Engram + MEMORY.md | `agent/memory.py` (DML) | Engram = operator learning; DML = lab decision ledger |
| Model calls | ✅ hermes → model | `pipeline/model.py` | hermes is the kernel |
| Sanskrit science | — | `pipeline/*` | ours (the moat) |
| Verification | — | `run_recorder/translation_proof/verify/audit/trace` | ours (the anti-hallucination spine) |
| Benchmark | — | `sanskrit_gold/benchmark_*` | ours |
| Re-render + fine-tune | — | `renderer/finetune_builder` | ours (the product vision) |
| Strategy search | — | `tree_search` | ours (AIDE mechanism) |

**The rule:** we never reimplement what hermes ships (kanban/cron/skills/memory/mcp). We *extend* it with
the Sanskrit-benchmark science + verification. Hermes = the orchestrator; our lab = the verifiable executor.

---

## 7. THE AGENT-MANAGEABLE SUMMARY

> **One command to see everything:** `python3 agent/trace.py --all`
> **One command to see the vision's progress:** `python3 agent/run.py --step checkpoints`
> **One command to verify a claim:** `python3 agent/verify.py --source X --candidate Y --gold Z`
> **Hermes drives:** `hermes kanban list · hermes cron list · hermes --skills sanskrit-benchy`

**The integration is complete and coherent:** Hermes orchestrates (who/what/when + review-gates + memory),
our lab executes + verifies (every number content-addressed, epistemically-labeled, gate-passed on fixed
gold), and dealradar feeds the model choice. Nothing is reinvented; everything composes. The box stays
safe (ramwatch); the work stays honest (trace + audit + verify).
