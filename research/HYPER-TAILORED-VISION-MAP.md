# THE HYPER-TAILORED RESEARCH MAP — every paper + mechanism → OUR vision

*2026-08-16 · The definitive review of all 32 curated arXiv papers + every cloned mechanism, explicitly
mapped to OUR exact vision: take a full Sanskrit text → re-render passages into multiple equally-valid
translations → build fine-tuning data (plain/precise registers) → run the whole thing as an autonomous
science lab that works toward goals with the scientific method. This is the "what's directly ours" map, not
a generic survey.*

---

## 0. OUR VISION, RESTATED (the target every paper maps to)

> **A full Sanskrit text → re-render each passage into N equally-valid English translations (verified by
> our ML system) → build fine-tuning data (plain / precise / literal / natural registers) → per-register
> LoRA adapters → license the verified + attributable result. The whole pipeline runs autonomously: a
> vision decomposes into a checkpoint DAG, the agent searches strategies (AIDE), verifies every number
> (nanopublication + proof gate), remembers decisions (Engram/DML), and writes a grounded paper (storm/
> paper-qa) — with the school/period lemma-sense as the moat (darshana-graph).**

The three pillars of "ours": **VERIFY** (benchmark), **PROVE** (Pāṭala proof), **RENDER + FINE-TUNE**
(the product). The autonomous layer sits on top of all three.

---

## 1. THE AUTONOMOUS-SCIENCE PAPERS → the goal-hitting + strategy layer

| Paper | Mechanism | → OUR vision |
|---|---|---|
| **2502.13138 AIDE** | metric-grounded tree search — every node scored by a REAL computed metric, never an LLM opinion | ⭐ **THE strategy loop.** We built `tree_search.py`: it proposes translation-strategies (prompt hints), scores each by semantic-fidelity on fixed gold, expands the best. This is how the lab autonomously *improves* the re-render/fine-tune pipeline. |
| **2502.14297 Evaluating Sakana's AI Scientist** | the honest critique — agents hallucinate results, circular review | ⭐ **Our anti-theater guardrail.** Tells us WHY our verify layer (nanopub + proof gate + only-cite-real-edges) is non-negotiable. |
| **2504.08066 AI Scientist-v2** | agentic tree search over experiment *strategies* | ⭐ **Our checkpoint DAG + tree_search.** The vision decomposes into checkpoints (what to do); tree_search decides how to do each one. |
| **2502.18864 AI Co-Scientist** | tournament/evolution over hypotheses | The hypothesis_lab's next evolution — tournament-select which strategy to try. |
| **2512.23760 Audited Skill-Graph Self-Improvement via Verifiable Execution** | agents improve their OWN skills, gated by verifiable execution | ⭐ **Our skill/checkpoint system.** The lab's skills (sanskrit-benchy) self-improve only when a verified result backs them. |
| **2608.03392 Self-Evolving Coding Agents** | agents that evolve their own code/skills | The fine-tune/rendering pipeline self-evolves toward better registers. |
| **2505.22954 Darwin Godel Machine** | open-ended evolution of self-improving agents | The long-term autonomous loop (roadmap). |
| **2606.21228 Sakana Fugu** | the AI-Scientist production infra | Our `agent/run.py` + kanban + cron is the analogous orchestration. |

## 2. THE MEMORY + KNOWLEDGE-GRAPH PAPERS → the "remembers" + domain layer

| Paper | Mechanism | → OUR vision |
|---|---|---|
| **2310.08560 MemGPT** | LLM as an OS with memory paging | ⭐ The agent's memory model — what our `agent/memory.py` (DML) + Engram approximate. |
| **2605.12061 SAGE** | self-evolving agentic graph-memory engine | ⭐ Structure-aware memory for the lab — the domain graph (darshana) as agent memory. |
| **2607.03726 SelfMem** | self-optimizing memory | The fine-tune/register data self-optimizes which registers help. |
| **2407.04363 AriGraph** | learn a knowledge graph from text | Build the lemma→school/period sense graph from the Sanskrit gold. |
| **2307.07697 Think-on-Graph / 2407.10805 ToG-2** | graph-guided reasoning | Route a passage through the darshana-graph before re-rendering (school-correct sense). |
| **2502.14902 PathRAG** | graph-RAG with path pruning | Retrieve the RIGHT school/period context before translation. |
| **2605.25480 Retrieval as Reasoning** | self-evolving agent-native retrieval | The retrieval layer that finds the correct gold/lemma context. |

## 3. THE VERIFICATION + TOOL-AGENT PAPERS → the "it's true" layer

| Paper | Mechanism | → OUR vision |
|---|---|---|
| **2606.01416 Self-Healing Agentic Orchestrators** | orchestrators that recover from failures | ⭐ Our watchdog (validate → hypothesize → report) auto-recovers. |
| **2607.11138 Formal Hierarchical Agentic Architecture** | a formal stack for agent orchestration | Our layered design (hermes → lab → verification) is this. |
| **2512.11147 MiniScope** | least-privilege tool authorization | The `--yolo`/approvals/egress safety for autonomous runs. |
| **2406.12045 tau-bench** | tool-agent-user interaction benchmark | A benchmark model for our re-render "equally valid" eval. |
| **2412.21139 Training SWE Agents + Verifiers** | train agents AND verifiers together | ⭐ Our verify.py (verifier) is trained/validated alongside the translator. |

---

## 4. THE MECHANISMS ALREADY BUILT → what each maps to (the "we already did this" map)

| Mechanism (source) | Where we built it | → Our vision |
|---|---|---|
| **metric-grounded tree search** (AIDE) | `pipeline/tree_search.py` | the autonomous strategy loop for improving re-render/fine-tune |
| **content-addressed run record** (DVC) | `run_recorder.py` | every re-rendered variant + fine-tune pair is content-addressed |
| **nanopublication** (sensein/ECO) | `run_recorder.py` | every claim = {assertion, evidence, provenance} |
| **eigenius 4-kind ladder** (eigenius) | `run_recorder.py` `kind` field | every result is Declared/Observed/Derived/Verified |
| **golden-file audit** (DVC) | `agent/audit.py` | recompute on fixed gold; fail on mismatch |
| **only-cite-real-edges** (darshana-graph) | `translation_proof.py` CITATION_GROUNDING | a re-render can't invent a term not in source |
| **number-inject templating** (AI-Scientist) | `agent/paper_build.py` | the re-render report's numbers come from the logs |
| **blind-assessor memory** (Engram) | `~/engram` (installed) | learn/review the fine-tune knowledge properly |
| **event-sourced deterministic memory** (RKA/DML) | `agent/memory.py` | the agent remembers past decisions (anti-regression) |
| **baseline-per-machine** (AI-Scientist) | `sanskrit_gold.py` clean_exemplars | every re-render compares vs our own fixed gold, not literature |

---

## 5. THE HYPER-TAILORED AUTONOMOUS VISION (the one diagram)

```
A FULL SANSKRIT TEXT (darshana-graph school/period context + DCS↔SH morphology)
   │
   ▼  checkpoint DAG (checkpoint.py) — decompose the vision into falsifiable gates
agent works the NEXT checkpoint (autonomous)
   │
   ▼  AIDE tree_search — propose re-render strategies, score each by REAL semantic on fixed gold
   │
   ▼  RE-RENDER (renderer.py) — N register-candidates (literal/plain/precise/natural)
   │      → keep the EQUALLY-VALID set (proof gate PASS + semantic ≥ threshold)
   │      → each variant content-addressed + eigenius-kind labeled
   │
   ▼  FINE-TUNE (finetune_builder.py) — LoRA-ready register-pair data from gold + valid re-renders
   │
   ▼  VERIFY (verify.py: proof gate + CITATION_GROUNDING + gold anti-hallucination)
   │      → VERIFIED kind only when a real number on fixed gold says so
   │
   ▼  MEMORY (Engram + DML) — learn/review + remember past decisions
   │
   ▼  PAPER (storm/paper-qa → number-inject) — the citable, grounded result
   │
   ▼  LICENSE — the verified, attributable translation capability
```

**The honest rule (unchanged, now fully grounded):** every re-rendered variant and every fine-tune pair is
real only when it is a machine-computed, content-addressed, epistemically-labeled value on fixed gold,
passed by a deterministic gate. The 32 papers + cloned mechanisms give us the TOOLS; our verification
layer keeps them honest.

---

*This is the hypertailored map. Every paper above either IS already built into our lab (the mechanisms
column) or is the reference for the next capability (the memory/knowledge-graph evolution). The vision is
real and the autonomous layer is in place — the papers are the roadmap, our verification is the spine.*
