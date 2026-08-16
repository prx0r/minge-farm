# INFRA-REQUIREMENTS — what I need to achieve the final vision autonomously

*2026-08-16 · The exact infrastructure needed to run the frontier-blueprint system (`visionadvice.md`)
autonomously. This is the ask: what I need to go from "CPU-only hermes-translated + heuristic-verified" to
"a legitimate calibrated, proof-carrying Sanskrit MT system." Everything else (code, schemas, gates,
datasets, orchestration) is already built.*

---

## 1. THE ONE-LINE STATE

**Everything that can be done on this 8GB CPU box IS DONE and verified** (the re-render, fine-tune data,
checkpoint DAG, verification gates, canonical schemas). The blueprint's *next* steps — COMET scoring, LoRA
training, a Sanskrit retrieval model, the calibrated confidence layer — all need **torch + a GPU**. That is
the only hard blocker.

## 2. WHAT I NEED (the minimum to run the blueprint's "build first" phase)

### 2.1 A GPU box with torch (the #1 requirement)
```
REQUIRED: 1× NVIDIA GPU, ≥12 GB VRAM (24 GB ideal for QLoRA + COMET-XL)
           Python 3.10+ · torch 2.x + CUDA · ~40 GB free disk for model weights
```
Why: COMET (wmt22-comet-da), xCOMET, MetricX, ByT5-Sanskrit, MITRA-E retrieval, and QLoRA fine-tuning all
need torch + a GPU. This is not optional — it's the substrate.

### 2.2 The model weights (downloadable from HuggingFace)
```
Unbabel/wmt22-comet-da        — the reference-based COMET metric
Unbabel/wmt23-cometkiwi-da    — the reference-free QE (for untranslated Sanskrit)
Unbabel/xcomet-xl             — score + error spans (the verifier/audit layer)
google/metricx-25             — learned quality (the TranslateGemma-style reward)
chronbmm/sanskrit5-multitask  — ByT5-Sanskrit (segmentation/lemmatization/morphology)
MITRA-MT + MITRA-E            — the Sanskrit-specialized translator + retrieval
(baselines) a generic Qwen/Gemma derivative for comparison
```

### 2.3 The datasets (already cloned, need importing into the training pipeline)
```
data/benchmarks/mitrasamgraha/     ✅ have — the primary SFT corpus + benchmark
mitra-parallel (cloned)            ✅ have — cross-canonical triangulation
itihasa (have) · saamayik (have)   ✅ have — auxiliary + domain control
(then acquire) Samasāmayik · SansTib · SAHAAYAK (audited) — more parallel + triangulation
```

---

## 3. THE AUTONOMOUS WORKFLOW ONCE I HAVE THE GPU (what I'll run)

```
PHASE 0 — REPRODUCE THE BASELINE (the blueprint's very first step)
  1. Run MITRA-MT · MITRA-Qwen3.5 · a generic model · deepseek-v4-flash
     over the SAME Mitrasamgraha test passages. Store every candidate (content-addressed).
  2. Run xCOMET · MetricX · GEMBA-MQM · morphology/alignment · candidate-disagreement
     over those outputs. (torch box)
  3. Annotate a strategically sampled ~500-1000 passages (oversampling disagreement) → the
     SaQE training signal + the "which signals predict Sanskrit errors?" answer.

PHASE 1 — BUILD THE INSTRUMENT
  4. Train SaQE (Sanskrit-specialized quality estimator + error-span detector) on the
     MQM-tagged gold (the Sanskrit error taxonomy from visionadvice.md).
  5. Build the calibrated confidence layer (isotonic/conformal) on held-out data.

PHASE 2 — IMPROVE THE TRANSLATOR (only after the instrument exists)
  6. Multi-candidate generation + MBR/QE reranking (the re-render engine scales to 8-32
     candidates, scored by the SaQE/xCOMET ensemble).
  7. LoRA register adapters (plain/precise/literal/natural) trained on the verified pairs.
  8. Preference tuning (CPO) + fine-grained error-span reward (only after SaQE is trustworthy).
  9. Multi-reference benchmark (PaliBench methodology) + the private blind test.

PHASE 3 — THE PROOF-CARRYING SYSTEM
 10. Every translation ships: source+hash · segmentation · morphology · alignment ·
     lexical/parallel/intertextual evidence · candidate distribution · evaluator error spans ·
     calibrated confidence + conformal interval · provenance · decision(accept/review/abstain).
```

---

## 4. THE MINIMUM VIABLE ASK (what I need RIGHT NOW to start)

| Item | Minimum | Ideal | Why |
|---|---|---|---|
| **GPU** | 1× 12GB (RTX 3060/4070) | 1× 24GB (4090/A5000) | COMET + QLoRA |
| **Disk** | 40GB free | 100GB | model weights |
| **torch/CUDA** | torch 2.x + CUDA 12 | same | the substrate |
| **Human gold** (later) | 500–1000 MQM-annotated passages | more | SaQE + calibration (the one thing I can't automate) |
| **Access** | ssh to the GPU box, or you install torch here | — | so I can run the pipeline |

**The honest dependency:** code is done; data is acquired; the gates exist. The two things I cannot
produce myself are (a) the **GPU/torch** to run COMET + training, and (b) the **human Sanskritist MQM
gold** for calibration. Everything else I run autonomously.

---

## 5. WHAT I CAN DO ON THIS BOX IN THE MEANTIME (no GPU needed)

- Import the frontier datasets (MITRA-parallel, Samasāmayik, SansTib) into the training pipeline.
- Build the **Sanskrit MQM error-taxonomy** schema + a challenge-set generator (controlled bad
  translations) — the SaQE training material.
- Wire the **multi-reference** structure into the benchmark registry (the PaliBench design).
- Extend the re-render engine to 8–32 candidates + candidate-disagreement signal.
- Set up the **annotation UI contract** for the human MQM gold (so when a Sanskritist is available, the
  data collection is ready).
- Keep the checkpoint DAG + verification gates green.

---

## 6. THE RULE

> **The blueprint is real and the code is built to it. The only thing between here and the final vision
> is (a) a GPU box with torch (to run COMET + training) and (b) human Sanskritist MQM gold (to calibrate
> the confidence). Give me those and I run the whole pipeline autonomously: reproduce baseline → build
> SaQE → calibrate → improve the translator → proof-carrying output.**
