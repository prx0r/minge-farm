# HERMES VERIFICATION ARCHITECTURE — how hermes features enforce our crypto/provenance anti-hallucination layer

*2026-08-16 · A deep map of every Hermes feature and how it plugs into sanskritbenchy's / dealradar's
verification stack. The goal: **make hallucination deterministically impossible** by combining Hermes'
orchestration (kanban swarm, review-gates, memory, hooks, MCP) with our content-addressed provenance
(`run_recorder.py`) and the deterministic Pāṭala proof gate + golden audit (`audit.py`).*

---

## 1. THE CORE INSIGHT (why hermes + our crypto layer beats a lone model)

A lone LLM hallucinates because it has no checkable ground truth. Hermes provides the **orchestration
scaffold** (who does what, review-gates, memory of prior decisions); our layer provides the **ground
truth** (content-addressed run records on fixed gold + deterministic proof gates). Together:

> **Hermes decides WHAT and orchestrates WHO reviews; our crypto layer proves the RESULT is real —
> machine-computed on fixed gold, content-addressed, unaltered.**

The two anti-hallucination pillars:
1. **Anti-circularity** — the scorer ≠ the generator. Hermes routes work so a DIFFERENT agent/profile
   verifies than the one that produced (kanban swarm's verifier role).
2. **Grounding** — every number traces to a content-addressed run record (run_recorder) + a deterministic
   recompute (audit.py). A claim with no record is flagged as theater.

---

## 2. THE FEATURE → VERIFICATION MAP (everything hermes offers)

### 2.1 Kanban — the task + REVIEW-GATE backbone (⭐ the main verification mechanism)
| Feature | What it does | Anti-hallucination use |
|---|---|---|
| `kanban create` / `claim` | atomic task ownership | a task is worked by ONE agent at a time (no double-write to the registry) |
| `kanban request-review --summary --metadata` | move to review with a handoff summary | **the "what I implemented + how I verified it" gate** — forces the worker to state evidence |
| `kanban request-changes` / `reopen-review` | reviewer rejects | the human/verifier check — a claim that doesn't pass is bounced back |
| `kanban promote --reason` | final approval + audit-trail reason | **promotion only on a logged reason + passing gate** — recorded on the task_events row |
| `kanban swarm --worker --verifier --synthesizer` | parallel workers → **verifier** → synthesizer | **anti-circularity**: a different profile verifies the workers' output before synthesis |
| `kanban dispatch --failure-limit` | auto-block after N failures | a task that keeps failing is blocked, not silently retried |
| `kanban decompose` | break a goal into sub-tasks | a big claim → many small verifiable claims |

### 2.2 Goals (the `/goal` + `--goal` mechanism) — higher-order gate
A **goal** is a continuing, stated outcome the agent works toward across a session. Used as a **verification
anchor**: the goal defines the acceptance test. E.g. "reach a logged Kendall's-tau > chrF on mitrasamgraha"
— every intermediate result is checked against this north-star, not just "did something interesting."

### 2.3 Cron — scheduled verification (the watchdog)
`hermes cron` with `--no-agent` + `--script` runs the watchdog daily: refresh → canary → validate → report,
and **delivers the output** so the numbers are re-checked on a schedule. `--monitor-script` can gate a
cheap pre-check before a heavier run.

### 2.4 Memory / Learning — the institutional memory (anti-regression)
- **Built-in memory (MEMORY.md / USER.md)** — persists decisions so the agent doesn't re-hallucinate what
  was already decided.
- **Memory providers (honcho, mem0, hindsight, retaindb)** — external memory; the lab's run records are
  effectively its memory (content-addressed, so never stale).
- **Skills auto-created from experience** — the lab skill `sanskrit-benchy` encodes the verified workflow.

### 2.5 MCP serve — expose the lab's VERIFIED surface to other agents
`hermes mcp serve` exposes the lab's tools (benchmark, proof, audit, registry) as MCP. Other agents get the
content-addressed results, not a model's opinion — **the lab's verified output becomes a tool other agents
trust.**

### 2.6 Hooks — auto-verify on events
`hooks` run shell scripts on hermes events. **The killer use: run `check.py --status` + `audit.py` after
every task-complete**, so a change that breaks the gate is caught immediately. `--accept-hooks` in cron
auto-approves them (headless).

### 2.7 egress (iron-proxy) — supply-chain integrity
TLS-intercepting egress firewall; swaps proxy tokens for real credentials. **Anti-supply-chain-attack**:
prevents a compromised agent from exfiltrating secrets. (Verification of the ENVIRONMENT, not the result.)

### 2.8 security audit (OSV.dev) — dependency integrity
`hermes security audit` scans venv/plugins/MCP deps against OSV.dev. **Verifies the code isn't compromised**
before we trust a run's provenance. (Found 12 moderate findings — pip, etc.)

### 2.9 verify — project smoke-test
`hermes verify` detects the build/test/start recipe + runs it. **Verifies the project is runnable** — a
prerequisite for trusting its outputs.

### 2.10 moa (mixture of agents) — ensemble verification
`/moa` routes a prompt through multiple model slots. **Ensemble-checking**: multiple models grade a
translation → a consensus, reducing single-model hallucination. (The anti-circularity variant: the graders
≠ the generator.)

### 2.11 approve/approvals — human-in-the-loop gates
`approvals` mines approval history into an allowlist. **Verification of ACTIONS** (what the agent is allowed
to run) — a permission layer on top of the result-verification.

---

## 3. THE END-TO-END ANTI-HALLUCINATION PIPELINE (how they combine)

```
GOAL (the north-star acceptance test, e.g. "logged tau > chrF on fixed gold")
   │
   ▼  kanban decompose → tasks
worker claims task → runs agent/run.py --step X   (the orchestrator, hermes model)
   │
   ▼  result → run_recorder.py (content-addressed: sha256(gold‖code‖config) → out_hash + nanopublication)
   │
   ▼  deterministic proof gate (translation_proof.py) + audit.py (recompute on fixed gold, fail on mismatch)
   │
   ▼  kanban request-review --summary --metadata   (the worker states its evidence)
reviewer (DIFFERENT profile — anti-circularity) checks it against the goal
   │
   ├─ request-changes → back to worker   (failed verification bounces)
   └─ promote --reason → approved, audit-trail recorded
   │
   ▼  hooks: on complete → auto-run check.py + audit.py (the gate is enforced, not assumed)
   │
   ▼  cron watchdog re-validates daily; mcp serve exposes the verified results to other agents
```

**Every stage leaves a content-addressed, timestamped, logged trace (`agent/trace.py`). If it isn't in the
trace, it didn't happen.**

---

## 4. THE HONEST LIMITATIONS (what hermes + our layer CANNOT verify)

1. **Human ground truth** — our layer verifies *computation* (this run → this number, on fixed gold) and
   *internal consistency* (proof gate, golden audit). It cannot verify *semantic correctness* against expert
   human judgment — that needs the expert MQM gold (Phase 4, human-in-the-loop).
2. **The crypto layer proves integrity, never quality** — a zkML/EZKL proof says "this model ran on these
   inputs → this output," not "this translation is good."
3. **Detection-based decontamination is unreliable** — only prevention (private holdout + fresh
   timestamped sources) works; detection is best-effort disclosure.
4. **Hermes `security audit` finds real vulns** — a compromised dependency undermines provenance trust; run
   it regularly (found 12 moderate findings).

---

## 5. THE RULE

> **Hermes decides WHAT and orchestrates WHO reviews; our crypto/provenance layer proves the RESULT is real
> (content-addressed on fixed gold, deterministic proof gate, golden audit). Anti-circularity: the reviewer
> ≠ the generator (kanban swarm). Every stage is logged to the trace. If a claim has no content-addressed
> run record AND no review-gate pass, it is theater.**
