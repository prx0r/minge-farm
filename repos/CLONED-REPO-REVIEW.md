# THE CLONED-REPO REVIEW — what powers a fully-autonomous science lab

*2026-08-16 · A comprehensive review of every relevant cloned repo across `patalacheckpoints/source-
evidence/repos/` and `fuck-off/ecosystem/`, plus the 32 curated arXiv papers. Organized by what each gives
us toward the vision: an autonomous science lab that works toward goals with the scientific method, verified
end-to-end.*

---

## 1. THE BIG PICTURE (what the ecosystem already gives us)

We have **everything needed** for a legitimate autonomous science lab — the pieces are cloned, verified,
and mature. The synthesis:

```
AUTONOMOUS GOAL-HITTING (checkpoint.py + kanban swarm + goals)      ← the "what" + "don't move on"
SCIENTIFIC METHOD (hypothesis_lab + metric-grounded search)          ← the "how it reasons"
MEMORY + LEARNING (engram, graphiti, MemOS, eigenius, RKA)           ← the "keeps knowledge"
VERIFICATION (nanopublication, run_recorder, proof gate, audit)      ← the "it's true"
KNOWLEDGE GRAPH (darshana-graph, emptiness-graph, adaptive-kg)       ← the "domain understanding"
TUTORING (DeepTutor, learner-modeling, pyBKT)                        ← the "teaches a human"
PAPER-WRITING (storm, paper-qa, scifact, literature-review-toolkit)  ← the "publishable result"
```

---

## 2. THE NEWLY-LISTED REPOS (reviewed)

### ⭐ Engram (nagisanzenin/engram) — the LEARNING + memory system (the top find)
- **What:** a spaced-repetition/tutor system that runs natively on **Hermes** (`INSTALL-HERMES.md`,
  verified). A **blind assessor** (isolated subagent) checks you actually learned it; **FSRS-4.5** scheduler
  brings ideas back before you forget; **307/307 self-tests**; 100% local.
- **Why it matters:** this is the *"keep the knowledge, learn it properly"* layer — both for a human user
  AND as a memory discipline. `/learn` → `/review` → `/coach` works on Hermes.
- **Steal:** the blind-assessor isolation pattern (assessor ≠ generator), the FSRS scheduler, the receipt/
  self-test rigor.

### ⭐ Darshana-graph + darshana-temporal-analysis (joyboseroy) — OUR VISION, BUILT
- **What:** a **text-grounded knowledge graph of Indian philosophy** (Hindu darshanas + Buddhist Pali +
  Jain), aligned across translators, with **diachronic sense disambiguation** (arXiv:2606.18222, 2606.29070).
  Plus a **debate simulator** where agents can only cite REAL graph edges — fabricated citations are
  programmatically rejected.
- **Why it matters:** this is exactly our school/period-conditioned lemma-sense vision, already built and
  published. **The debate-simulator anti-hallucination (only-cite-real-edges) is the model for our
  verification.**

### ⭐ DCS↔SH alignment (SriramKrishnan8) — the Sanskrit morphology/lemma layer
- **What:** aligns the **Digital Corpus of Sanskrit** (650k annotated sentences) with the **Sanskrit
  Heritage** analyzer — full morphological + lexical analyses per sentence. 
- **Why it matters:** the lemma→sense spine for our term-density + *vimarśa* tests, already computed.

### DeepTutor (HKUDS) — lifelong personalized tutoring
- **What:** a full lifelong tutoring platform (personalization, spaced repetition, multi-agent).
- **Why it matters:** the tutor layer for the education product; patterns to borrow for the learner loop.

### Adaptive Knowledge Graph + Agetor + beads + vouch
- **adaptive-knowledge-graph:** grounded learning over a knowledge graph with citations (the demo pattern).
- **Agetor:** local-first kanban board for orchestrating coding agents in isolated git worktrees — a
  control-plane for parallel agent tasks (complements hermes kanban).
- **beads_rust/viewer:** a probabilistic-BEADs data-race detector (not relevant to our core).

---

## 3. THE AGENTIC-SCIENCE CLONES (reviewed)

| Repo | Present? | What we adopt |
|---|---|---|
| **AI Scientist** (Sakana) | ⚠️ not cloned | baseline-per-machine, ensemble reviewer, number-inject templating (we already built these in `run_recorder`/`paper_build`) |
| **AIDE** | ⚠️ not cloned | metric-grounded tree search (roadmap — the strongest anti-theater primitive) |
| **sensein/ECO** | ✅ | the **nanopublication** model `{assertion, evidence, provenance}` (built into `run_recorder.py`) |
| **RO-Crate** | ✅ | the paper-ready provenance bundle (roadmap — emit `ro-crate-metadata.json` per result) |
| **mt-metrics-eval** | ✅ | the WMT meta-eval (tau/significance) — the honest metric proof |

---

## 4. THE FUCK-OFF / IP-GRAPH ECOSYSTEM (reviewed)

### The autonomous-science agents
- **EvoScientist** — an autonomous science agent (DeepAgents framework, MCP, skills like `paper-navigator`,
  stream-JSON output protocol). A reference for headless autonomous research.
- **evolution/dgm + axplorer + openevolve** — the **Darwin-Godel-Machine** (arXiv:2505.22954) open-ended
  self-improving agents + evolution + exploration.

### The memory + epistemic substrate
- **eigenius** — the **"how-known" substrate**: typed knowledge graph with 4 epistemic kinds
  (Declared/Observed/Derived/**Verified** via Lean-4 formal proofs), content-addressed IDs, provenance.
  **This is the strongest provenance model we've seen — our nanopublication is a simplified version of it.**
- **graphiti, MemOS, neo4j agent-memory, agent-memory/cognee, node** — temporal knowledge-graph memory for
  agents (the "remember across sessions" layer).
- **RKA (replay/knowledge accumulation), infinitywings_rka, deterministic-memory-layer** — the RKA memory
  accumulation + replay patterns (we reference RKA in the organism).

### The learner-modeling + tutoring
- **learner-modeling/ (pyBKT, GKT, deep-knowledge-tracing-plus, GIKT, pykt-toolkit)** — BKT and deep
  knowledge-tracing (the tutor's learner model — the education layer).
- **open-spaced-repetition/py-fsrs** — the FSRS scheduler (already wired into our memory_scheduler).

### The Sanskrit / philosophy / argumentation
- **sanskrit/vidyut** — the morphological analyzer.
- **philosophy/, argumentation/, epistemic/knowledgeProvenance, kappa-graph** — the philosophical-epistemic
  substrate + argument-provenance tooling.

### The science-writing cluster
- **science/storm** — agentic knowledge-storm (research report writing from an outline + retrieval).
- **science/paper-qa** — grounded Q&A with citations.
- **science/scifact, EleutherIA, literature-review-toolkit** — evidence-grounded + literature review.

---

## 5. THE 32 CURATED ARXIV PAPERS (the "geniuses" — the memory/agent/science frontier)

Key ones for our vision:
- **2502.14297 — Evaluating Sakana's AI Scientist** — the honest critique of autonomous research agents.
- **2505.22954 — Darwin Godel Machine** — open-ended evolution of self-improving agents.
- **2407.04363 / 2509.24276 — AriGraph / G-reasoner** — learning/using knowledge graphs for RAG reasoning.
- **2605.12061 — SAGE** — self-evolving agentic graph-memory engine (the memory-driven science loop).
- **2607.03726 / 2310.08560 — SelfMem / MemGPT** — agent memory optimization.
- **2608.03392 — Self-Evolving Coding Agents** — code agents that improve their own skills.
- **2606.21228 — Sakana Fugu** — the AI Scientist infra.
- **2407.10805 / 2307.07697 — ToG-2 / Think-on-Graph** — graph-guided reasoning (our domain RAG).
- **2512.23760 — Audited Skill-Graph Self-Improvement via Verifiable Execution** — skill-graph self-
  improvement with verification (directly relevant to our skill/checkpoint system).

---

## 6. THE SYNTHESIS — a fully-autonomous science lab toward the vision

```
VISION → checkpoint DAG (checkpoint.py) → agent works the NEXT checkpoint
   ↓
SCIENTIFIC METHOD: hypothesis_lab (observe→hypothesize→test→keep) +
                   AIDE-style metric-grounded tree search (every node scored by a real number)
   ↓
MEMORY: engram (learn/review) + graphiti/MemOS (agent temporal memory) + RKA (accumulation)
   ↓
DOMAIN UNDERSTANDING: darshana-graph + emptiness-graph (school/period lemma-sense) +
                      dcs↔sh alignment (morphology)
   ↓
VERIFICATION (the anti-hallucination spine): nanopublication/eigenius + run_recorder +
   proof gate + audit + the debate-simulator "only-cite-real-edges"
   ↓
PAPER: storm/paper-qa/scifact → number-inject → a citable, grounded result
   ↓
TUTORING: DeepTutor + pyBKT → the learner loop (teach a human the verified knowledge)
```

**The concrete next moves (in priority order):**
1. **Install Engram on Hermes** (it's verified to work, `INSTALL-HERMES.md`) → the learn/review memory
   layer. (Do this on a safe box.)
2. **Adopt the darshana-graph debate-simulator anti-hallucination** — "only cite real graph edges" — into
   our `verify.py` (a candidate must trace to a real gold/source edge, or it's rejected).
3. **Clone AIDE** — implement metric-grounded tree search as the autonomous strategy loop (the strongest
   anti-theater primitive).
4. **Use eigenius as the provenance model** — our nanopublication is the simplified version; adopt its
   4-kind epistemic ladder (Declared/Observed/Derived/Verified) as the strict version.
5. **Wire graphiti/MemOS + RKA** as the agent's temporal memory so it "remembers" decisions across the
   checkpoint DAG (anti-regression).

---

*The ecosystem is the moat: the pieces for a legitimate autonomous science lab are already cloned, mature,
and verified. We don't rebuild them — we wire them into our checkpoint-driven, verification-gated lab.
The single highest-value adoptions: Engram (memory/learning), darshana-graph's only-cite-real-edges
(anti-hallucination), and AIDE's metric-grounded search (autonomous strategy).*
