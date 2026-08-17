# THE LEGITIMATE ML STACK — spec for a proper COMET + frontier Sanskrit-translation environment

*2026-08-16 · The full spec for making sanskritbenchy legitimate with a proper ML stack: the evaluation
metric (COMET/learned), the training environment (frontier methods), the datasets (what we need + what we
have), and the training methods (LoRA/register adapters, school/period conditioning). This is the
engineering path from "hermes-translated + heuristic-verified" to "a proper, trainable, publishable MT
system."*

---

## 1. THE GOAL (what "legitimate ML" means here)

> **Replace the hermes-only translation + heuristic verification with a proper MT stack: (1) a learned
> quality metric (COMET) that provably beats BLEU/chrF on Sanskrit (meta-eval vs human gold), (2) a
> trainable translation model with per-register adapters (LoRA) conditioned on school/period, and (3) a
> legitimate benchmark + eval harness that produces publishable numbers.**

The pipeline has three ML surfaces: **EVALUATE** (COMET), **TRAIN** (LoRA/register adapters), **BENCHMARK**
(the legitimate progressive-difficulty test set + meta-eval).

---

## 2. THE EVALUATION LAYER — COMET + learned metrics (the "verify" upgrade)

### 2.1 Why COMET (the frontier standard)
COMET is the learned MT metric that **provably beats BLEU/chrF** at ranking translations like a human. It's
a neural regressor `[src, hyp, ref] → 0..1` trained on human DA/MQM labels. For us: our current semantic-
judge is a good proxy, but COMET is the **reproducible, established** metric — and the field standard for
"is this translation good."

### 2.2 The COMET models (verified, from `research/DEEP-DIVE-COMET-CRYPTO-VERIFICATION.md`)
| Model | What | Use |
|---|---|---|
| `Unbabel/wmt22-comet-da` | reference-based learned metric, XLM-R | the primary eval metric |
| `Unbabel/wmt22-cometkiwi-da` | **reference-free QE** `(src, hyp)` | when no gold reference (re-render validation) |
| `xCOMET` | score + error spans | diagnostic (which span is wrong) |

**The honest caveat:** XLM-R covers Sanskrit only weakly. **Before trusting COMET on Sanskrit, we must
meta-evaluate it** (correlate with human gold) — that's the legitimate gate. If it underperforms, we
fine-tune a Sanskrit-aware COMET head (on ByT5-Sanskrit or Gemma2-MITRA).

### 2.3 The COMET eval spec
```
INPUT:  a (src, hyp, ref) triple (or (src, hyp) for ref-free)
OUTPUT: comet ∈ [0,1]  (the learned quality estimate)
GATE:   COMET must be meta-validated on Sanskrit human gold (tau vs experts) before we trust it
HARDWARE: torch + the model weights — needs a GPU/torch box (NOT this 8GB CPU box)
```
**Integration:** `pipeline/comet_scorer.py` already wraps it (fails cleanly without torch). When run on a
torch box, it scores our gold + re-renders, and we compare its tau vs chrF vs our semantic-judge.

---

## 3. THE TRAINING ENVIRONMENT — frontier translation methods

### 3.1 The base model + why
We translate with a **strong multilingual LLM** (mimo-v2.5 via hermes now; the frontier uses
NLLB-200 / IndicTrans / Gemma). For a *proper* trainable system, the base is one of:
- **IndicTrans2/3** (AI4Bharat) — SOTA Indic MT incl. Sanskrit `san_Deva`; ships COMET eval scripts.
- **NLLB-200** (Meta) — 200-language MT; the Sāmayik baseline.
- **Gemma-2-MITRA** — Sanskrit/Pāli/Buddhist specialized; a semantic-embedding model for retrieval.

### 3.2 The training method: LoRA register adapters (the product vision)
We don't retrain the base — we train **per-register LoRA adapters** (QLoRA, 4-bit) so a single base
produces plain/precise/literal/natural registers by adapter-swap. The training data is the **verified
fine-tune pairs** (`data/finetune/` — instruction/input/output/register), each output already validated by
the proof gate + gold.

```
BASE (IndicTrans/NLLB/Gemma) + LoRA-register-adapters
   ├─ adapter: plain    (trained on "translate into plain English" pairs)
   ├─ adapter: precise  (trained on "translate precisely, terms exact")
   ├─ adapter: literal  (trained on "translate literally, preserve word order")
   └─ adapter: natural  (trained on "translate idiomatically")
→ per-register output verified by the same gate (proof + COMET) → equally-valid set
```

### 3.3 The training spec
```
FRAMEWORK: QLoRA (4-bit NF4) — train per-register adapters on a GPU box (8-12GB VRAM)
DATA:      data/finetune/sanskrit-translation-pairs.jsonl (register-tagged, verified)
METHOD:    LoRA rank 8-16, alpha 16-32, on the decoder layers
EVAL:      each adapter's outputs must PASS the proof gate + semantic/COMET ≥ threshold
GATE:      a per-register adapter whose outputs are VERIFIED (not just fluent)
HARDWARE:  needs a GPU box (NOT this 8GB CPU box)
```

### 3.4 School/period conditioning (the moat)
The lemma→sense→(school,period) map (built from darshana-graph + dcs↔sh alignment) conditions WHICH sense
a term takes. For training, add a **school/period condition token** to the prompt (or a conditioning LoRA),
so the adapter knows "this is Pratyabhijñā, translate vimarśa as X." This is the *vimarśa* test.

---

## 4. THE DATASETS (what we need + what we have)

### 4.1 What we HAVE (verified, in `data/`)
| Dataset | Size | Use |
|---|---|---|
| Mitrasamgraha test | 5,552 pairs | the primary translation gold |
| Mitrasamgraha val | 5,587 | held-out validation |
| IPVV published | 49 passages | scholarly gold (Pratyabhijñā) |
| Sāmayik | 2,417 (En→Sa) | external modern-prose gold |
| Itihāsa | 11,721 (En→Sa) | external epic gold |
| DCS/GRETIL | 254 texts | the progressive-difficulty source (school/period-tagged) |
| dcs↔sh alignment | full | the lemma/morphology spine |

### 4.2 What we NEED (the gaps for a proper ML stack)
| Dataset | Why | Source |
|---|---|---|
| **Sanskrit human MQM/DA gold** (Phase 4) | the expert labels to train + meta-validate COMET, and to prove tiers are "harder" | build it (expert annotators) — the long-term asset |
| **More parallel data** | to fine-tune a Sanskrit-aware COMET head + train adapters | **MITRA** (1.74M sa-pairs, cloned at `dharmamitra__mitra-parallel`), **SAHAAYAK** (1.5M), **Samasāmayik** (92k) |
| **A Sanskrit-specific eval set** | COMET is unvalidated on Sanskrit; need our own to trust it | from the progressive-difficulty registry |
| **The lemma→sense map** | the school/period conditioning | build from darshana-graph + dcs↔sh + CDSL/DCS |

### 4.3 The data licensing honesty
- **Open/usable:** Itihāsa (Apache), Sāmayik, DCS/GRETIL (CC-BY), csl/Monier-Williams (CC-BY-SA), Manoj vocab (MIT), MITRA-parallel, IndicTrans2 (CC-BY-NC — non-commercial).
- **Unlicensed (internal-only):** Mitrasamgraha, skt-en-itihasa-tagged, vedic-sanskrit.
- **For a PUBLISHED benchmark, prefer the Apache/CC-BY sources; keep unlicensed as offline scaffolding.**

---

## 5. THE FULL ML-STACK ARCHITECTURE

```
DATA (gold + frontier + lemma map)
   │
   ▼  TRAIN (GPU box, QLoRA)
BASE + LoRA-register-adapters (plain/precise/literal/natural)
   + school/period condition token
   │
   ▼  TRANSLATE (the runner, hermes OR the trained model)
   │
   ▼  VERIFY (the gate)
proof gate + CITATION_GROUNDING + gold
   + COMET (meta-validated) + semantic-fidelity
   │
   ▼  EVALUATE (the benchmark)
MTME: Kendall's-tau of each metric vs human gold, per school × period
   │
   ▼  THE PROOF
our metric's tau > chrF/bleu's tau, logged, content-addressed, epistemically-labeled
```

---

## 6. THE HONEST GAPS (what's code vs what needs hardware/humans)

| Gap | Blocked on | Status |
|---|---|---|
| **COMET scoring** | torch + model weights | scaffolded (`comet_scorer.py`), needs a torch box |
| **LoRA adapters** | GPU (QLoRA) | data + method specced, needs GPU |
| **Sanskrit human MQM gold** | expert annotators | the long-term asset (Phase 4) |
| **More parallel data** | just needs importing (MITRA/SAHAAYAK) | importable now |
| **COMET meta-validation on Sanskrit** | the MQM gold + torch | the honest gate before trusting COMET |
| **School/period conditioning** | the lemma→sense map | buildable from darshana-graph + dcs↔sh |

---

## 7. THE RULE

> **A metric is legitimate only after it is meta-validated on Sanskrit human gold (COMET's tau vs experts
> beats chrF). A trained adapter is legitimate only when its outputs pass the proof gate + COMET +
> semantic. A benchmark is legitimate only when it is content-addressed, decontamination-audited, and its
> "harder" tiers are proven by human gold. We have the data + the method + the spec; the missing pieces are
> a GPU/torch box and the expert MQM gold.** The spec is real; the execution needs the hardware.
