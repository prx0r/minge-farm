# DEV-PLAN-NO-GPU-v2 — the current CPU box plan (2026-08-16)

*2026-08-16 · The executable CPU-runnable plan, rebuilt per `RETIRING-A-DEV-PLAN.md`. The previous
`DEV-PLAN-NO-GPU.md` was retired (kept as history). This plan carries forward the genuinely-incomplete
items (each linked to a real file + gate) and adds the openpatala school/period-integration work. The GPU
path is unchanged: `DEV-PLAN-WITH-GPU.md`. The checkpoint DAG (8/9 DONE, `lora-adapter` OPEN) is GPU-blocked;
this plan does NOT advance a checkpoint — it prepares the data/instruments so the GPU phase runs immediately.*

---

## 0. WHY THIS PLAN EXISTS (the honest state)

- **The checkpoint DAG cannot progress on this CPU box** — the only OPEN gate (`lora-adapter`) needs a GPU.
  Every CPU checkpoint (1-8) is DONE.
- So this plan's job is **data + instrument prep** for the GPU/human phase — nothing here claims to advance a
  checkpoint, and nothing here is "progress theater."
- **Retired by audit:** the previous `DEV-PLAN-NO-GPU.md` items were reconciled with `agent/plan_audit.py`;
  the incomplete ones are carried forward below with their gates intact.

## 1. THE VERIFIED DONE STATE (what exists now, all files confirmed + data gate clean)

| Capability | File (exists) | Status |
|---|---|---|
| Fixed gold (5,393, mostly Mitrasamgraha) | `pipeline/sanskrit_gold.py` | ✅ |
| Progressive-difficulty source (254 DCS/GRETIL) | `pipeline/sanskrit_texts.py` | ✅ |
| Re-render + disagreement signal | `pipeline/renderer.py` | ✅ |
| Fine-tune register-pair data | `pipeline/finetune_builder.py` | ✅ |
| Challenge sets (196 rows, 14 families) | `pipeline/sanskrit_mqm.py` | ✅ built; ⬜ gate pending |
| Cross-canon triangulation | `pipeline/triangulation.py` | ✅ |
| Multi-reference benchmark registry | `pipeline/benchmark_registry.py` | ✅ scaffold; ⬜ refs |
| Verification spine | `agent/{verify,audit,trace,validate_data}.py` + `run_recorder.py` | ✅ |
| Annotation contract | `agent/annotation.py` | ✅ scaffold; ⬜ at scale |
| Orchestration (checkpoint DAG, skill, memory) | `agent/run.py` + `pipeline/checkpoint.py` | ✅ |
| **New: retirement process + validator** | `RETIRING-A-DEV-PLAN.md` + `agent/plan_audit.py` | ✅ |

## 2. THE WORK ITEMS (priority order, each with a real file + a deterministic gate)

### N1 — Finish the challenge-set competence gate (SaQE data) ⬜ CARRIED FORWARD
**What:** complete the T-<T+ verification (`bad` < `good` on semantic fidelity) over all 196 rows. The
build is done; only the full run is missing (the earlier run died at 46/196 on a judge timeout — now fixed).
**Why:** this is the SaQE training material + evaluator-competence test; without it we can't trust a Sanskrit evaluator.
```
python3 agent/plan_audit.py --plan DEV-PLAN-NO-GPU-v2.md   # reconcile (part of the close-out)
python3 agent/ramwatch.py                                  # wait for SAFE
setsid nohup bash agent/challenge_verify_batch.sh > /tmp/sb-challenge-verify.log 2>&1 < /dev/null &
echo "PID $!" && tail -30 /tmp/sb-challenge-verify.log
```
**Gate:** a content-addressed `challenge_verify` run with `n >= 180` and `pass_rate >= 0.90` on the 13
factual-adequacy families (STYLE excluded — a register axis). Files: `agent/challenge_verify.py` ·
`agent/challenge_verify_batch.sh` · `data/challenge-sets/sanskrit-challenge-set.jsonl`.
**If the gate fails:** remove/improve the specific failing rows (the judge correctly says bad≈good) — don't
force a pass; those rows poison SaQE training.

### N2 — Collect the candidate-disagreement → review signal at scale ⬜ CARRIED FORWARD
**What:** run re-render on a sample of gold passages; record the disagreement verdict (convergent/mixed/
divergent-review) per passage.
**Why:** the blueprint §14 — divergent passages go to human review.
**Gate:** a logged distribution of disagreement across the sample. Files: `pipeline/renderer.py`.

### N3 — Complete the annotation contract at scale ⬜ CARRIED FORWARD (scaffold exists, 5 rows)
**What:** wire `agent/annotation.py` to fill `candidate_b` with a REAL re-rendered variant (currently
placeholder) and oversample divergent passages; export ~200 rows.
**Why:** the human MQM gold is the only non-automated input; the contract must be ready for the Sanskritist.
**Gate:** the exported file validates against the ANNOTATION_RECORD schema with real candidate pairs.
Files: `agent/annotation.py` · `data/annotation/mqm-gold-export-*.jsonl` (5 rows today).

### N4 — Polish the multi-reference benchmark (PaliBench) ⬜ CARRIED FORWARD (0 refs)
**What:** ensure ≥2 independent references where they exist (from re-renders + **published translations via
openpatala**) + alternative-senses representation.
**Why:** single-reference unfairly penalizes valid Sanskrit (blueprint §10).
**Gate:** registry validates against the multi-reference PASSAGE schema; ≥2 refs on matching passages.
Files: `pipeline/benchmark_registry.py` (+ `attach_references`), data from openpatala.

### N5 — Expand the cross-canon triangulation evidence channel ⬜ CARRIED FORWARD
**What:** grow the MITRA sample; confirm `triangulation.py` reports Tibetan/Chinese parallel agreement.
**Why:** the `C_crosslingual` confidence feature (blueprint §7).
**Gate:** a candidate with an agreeing parallel scores higher than one that disagrees.
Files: `pipeline/triangulation.py`.

### N7 — Import the openpatala school/period conditioning data (NEW — the G6 moat prep)
**What:** a small importer `pipeline/import_openpatala.py` that reads openpatala's `WORKS` metadata map
(author/period/school/genre) + its verse JSONL and emits benchmark PASSAGE rows with real `school` + `period`
+ source provenance. (Brainstorm: `research/PINCHING-OPENPATALA.md`.)
**Why:** this turns the `*vimarśa*` school/period moat (`DEV-PLAN-WITH-GPU` G6) from "spec'd" to "data-ready"
— the exact conditioning the benchmark needs. CPU-runnable now.
**Gate:** imported rows validate against the PASSAGE schema; school/period coverage reported (12 works →
Trika / Pratyabhijñā / Śaiva Siddhānta / Spanda / Bhairava / Kaula).
Files: `pipeline/import_openpatala.py` (to build) · source `openpatalaproject/pipeline/build_translation_availability.py`.

### N6 — Keep the gate + orchestration green (CONTINUING, always on)
**What:** every new module: register in MANIFEST + add a schema (if it writes data) + wire into `agent/run.py`
+ a skill line; run the retirement audit.
**Gate:** `check.py --status` + `agent/validate_data.py` PASS after every change; `agent/plan_audit.py --plan
DEV-PLAN-NO-GPU-v2.md` PASS at close-out.

---

## 3. THE RULES (unchanged)

- **Never claim a result without a logged number on fixed gold.** Use `agent/run.py` + `run_recorder`.
- **Every data file validates** against its canonical schema (`agent/validate_data.py`).
- **Box safety:** `agent/ramwatch.py` before + during heavy jobs; small samples; one job at a time; kill by PID.
- **Reuse, don't rebuild** (COMET/MTME/MQM/ByT5/Vidyut cloned; openpatala's WORKS map + verse JSONL).

## 4. WHEN TO STOP (this box's limit)

Stop CPU work when the only remaining items need torch/GPU (COMET scoring, SaQE training, LoRA, calibration/
conformal) or a human Sanskritist (the expert MQM gold). Those are `DEV-PLAN-WITH-GPU.md` + the
human-in-the-loop items. Everything CPU-doable is here; the retirement process (`RETIRING-A-DEV-PLAN.md`)
is how each item is verified done before it's ticked.
