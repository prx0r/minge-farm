# DEV PLAN — WITH-GPU (the full ML path once a torch/GPU box arrives)

*2026-08-16 · The executable plan for the moment a GPU/torch box is available. This runs the full
frontier-blueprint ML path (`research/visionadvice.md`): COMET evaluation, SaQE training, LoRA register
adapters, calibration + conformal prediction, and the proof-carrying output. Everything here needs torch
+ a GPU (the CPU-only work is `DEV-PLAN-NO-GPU.md`).*

---

## 0. THE ONE-LINE GOAL (GPU box)

> **Run the blueprint's full pipeline autonomously: reproduce the baseline → build + validate the SaQE
> evaluator → calibrate confidence (isotonic + conformal) → improve the translator (LoRA, preference tuning)
> → ship every translation as a calibrated, proof-carrying, evidence-backed artifact.**

---

## 1. THE DONE STATE (CPU box — what the GPU phase builds on)

Everything CPU-doable is DONE + verified: the gold, schemas, verification gates, re-render + fine-tune
data, challenge sets, cross-canon triangulation, proof-carrying evidence object, confidence contract, the
checkpoint DAG (8/9 gates done), the annotation contract. The GPU phase consumes these.

## 2. THE WITH-GPU WORK ITEMS (in dependency order)

### G1 — Baseline reproduction (the blueprint's very first step)
- [ ] Install torch + `unbabel-comet` on the GPU box.
- [ ] Run **MITRA-MT, MITRA-Qwen3.5, a generic current model, mimo-v2.5** over the SAME
      Mitrasamgraha test passages. Store every candidate (content-addressed).
- [ ] Run **xCOMET, MetricX-25, GEMBA-MQM** over those outputs.
- [ ] **Gate:** a content-addressed candidate + evaluator matrix across models.

### G2 — COMET meta-validation on Sanskrit (the honest metric gate)
- [ ] Score COMET (`wmt22-comet-da`, `cometkiwi-da` ref-free) on our gold + frontier gold.
- [ ] Compute COMET's Kendall-tau vs the judge (and vs our semantic-judge) — does COMET beat chrF on
      Sanskrit? **This decides whether we trust COMET or fine-tune a Sanskrit-aware head.**
- [ ] **Gate:** a logged tau table (COMET vs chrF vs ours) on the same fixed gold.

### G3 — SaQE: the Sanskrit-specialized evaluator (§6)
- [ ] Collect the **human MQM gold** (500-1000 passages, oversampling disagreement) via the annotation
      contract.
- [ ] Train **SaQE** on the MQM-tagged gold: predict Q_segment + per-span (e_i, category_i, severity_i)
      using the Sanskrit MQM taxonomy + challenge sets.
- [ ] **Gate:** SaQE's error-span F1/AUROC on held-out gold; its correlation beats chrF.

### G4 — The calibrated confidence + conformal layer (§7, §8)
- [ ] Build the feature vector z (the CPU scaffold) with the neural features now available (q_xCOMET,
      q_SaQE, A_alignment, M_morph, R_retrieval).
- [ ] Train a calibrated P(Y=1 | z) (isotonic/logistic) on held-out human data.
- [ ] Add **split conformal prediction** → a coverage-guaranteed interval per translation.
- [ ] **Gate:** on a calibration set, the conformal interval achieves ~90% coverage; risk-vs-coverage is
      measured (e.g. "at 60% coverage, only 1.2% of accepted translations have a major error").

### G5 — The improved translator (only after the instrument exists)
- [ ] **LoRA register adapters** (plain/precise/literal/natural) trained on the verified fine-tune pairs
      (QLoRA, 4-bit). Each adapter's outputs re-verified by the gate.
- [ ] **Multi-candidate generation + MBR/QE reranking** — scale the re-render engine to 8-32 candidates,
      pick by the SaQE/xCOMET ensemble (not one decode).
- [ ] **Preference tuning (CPO)** + fine-grained error-span reward — only after SaQE is trustworthy
      (avoid the reward-hacking warning §16).
- [ ] **Gate:** the improved model's MQM/preference score beats the baseline on the blind test.

### G6 — The school/period conditioning (the moat, §3)
- [ ] Build the lemma→sense→(school,period) map (darshana-graph + dcs↔sh + CDSL/DCS).
- [ ] Add the school/period condition token (or conditioning LoRA).
- [ ] **The *vimarśa* test:** the conditioned metric ranks the school-correct sense higher.
- [ ] **Gate:** tau(school-conditioned) > tau(not), on the same gold.

### G7 — The proof-carrying, calibrated system (§12, §20, §21)
- [ ] Every translation ships the full evidence artifact: source+hash · segmentation · morphology ·
      alignment · lexical/parallel/intertextual evidence · candidate distribution · evaluator error spans ·
      calibrated confidence + conformal interval · provenance · decision(accept/review/abstain).
- [ ] Per-span confidence (§21) for compounds/ambiguous terms.
- [ ] **Gate:** the proof-carrying artifact validates against the PROOF_EVIDENCE schema and every
      uncertainty field is a calibrated number, not a vague "confidence."

### G8 — The legitimate benchmark + paper (§9, §19, §23)
- [ ] Build **SanskritMT-MQM**: gold/silver/challenge levels + the 4 leaderboards (translation,
      critical-error detection, QE correlation, calibration).
- [ ] Multi-reference + PaliBench methodology + a private blind test (decontamination-audited).
- [ ] Write the papers (Paper A benchmark, Paper B SaQE, Paper C calibration, Paper D proof-carrying) via
      `agent/paper_build.py` (number-inject from logs).
- [ ] **Gate:** a logged, content-addressed, publishable result per paper.

---

## 3. THE RULES (unchanged)

- **Never train against COMET indefinitely** — use a reward mixture + a private human-evaluated benchmark
  the reward models can't see (§16).
- **The scorer ≠ the generator** — SaQE/xCOMET verify; the translator doesn't grade itself.
- **Every number is content-addressed + epistemically-labeled** (`run_recorder.py`).
- **Every data file validates** (`agent/validate_data.py`).
- **The human MQM gold is the one non-automated input** — the annotation contract is ready.

---

## 4. WHEN THIS COMPLETES THE VISION

When G1–G8 pass, the system is: a **calibrated, proof-carrying Sanskrit MT system** that (a) knows when it
should be trusted (conformal interval + abstention), (b) ships auditable evidence per translation, (c)
ranks better than chrF on a legitimate multi-reference benchmark, and (d) is licenseable. That is the
`visionadvice.md` moat. The CPU work (G0/data/instruments) is done; the GPU work (G1–G8) runs once a GPU
box is available.
