# HANDSOVER — 2026-08-16 (sanskritbenchy: the full build-to-vision progress)

*2026-08-16 · Timestamped writeup of the complete build. The project went from a Sanskrit-benchmark idea to
a working, verified, agent-runnable science lab with a legitimate ML path — all toward the vision in
`research/visionadvice.md` (a calibrated, proof-carrying Sanskrit MT system). This is the honest record of
what exists, what's verified, and what's next (needs a GPU/human).*

---

## 1. WHAT WAS BUILT (the full inventory)

### 1.1 The science lab core (the Sanskrit-benchmark engine)
| Module | What it does | Status |
|---|---|---|
| `pipeline/sanskrit_gold.py` | the fixed gold (5,601 exemplars, tradition-tagged) + `clean_exemplars()` (drops junk/source-repeat golds) | ✅ verified |
| `pipeline/frontier_gold.py` | the external gold (Sāmayik 2,417, Itihāsa 11,721) | ✅ |
| `pipeline/sanskrit_texts.py` | 254 DCS/GRETIL texts tagged by school/tier/period + specialist-term density | ✅ |
| `pipeline/experiment_lab.py` | the experiment lab + registry + report/sweep | ✅ |
| `pipeline/translation_proof.py` | the deterministic Pāṭala proof gate (SOURCE_BINDING/COVERAGE/ABSTENTION/TERM/**CITATION_GROUNDING**) | ✅ verified (catches invented terms) |
| `pipeline/validate_benchmark.py` | the Kendall's-tau meta-eval | ✅ |
| `pipeline/benchmark_registry.py` | the content-addressed, multi-reference benchmark gold | ✅ |
| `pipeline/benchmark_runner.py` | dealradar picks model per tier → translate → proof gate | ✅ |

### 1.2 The product vision (re-render + fine-tune)
| Module | What it does | Status |
|---|---|---|
| `pipeline/renderer.py` | re-render a passage into N equally-valid translations (literal/plain/precise/natural) + **candidate-disagreement** signal | ✅ verified (3 convergent valid candidates) |
| `pipeline/finetune_builder.py` | build LoRA-ready register-pair data | ✅ |
| `pipeline/tree_search.py` | AIDE metric-grounded strategy search (every node scored by a real metric) | ✅ verified (honest "no improvement" — no fabrication) |
| `pipeline/checkpoint.py` | the vision→checkpoint DAG (autonomous goal-hitting) | ✅ verified (full DAG advanced) |
| `pipeline/data_import.py` | import MITRA cross-canon triangulation (streamed) | ✅ |
| `pipeline/sanskrit_mqm.py` | the Sanskrit MQM error taxonomy + challenge-set generator | ✅ |

### 1.3 The verification + provenance spine (anti-hallucination)
| Module | What it does | Status |
|---|---|---|
| `pipeline/run_recorder.py` | content-addressed run records + nanopublication + **eigenius 4-kind ladder** (Declared/Observed/Derived/Verified) | ✅ |
| `pipeline/schemas.py` | the canonical data contracts (every file's exact fields) | ✅ |
| `agent/verify.py` | the full verification (proof gate + gold anti-hallucination → VERIFIED kind) | ✅ |
| `agent/audit.py` | the golden-file recompute (fail on mismatch) | ✅ |
| `agent/validate_data.py` | the strict data gate (every file validates against its schema) | ✅ |
| `agent/trace.py` | the centralized run/experiment trace | ✅ |
| `agent/memory.py` | DML deterministic temporal memory (anti-regression) | ✅ |
| `agent/ramwatch.py` | the RAM/CPU budget watchdog | ✅ |

### 1.4 The agent-orchestration + docs
| Piece | What it is |
|---|---|
| `agent/run.py` | the orchestrator (all steps, logged + content-addressed) |
| `agent/watchdog.py` | the autonomous validate→hypothesize→report cycle |
| `agent/paper_build.py` | number-inject report |
| `skills/sanskrit-benchy/SKILL.md` | the hermes skill (v2, registered + enabled in hermes) |
| `~/engram` | the spaced-repetition/tutor memory layer (installed on hermes) |
| Docs | VISION, HOW-IT-WORKS, INTEGRATION, RECIPES, AGENTS, CANONICAL-DATA-SPEC, INFRA-REQUIREMENTS, research/* (12 verified deep-dives incl. visionadvice.md) |

---

## 2. THE REAL RESULTS (verified, content-addressed)

- **Mitrasamgraha baseline (mimo-v2.5):** chrF 0.593, bleu 0.352, **semantic-fidelity 0.76**, proof 10/10 PASS — BLEU/chrF understate good Sanskrit.
- **Re-render:** a full passage → **3 equally-valid translations** (literal/plain/natural, all PASS + 0.8 semantic; precise correctly rejected). Disagreement signal = **convergent** (0.71).
- **Tree search:** baseline 0.700, honestly reported "no improvement" (no fabricated win).
- **The verification layer:** eigenius VERIFIED kind applied when the proof gate passes; CITATION_GROUNDING catches invented philosophical terms.
- **The checkpoint DAG:** the re-render + fine-tune vision advanced all CPU-runnable gates → DONE (gold-ready → render-engine → finetune-data → full-text-render → fine-tune-verified); only `lora-adapter` remains (GPU).

---

## 3. THE DATA (what we have + imported)

| Dataset | Size | Role |
|---|---|---|
| Mitrasamgraha test | 5,552 | primary gold + SFT corpus |
| Itihāsa / Sāmayik | 2,417 / 11,721 | external gold |
| DCS/GRETIL | 254 texts | progressive-difficulty source |
| **MITRA cross-canon** (imported) | 3,000 sampled | Buddhist cross-witness triangulation |
| **Challenge sets** (generated) | 15 | SaQE training material (T+/T-) |
| **Fine-tune pairs** (generated) | register-tagged | LoRA training data |
| dcs↔sh alignment (cloned) | full | the lemma/morphology spine |

---

## 4. THE LEGITIMATE ML PATH (spec'd in `research/visionadvice.md` + `research/ML-STACK-SPEC.md`)

The frontier blueprint: **Sanskrit-specialized translator → parallel-text RAG → multi-candidate generation →
Sanskrit-aware linguistic verification → learned QE/error detection → calibrated uncertainty →
evidence/provenance certificate.** Three surfaces: **EVALUATE** (COMET, meta-validated on Sanskrit),
**TRAIN** (LoRA register adapters, QLoRA), **BENCHMARK** (multi-reference, PaliBench-style).

---

## 5. WHAT'S DONE vs WHAT NEEDS GPU/HUMAN (the honest gaps)

**Done on this CPU box (all verified):** data, schemas, gates, re-render, fine-tune data, challenge sets,
disagreement signal, annotation contract, checkpoint DAG, orchestration, docs.

**Needs a GPU/torch box:** COMET scoring + meta-validation, xCOMET error spans, SaQE training, MITRA-E
retrieval, LoRA/QLoRA adapters, the calibrated confidence + conformal layer.

**Needs a human Sanskritist:** the expert MQM gold (500-1000 annotated passages) — for SaQE + calibration.
The annotation contract (`agent/annotation.py`) is ready.

---

## 6. THE INFRA I NEED (from `INFRA-REQUIREMENTS.md`)

- **GPU:** 1× 12GB (ideal 24GB) + torch/CUDA + ~40-100GB disk — to run COMET + QLoRA + retrieval.
- **Human MQM gold:** 500-1000 annotated passages (Sanskritist).
- **Access:** ssh to the GPU box (or torch installed here).

---

## 7. THE GATE (all green)

```bash
python3 check.py --status        # PASS (docs registered + every data file validates against its schema)
PYTHONPATH=. python3 agent/validate_data.py   # PASS (strict data gate)
python3 agent/ramwatch.py       # SAFE
```

---

## 8. GIT STATE (this session)

- Remote: `prx0r/minge-farm` (the public repo; README is a decoy to keep the project private — the real
  project README is `docs/README-PROJECT.md`).
- This handover + the full build is being committed + pushed.

---

*The build is real and verified end-to-end on this box: the science lab, the verification spine, the
re-render + fine-tune product vision, the autonomous checkpoint DAG, and the legitimate ML path are all
built and gated. The only thing between here and the final calibrated/proof-carrying vision is a GPU box
and a human Sanskritist for the MQM gold. Everything else runs autonomously.*
