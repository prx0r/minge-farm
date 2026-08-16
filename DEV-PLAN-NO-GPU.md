> **RETIRED** — superseded by `DEV-PLAN-NO-GPU-v2.md` · 2026-08-16. The incomplete items (N1 gate, N2, N3,
> N4, N5) carried forward; N7 (openpatala integration) added. Retired via `RETIRING-A-DEV-PLAN.md` +
> `agent/plan_audit.py` — kept as timestamped history. The GPU path is unchanged (`DEV-PLAN-WITH-GPU.md`).

# DEV PLAN — NO-GPU (the current CPU box, 2026-08-16)

*2026-08-16 · The executable plan for what to keep building on THIS 8GB CPU box (no torch, no GPU). The
GPU-gated work is `DEV-PLAN-WITH-GPU.md`. Everything here is CPU-runnable, deterministic, and gated. The
goal on this box: **prepare the data + instruments + annotation so the moment a GPU arrives, the full ML
path runs immediately.***

---

## 0. THE ONE-LINE GOAL (CPU box)

> **Build every instrument that needs NO GPU: the SaQE training data (challenge sets + MQM annotations), the
> multi-reference benchmark, the cross-canon triangulation evidence, the candidate-disagreement signal, and
> the COMET scaffolding — so the GPU phase is pure "load weights + train + calibrate."**

---

## 1. THE DONE STATE (verified, not aspirational)

| Capability | Status |
|---|---|
| Gold + clean_exemplars (junk dropped) | ✅ |
| Progressive-difficulty source (254 DCS/GRETIL, school/period-tagged) | ✅ |
| Re-render into equally-valid translations + disagreement signal | ✅ |
| Fine-tune register-pair data | ✅ |
| Challenge sets (controlled bad translations) | ✅ |
| MITRA cross-canon triangulation imported | ✅ |
| Multi-reference benchmark registry (PaliBench) | ✅ |
| Verification spine (proof gate + eigenius kind + CITATION_GROUNDING + schemas + data gate) | ✅ |
| Autonomous orchestration (checkpoint DAG, AIDE tree search, DML memory, hermes skill v2, Engram) | ✅ |
| Annotation contract (human MQM gold exporter + validator) | ✅ |

## 2. THE NO-GPU WORK ITEMS (in priority order)

### N1 — Scale the challenge set + make it a real evaluator test (SaQE data)
- [x] Expand the challenge set to ~200 controlled bad translations across ALL 14 error families (not just
      the 5 heuristic perturbations). → **196 rows, 14/family** (2026-08-16).
- [x] Verify each T- is genuinely worse than T+ (the gold) using the semantic-judge. → built
      `agent/challenge_verify.py` (resilient: SB_JUDGE_TIMEOUT + per-row retry) + box-safe batch runner.
- [ ] **Gate:** every challenge row's `bad` scores LOWER than its `good` on semantic-fidelity (a
      deterministically-checkable property). → **run in progress** (`bash agent/challenge_verify_batch.sh`,
      needs the box SAFE; ~400 judge calls ≈ 15-20 min).
- [ ] **Design note (2026-08-16):** the T-<T+ semantic gate applies to the FACTUAL-ADEQUACY families.
      **STYLE is excluded** — per the MQM taxonomy it is a register/readability error "kept separate from
      factual adequacy," so it is not supposed to lower semantic fidelity (it remains valid SaQE span
      data). The gate's pass-rate denominator = the 13 semantic families.

### N2 — Collect the candidate-disagreement → review signal at scale
- [ ] Run re-render on a sample of gold passages; record the disagreement verdict (convergent/mixed/
      divergent-review) per passage.
- [ ] **Gate:** a logged distribution of disagreement across the sample; divergent passages are flagged
      for human review (the blueprint §14).

### N3 — Complete the annotation data contract (human-ready)
- [ ] Wire the annotation exporter to fill `candidate_b` with a REAL re-rendered variant (not a
      placeholder).
- [ ] Oversample the divergent/disagreement passages so the human annotates the hard cases (the blueprint's
      strategic sampling).
- [ ] **Gate:** the exported annotation file validates against the ANNOTATION_RECORD schema, with real
      candidate pairs.

### N4 — Polish the multi-reference benchmark (PaliBench)
- [ ] Ensure the benchmark registry holds ≥2 independent references where they exist (from re-renders +
      published translations).
- [ ] Add the alternative-senses representation (sense(x) ∈ {A,B}) for polysemous terms.
- [ ] **Gate:** the registry validates against the multi-reference PASSAGE schema.

### N5 — Prepare the cross-canon triangulation evidence channel
- [ ] Expand the MITRA cross-canon sample; build a `triangulation.py` that, given a Sanskrit passage +
      candidate, reports Tibetan/Chinese parallel agreement (when parallels exist).
- [ ] **Gate:** a candidate with a parallel agreeing scores higher than one that disagrees (the blueprint §3).

### N6 — Keep the gate + orchestration green
- [ ] Every new module: register in MANIFEST + add a schema (if it writes data) + wire into `agent/run.py`
      + a skill line.
- [ ] **Gate:** `check.py --status` + `agent/validate_data.py` PASS after every change.

---

## 3. THE RULES (unchanged)

- **Never claim a result without a logged number on fixed gold.** Use `agent/run.py` + `run_recorder`.
- **Every data file validates against its canonical schema** (`agent/validate_data.py`).
- **Box safety:** `agent/ramwatch.py` before + during heavy jobs; small samples; one job at a time.
- **Reuse, don't rebuild** (COMET/MTME/MQM/ByT5/Vidyut cloned).

---

## 4. WHEN TO STOP (this box's limit)

Stop CPU work when the only remaining items need torch/GPU (COMET scoring, SaQE training, LoRA, MITRA-E,
calibration/conformal) or a human Sanskritist (the expert MQM gold). Those are `DEV-PLAN-WITH-GPU.md` +
the human-in-the-loop items. Everything CPU-doable is done or specced here.
