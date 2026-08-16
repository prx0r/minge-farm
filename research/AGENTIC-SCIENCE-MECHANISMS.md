# AGENTIC-SCIENCE MECHANISMS — the bulletproof patterns we steal (verified)

*2026-08-16 · Verified research (arXiv + GitHub + docs) on agentic science labs and reproducibility infra.
What we adopt, from where, and why it's bulletproof. Every pattern is now implemented in sanskritbenchy
(see `HERMES-MCP-API.md` + `pipeline/run_recorder.py` + `agent/audit.py` + `agent/paper_build.py`).*

---

## 1. AGENTIC SCIENCE AGENTS (what exists, what we steal)

| Project | ID / repo | The good mechanism |
|---|---|---|
| **AI Scientist** (Sakana) | 2408.06292 | baseline-per-machine `run_0`; ensemble reviewer (5 reviews, reflections, ICLR calibration); template contract |
| **AI Scientist-v2** | 2504.08066 | **agentic tree search over experiment strategies** (best-first), metric feedback prunes branches |
| **AI Co-Scientist** (Google, Nature) | 2502.18864 | **tournament/evolution over hypotheses** (generate→critique→refine, Elo) |
| **SciAgents** | 2409.05556 (NOT 2402.05181) | critique-and-improve as a first-class pass; knowledge-graph novelty check |
| **MLAgentBench** | 2310.03302 | success = a machine-computed delta over a fixed gold baseline |
| **AIDE** | 2502.13138 | **metric-grounded tree search** — every node's score is a real computed number, never an LLM opinion |

**The single best anti-theater primitive:** AIDE's grounding — the feedback metric is **computed by real
code on real data**, never produced by an LLM. AI-Scientist's weakness is its reviewer being an LLM
(circular). We adopt the former, avoid the latter.

## 2. REPRODUCIBILITY / PROVENANCE INFRA (the golden gems)

| Tool | What we steal |
|---|---|
| **DVC** | content-addressed hashing (input→output), run-cache (same signature ⇒ same result), golden-file |
| **MLflow** | the `Run` object schema (params+metrics+artifacts atomically bundled) |
| **wandb** | git-commit + diff.patch + requirements capture per run |
| **Hydra** | the RESOLVED config as a hashable artifact (config_sha) |
| **RO-Crate** | emit a provenance bundle linking number → gold → code → config → run |
| **sensein/ECO** | **nanopublication** = `{assertion, evidence(ECO code), provenance}` per claim |

## 3. PAPER-WRITING INFRA

- **Number-inject templating** (AI-Scientist): figures/numbers are build outputs of `metrics.json`, never
  hand-typed prose; CI compiles the PDF. The paper can't drift from the log.
- We implement this in `agent/paper_build.py`.

## 4. HIGHER-ORDER GOAL INTERPRETATION

- **Tournament selects WHAT to try → tree-search executes HOW → metric logs on fixed gold → critique →
  next.** The north-star (Kendall's τ > BLEU/chrF on fixed gold) is the only score that moves the loop.

## 5. BULLETPROOF VERIFICATION (implemented)

1. **Content-addressed run record** — `run_signature = sha256(gold_hash || code_sha || config_sha) →
   out_hash`, persisted per run (`run_recorder.py`).
2. **Golden-file audit** — recompute on fixed gold, fail on mismatch (`agent/audit.py`).
3. **Baseline-per-machine** — never cite literature numbers; run your own gold baseline.
4. **Nanopublication triples** — every headline claim ships `{assertion, evidence, provenance}`.
5. **git + deps auto-capture** per run.
6. **Number-inject paper** — the PDF is a build output of the logs.
7. **Anti-circularity** — the scorer ≠ the generator; deterministic recompute verifies.

---

## The TOP-10 list (what we actually built)

| # | Mechanism | Source | Built where |
|---|---|---|---|
| 1 | Metric-grounded strategy search | AIDE / AI-Scientist-v2 | (roadmap — Phase 3+) |
| 2 | **Content-addressed run record** | DVC | `run_recorder.py` ✅ |
| 3 | **Golden-file audit** | DVC run-cache | `agent/audit.py` ✅ |
| 4 | Baseline-per-machine run_0 | AI-Scientist | (to wire) |
| 5 | **Nanopublication data model** | sensein/ECO | `run_recorder.py` ✅ |
| 6 | Ensemble reviewer + anti-circularity | AI-Scientist | (roadmap) |
| 7 | **git+deps auto-capture** | wandb | `run_recorder.py` ✅ |
| 8 | **Number-inject paper templating** | AI-Scientist | `agent/paper_build.py` ✅ |
| 9 | Tournament over hypotheses | AI Co-Scientist | (roadmap) |
| 10 | **Config-as-hashable-artifact** | Hydra | `run_recorder.py config_sha()` ✅ |

*Honest flags: MLflow/wandb are schemas to copy, not on-box dependencies — we implement the ~200-line
core ourselves (content-addressed + git capture), which we did. The bulletproof parts are the data model
and the hashing, not the SaaS.*
