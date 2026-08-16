# HANDSOVER-2026-08-16-CANONICAL — the complete current state for the next agent

*2026-08-16 · Complete orientation for the next agent working on sanskritbenchy. Read this top-to-bottom,
then the files it points to. Run the gates before building. This follows `HANDSOVER-TEMPLATE.md` (the
canonical handover spec).*

---

## 0. THE ONE-LINE STATE

> **A working, verified, agent-runnable Sanskrit-benchmark science lab: the gold, the verification spine
> (proof gate + eigenius kind + canonical schemas + strict data gate), the re-render + fine-tune product
> vision, the autonomous checkpoint DAG (8/9 gates DONE), and the legitimate ML path — all built on this
> CPU box and gate-green. The only blockers to the final vision are a GPU/torch box and a human Sanskritist
> for the MQM gold.**

---

## 1. THE PROJECT (what this is + why)

- **What:** sanskritbenchy — a Sanskrit translation benchmark + science lab that PROVES translation quality
  (learned metric + crypto commitment) and re-renders full texts into equally-valid registers, then builds
  fine-tuning data for LoRA adapters.
- **The vision:** a **calibrated, proof-carrying Sanskrit MT system** (the frontier blueprint in
  `research/visionadvice.md`): translate → verify → calibrate confidence + conformal interval → ship every
  translation as an auditable evidence artifact → license it.
- **The moat:** the verification/provenance spine (content-addressed, epistemically-labeled, gate-passed)
  + the school/period lemma-sense conditioning (*vimarśa*) — "proving when the machine should be trusted."

---

## 2. THE READ ORDER (60-second orientation)

| # | File | Why |
|---|---|---|
| 1 | `AGENTS.md` | the ONE RULE + the anti-mess standard |
| 2 | `CODING-AGENT.md` | the strict operational discipline (no-timeout, file lifecycle, review, test) |
| 3 | `VISION.md` | the goal + the checkpointed roadmap + §4.5 granular attainment path |
| 4 | **`HANDSOVER-2026-08-16-CANONICAL.md`** | **THIS file — the complete state** |
| 5 | `DEV-PLAN-NO-GPU.md` / `DEV-PLAN-WITH-GPU.md` | the current plans (CPU now / GPU later) |
| 6 | `HOW-IT-WORKS.md` / `INTEGRATION.md` | the mechanisms + the hermes-native vs our-additions integration |
| 7 | `RECIPES.md` | every command + how to expand |
| 8 | `CANONICAL-DATA-SPEC.md` | the schemas (every data contract) |
| 9 | `INFRA-REQUIREMENTS.md` | what's needed to complete the vision |
| 10 | `research/visionadvice.md` | the frontier blueprint (the north-star architecture) |

---

## 3. THE CURRENT STATE — WHAT'S DONE (verified, content-addressed)

| Capability | Status | Where |
|---|---|---|
| Fixed gold + clean_exemplars (junk dropped) | ✅ | `pipeline/sanskrit_gold.py` |
| Progressive-difficulty source (254 DCS/GRETIL, school/period) | ✅ | `pipeline/sanskrit_texts.py` |
| Deterministic proof gate (incl. CITATION_GROUNDING) | ✅ | `pipeline/translation_proof.py` |
| Experiment lab + registry | ✅ | `pipeline/experiment_lab.py` |
| Re-render into equally-valid translations + disagreement signal | ✅ | `pipeline/renderer.py` |
| Fine-tune register-pair data | ✅ | `pipeline/finetune_builder.py` |
| Challenge sets (controlled bad translations, SaQE data) | ✅ | `pipeline/sanskrit_mqm.py` |
| MITRA cross-canon triangulation | ✅ | `pipeline/data_import.py` + `triangulation.py` |
| Multi-reference benchmark registry (PaliBench) | ✅ | `pipeline/benchmark_registry.py` |
| AIDE metric-grounded tree search | ✅ | `pipeline/tree_search.py` |
| Content-addressed runs + nanopublication + eigenius kind | ✅ | `pipeline/run_recorder.py` |
| Canonical schemas + strict data gate | ✅ | `pipeline/schemas.py` + `agent/validate_data.py` |
| Verify / audit / trace / DML memory / ramwatch | ✅ | `agent/{verify,audit,trace,memory,ramwatch}.py` |
| Proof-carrying evidence object | ✅ | `pipeline/proof_carrying.py` |
| Confidence feature-vector + multidim proof score | ✅ | `pipeline/confidence.py` |
| Annotation contract (human MQM gold) | ✅ | `agent/annotation.py` |
| Checkpoint DAG (8/9 gates DONE) | ✅ | `pipeline/checkpoint.py` |
| Hermes skill v2 (registered + enabled) + Engram | ✅ | `skills/sanskrit-benchy/` + `~/engram` |
| Frontier blueprint + 13 research deep-dives | ✅ | `research/` |

---

## 4. THE LIVE CHECKPOINT DAG (the machine truth of what's done/next)

```
$ python3 agent/run.py --step checkpoints
[DONE] gold-ready · render-engine · finetune-data · full-text-render · fine-tune-verified
[DONE] triangulation · confidence-contract · proof-evidence
[OPEN] lora-adapter   ← the NEXT gate (per-register LoRA, needs GPU)
```
> **The next gate is `lora-adapter`** — it needs a GPU/torch box (QLoRA). On this CPU box, continue the
> `DEV-PLAN-NO-GPU.md` items (scale challenge sets, complete the annotation contract, expand triangulation).

---

## 5. THE DEV PLANS (which to follow, when)

- **CPU box (now):** `DEV-PLAN-NO-GPU-v2.md` (v1 retired) — N1 finish the challenge-set gate, N2 disagreement
  at scale, N3 complete the annotation contract, N4 polish multi-ref benchmark, N5 expand triangulation, N7
  import openpatala school/period data (the G6 moat prep). Followed by the retirement process
  (`RETIRING-A-DEV-PLAN.md` + `agent/plan_audit.py`).
- **GPU box (when available):** `DEV-PLAN-WITH-GPU.md` — G1 baseline reproduction → G2 COMET meta-validation
  → G3 SaQE → G4 calibration+conformal → G5 LoRA/translator → G6 school/period → G7 proof-carrying → G8
  benchmark+papers.
- **The immediate next action (CPU):** N1 — finish the challenge-set competence gate (complete the T-<T+
  run that died at 46/196; the verifier is now resilient).

---

## 6. THE VERIFIED RESULTS (real numbers, content-addressed)

| Result | Value | Evidence |
|---|---|---|
| Mitrasamgraha baseline | chrF 0.593 · bleu 0.352 · **semantic 0.76** · proof 10/10 | run `ef5b2fe0` |
| Re-render | 3/4 equally-valid (literal/plain/natural PASS+0.8; precise rejected) | run `7d1ced5d` (VERIFIED) |
| Candidate disagreement | convergent (agreement 0.71) | `renderer.candidate_disagreement` |
| AIDE tree search | baseline 0.700, honestly "no improvement" (no fabrication) | run `ddf8242e` |
| Proof gate | faithful→PASS, invented-term→BLOCKED (CITATION_GROUNDING) | `verify.py` |
| Cross-canon triangulation | finds Chinese + Tibetan parallels for a passage | `triangulation.py` |
| Content-addressed runs | 25 in the registry, eigenius-kind labeled | `agent/verify.py --registry` |

---

## 7. THE DATA (what exists, what's source-of-truth)

| Dataset | Size | Role |
|---|---|---|
| Mitrasamgraha test | 5,552 | primary gold + SFT corpus (source-of-truth) |
| Itihāsa / Sāmayik | 2,417 / 11,721 | external gold (source-of-truth) |
| DCS/GRETIL | 254 texts | progressive-difficulty source (source-of-truth) |
| MITRA cross-canon (imported) | 3,000 sampled | cross-canon triangulation (source-of-truth) |
| Challenge sets (generated) | 15 | SaQE training material (regenerable) |
| Fine-tune pairs (generated) | register-tagged | LoRA training data (regenerable) |
| Run records / registry / trace | ~25 runs | regenerable provenance |

**Regenerable (gitignored):** `data/runs/`, `data/checkpoints.json`, `data/benchmark-registry.json`,
`data/lab-memory.db`, the `.jsonl` logs. **Source-of-truth (committed):** the gold, challenge sets,
fine-tune pairs, MITRA samples.

---

## 8. THE GATES (must be green — run these)

```bash
python3 check.py --status                 # PASS = docs registered + data validates
PYTHONPATH=. python3 agent/validate_data.py   # the strict data gate
python3 agent/ramwatch.py                 # SAFE (box budget)
```

---

## 9. THE HONEST GAPS / BLOCKERS

| Gap | Blocked on | How to proceed |
|---|---|---|
| COMET scoring + meta-validation | torch/GPU | `DEV-PLAN-WITH-GPU.md` G1-G2 |
| SaQE evaluator training | the human MQM gold + GPU | annotation contract ready; G3 |
| LoRA register adapters | GPU (QLoRA) | G5 |
| Calibrated confidence + conformal | human gold + GPU | G4 |
| School/period conditioning | the lemma→sense map | build from darshana-graph + dcs↔sh |
| Human MQM gold | a Sanskritist annotator | the annotation contract is ready (`agent/annotation.py`) |

---

## 10. THE INFRA I NEED (if the vision is not yet complete)

From `INFRA-REQUIREMENTS.md`: **1× GPU (12-24GB) + torch/CUDA + ~40-100GB disk**, and **500-1000 human
MQM-annotated passages**. Everything else is built.

---

## 11. THE RECENT CHANGES (this handover's delta since the last handover)

- **New modules:** `pipeline/proof_carrying.py` (evidence artifact), `pipeline/confidence.py` (feature
  vector + proof score), `pipeline/triangulation.py` (cross-canon), `pipeline/data_import.py` (MITRA
  import), `pipeline/sanskrit_mqm.py` (challenge sets), `agent/annotation.py` (MQM contract),
  `DEV-PLAN-NO-GPU.md`, `DEV-PLAN-WITH-GPU.md`, `CODING-AGENT.md`, `HANDSOVER-TEMPLATE.md`.
- **Updated:** VISION (§4.5 granular attainment path), GOALS (dual dev plans), AGENTS.md (points to
  CODING-AGENT), pipeline/schemas.py (PROOF_EVIDENCE + more), MANIFEST.
- **The checkpoint DAG grew to 9 gates** (8 DONE); proof-evidence/triangulation/confidence-contract all
  built + verified.
- **N1 (2026-08-16):** `sanskrit_mqm.py` expanded to cover all 14 MQM error families (real deterministic
  perturbations, no placeholders); challenge set grown 15 → **196 rows (14/family)**, data-valid. New
  `agent/challenge_verify.py` + `agent/challenge_verify_batch.sh` (the T-<T+ competence gate, content-
  addressed). Wired `step_challenge` into `agent/run.py`, the skill, and MANIFEST.
- **Commits this session:** `037de6b` (the session's uncommitted modules + docs — Task 1), `dfdc523`
  (N1 challenge expansion + verifier + wiring).

---

## 12. THE GIT STATE

- Remote: `prx0r/minge-farm` · branch: `main` · HEAD: `b289c86` (the full build handover).
- **Dirty: ~13 uncommitted files** (this session's work): CODING-AGENT.md, both DEV-PLANs,
  HANDSOVER-TEMPLATE.md, proof_carrying.py, confidence.py, triangulation.py, + updates to AGENTS/GOALS/
  VISION/MANIFEST/schemas/docs-README/agent-runs.
- **Commit rule:** timestamped handover + dev plans + code together; run gates first.

---

## 13. HOW TO VERIFY THE PROJECT IS HEALTHY (the fresh-agent smoke test)

```bash
cd /root/sanskritbenchy
python3 agent/ramwatch.py                  # 1. box ok?
python3 check.py --status                  # 2. gate ok?
python3 agent/run.py --step checkpoints    # 3. what's next?
python3 agent/trace.py --recent            # 4. see the recent runs
python3 agent/verify.py --registry         # 5. every result content-addressed?
```
If all five pass, the project is healthy and you can start on the next gate.

---

## 14. THE SIGN-OFF (the last line)

> **The lab is real, verified, and agent-runnable on this CPU box — 8/9 vision gates done. The single
> most important next thing: commit this session's uncommitted work (see §12), then follow
> `DEV-PLAN-NO-GPU.md` on this box or `DEV-PLAN-WITH-GPU.md` once a GPU arrives. The code is built; the
> only real blockers are the GPU/torch box and the human MQM gold.**

---

## 15. THE GRANULAR NEXT TASKS (exact, in order — and WHY each)

*Read §15 with `DEV-PLAN-NO-GPU.md` (CPU) + `DEV-PLAN-WITH-GPU.md` (GPU). Each task says WHAT, the exact
command, and WHY it matters (which vision gate / research question it unlocks).*

### Task 1 — COMMIT the uncommitted work (do this FIRST, ~2 min)
**What:** commit the 16 uncommitted files (this session's modules + docs).
**Why:** the whole build is only in the working tree right now; if the box crashes or the other agent
rebases, this session's work is lost. Nothing survives until it's committed.
```
git add -A && git commit -m "add CODING-AGENT, DEV-PLANs, HANDSOVER-TEMPLATE, proof_carrying, confidence, triangulation, METASTRUCTURE"
```

### Task 2 — Verify the box + the gates are green (every session start, ~30s)
**What:** run the smoke test (§13).
**Why:** confirms the project is healthy before you build; a stale gate means a stale claim.
```
python3 agent/ramwatch.py && python3 check.py --status && python3 agent/run.py --step checkpoints
```

### Task 3 (CPU) — Scale the challenge set + verify T- < T+ (the SaQE data)
**What:** expand `sanskrit_mqm.py` from 15 to ~200 controlled bad translations across all 14 error
families, and verify each `bad` scores LOWER than its `good`.
**Why:** this is the SaQE training material + the evaluator-competence test (visionadvice §11). Without
verifiable T-/T+ pairs, we can't train or validate a Sanskrit evaluator. It's the prerequisite for the
whole calibration layer.
```
# extend the PERTURBATIONS in pipeline/sanskrit_mqm.py, then:
PYTHONPATH=. python3 pipeline/sanskrit_mqm.py --challenge 200
PYTHONPATH=. python3 agent/validate_data.py    # the new rows must validate
```

> **STATUS (2026-08-16):** ✅ generation DONE — `sanskrit_mqm.py` now covers ALL 14 error families
> (real deterministic perturbations, no placeholders); the challenge set is expanded to **196 rows,
> 14 each across all families**, data-valid (0 violations). A verifier was built:
> `agent/challenge_verify.py` (scores each bad vs good on semantic fidelity, logs a content-addressed run
> record, reports per-family pass rate; gate threshold ≥90% bad<good) + a box-safe batch runner
> `agent/challenge_verify_batch.sh`. ⏳ **The T-<T+ verification is NOT YET RUN** — it needs ~1 judge
> call per pair and the box was CRITICAL (other agent's OCR) during this session. To finish N1:
> ```
> python3 agent/ramwatch.py                      # wait for SAFE
> setsid nohup bash agent/challenge_verify_batch.sh --n 196 > /tmp/sb-challenge-verify.log 2>&1 &
> echo "PID $!" && tail -30 /tmp/sb-challenge-verify.log   # check later
> ```

### Task 4 (CPU) — Complete the annotation contract (fill candidate_b with a real re-render)
**What:** wire `agent/annotation.py` to fill `candidate_b` with a REAL re-rendered variant (not a
placeholder), and oversample the divergent/disagreement passages.
**Why:** the human MQM gold is the ONLY input I can't automate. The moment a Sanskritist is available,
this contract must be ready so they can annotate immediately (visionadvice §6/§17 — the SaReward + SaError
data). The faster it's ready, the faster we can train SaQE.
```
PYTHONPATH=. python3 agent/annotation.py --export 200    # real pairs, disagreement-oversampled
```

### Task 5 (CPU) — Expand the cross-canon triangulation
**What:** grow the MITRA sample + build the evidence channel so a candidate's Tibetan/Chinese parallel
agreement is a real signal.
**Why:** cross-canon triangulation is the blueprint's §3 evidence + the `C_crosslingual` confidence feature
(§7). It's a CPU-doable evidence channel that strengthens every translation's proof artifact.
```
PYTHONPATH=. python3 pipeline/triangulation.py    # confirm parallels resolve
```

### Task 6 (CPU) — Wire the new kernels into the orchestrator + skill
**What:** add `step_proof_evidence`, `step_triangulation`, `step_confidence` to `agent/run.py` + lines in
`skills/sanskrit-benchy/SKILL.md`, register in MANIFEST.
**Why:** an agent (or cron) must be able to run every capability; anything not agent-callable is
effectively dead. This keeps the lab fully autonomous.

### Task 7 (CPU, ongoing) — Polish the multi-reference benchmark (PaliBench)
**What:** ensure the benchmark registry holds ≥2 independent references where they exist + the
alternative-senses representation.
**Why:** single-reference evaluation unfairly penalizes valid Sanskrit translations (the §10 finding —
legit translations score BLEU 25.2 vs each other). Multi-reference is what makes the benchmark legitimate
and publishable.

### Task 8 (CPU) — Run the meta-eval baseline (the first real tau)
**What:** `validate_benchmark.py` on mitrasamgraha + frontier gold → a logged Kendall's-tau (chrF vs bleu
vs semantic-judge).
**Why:** this is the falsifiable "our metric beats chrF" number the whole benchmark claims. Without it,
the benchmark has no proven value.

### Task 9 (GPU, when available) — Follow DEV-PLAN-WITH-GPU.md
**What:** G1 baseline reproduction → G2 COMET meta-validation → G3 SaQE → G4 calibration+conformal → G5
LoRA → G6 school/period → G7 proof-carrying → G8 benchmark+papers.
**Why:** this completes the vision (a calibrated, proof-carrying Sanskrit MT system). The CPU tasks
(3-8) prepare the data + instruments so the GPU phase runs immediately with no rework.

### The dependency logic (why this order)
- **3-5 first** (data/instruments) → they need no GPU and produce the SaQE training material + evidence.
- **6** (wiring) → so everything above is agent-callable.
- **7-8** (benchmark rigor) → the legitimate number + multi-ref design.
- **9** (GPU) → consumes all of the above; the GPU phase has zero CPU-rework because the data +
  instruments are ready.

**The ONE next action:** Task 1 (commit). After that, Task 3 (scale the challenge set).
