# CLONED-REPO ADOPTION — the MT-metrics/Sanskrit-benchmark reference (reuse, don't rebuild)

*2026-08-16 · The repos relevant to the sanskritbenchy vision: the MT-metrics toolkits we adopt (reuse,
don't rebuild) + the verified GitHub landscape from the deep-dive
(`research/DEEP-DIVE-COMET-CRYPTO-VERIFICATION.md`). Every repo below is **live-verified**. It says what it
is, how it fits, and the honest limitation.*

---

## The 5 directly-relevant clones (already in `patalacheckpoints/source-evidence/repos/`)

### 1. `Unbabel__COMET` — the learned MT metric framework ⭐ CORE
- **What:** neural learned metric (encoder `[src, hyp, ref]` → 0..1), trained on human DA/MQM. CLI:
  `comet-score`, `comet-compare`, `comet-mbr`, **`comet-train`** (train your own). v2.2.7.
- **Verified:** `comet-score -s src -t hyp -r ref --gpus 0` runs on **CPU**; `wmt22-comet-da` covers
  Sanskrit (XLM-R) — nominally, poorly trained. Ref-free `cometkiwi` needs no reference.
- **Fit:** Phase B baseline + the training scaffold for our Sanskrit-aware COMET head (AfriCOMET recipe).
- **Adopt:** our `pipeline/comet_scorer.py` wraps it; train via `comet-train` after the Phase A gold.

### 2. `google-research__mt-metrics-eval` (MTME) — the meta-evaluation toolkit ⭐ CORE
- **What:** the **WMT-standard** meta-eval: Kendall/Spearman/Pearson of a metric vs human gold, significance,
  matrix comparisons. `mtme --download` then `mtme -t wmt22 -l en-de < scores.seg.score`.
- **Verified:** runs on **CPU**; bundles WMT19+ human gold (incl. MQM).
- **Fit:** **replaces our hand-rolled `kendall_tau`** — the honest way to prove "our metric beats BLEU".
- **Adopt:** wire its `Correlation`/`AverageCorrelation` into `validate_benchmark.py`; feed our Sanskrit
  metric scores + our human DA/MQM gold.

### 3. `google__wmt-mqm-human-evaluation` — the human MQM gold FORMAT ⭐ TEMPLATE
- **What:** expert (professional-translator) MQM annotations for WMT, newstest2020-2024.
- **Fit:** the **format + methodology template for our Phase A Sanskrit DA/MQM gold** (Sanskrit has none).
- **Adopt:** copy the MQM schema/severity (minor/major/critical) + DA scoring into `data/da-mqm/`.

### 4. `amazon-science__span-mt-metaeval` — LLM-as-judge + meta-eval harness
- **What:** evaluates LLM-based MT metrics (bedrock GPT/LLama/Qwen judges) vs human MQM — span-level.
- **Fit:** the blueprint for our **school-instructed, reference-grounded LLM judge** (fixes naive-LLM-judge
  bias on creative/śāstric text).
- **Adopt:** its judge-config pattern (model_aliases.yaml, metrics.yaml).

### 5. `langtech-bsc__mt-evaluation` (MT-Lens) — the evaluation platform
- **What:** an MT-evaluation web app (comet/other metrics, per-system dashboards).
- **Fit:** optional serving/visualization of the per-school × per-period leaderboard later.

---

## Additional verified GitHub (from the deep-dive) — the crypto/proof + Sanskrit tooling

| Repo | What it actually does | Our use | Honest limitation |
|---|---|---|---|
| **`zkonduit/ezkl`** | ONNX model → ZK-SNARK proving "this public network ran on inputs → output"; audited (Trail of Bits) | ⭐ prove the COMET metric scored these inputs (compute integrity) | proves integrity, **not** quality |
| **`risc0/risc0`** | general zkVM; produces a **receipt** (journal+seal), tamper-evident, cheap to verify | ⭐ most general "proof of execution" receipt | GPU-heavy to prove |
| **`AI4Bharat/IndicTrans2`** | SOTA NMT for 22 Indic langs **incl. Sanskrit `san_Deva`**; ships COMET eval scripts | generate/validate Sanskrit + scaffolding | IN22 is a ref benchmark, no human QE ratings |
| **`jwkirchenbauer/lm-watermarking`** | "A Watermark for LLMs" official impl (provenance) | only if we control the generator | provenance, not quality; GPU-bound |
| **`masakhane-io/africomet`** | COMET fine-tuned for 13 African low-resource pairs + human-scored challenge set | **the exact recipe** for a Sanskrit COMET | code thin; models are the deliverable |
| **`google-research/metricx`** | Google's learned metric (hybrid ref+QE) | strong metric option | needs GPU for XL/XXL |
| **`google-research/bleurt`** | BERT regression metric | aging | English-centric |

**⚠️ Not usable / not real (verified 404 or research-only):** zkLLM (folded into =nil; zkLLVM), TensorCommitments / zkComposer (not open), Modulus Labs (defunct), AEX signed-attestation (no mature repo), proof-of-learning (forgeable). **Do not build on these.**

---

## The adoption map → the vision

```
OUR GOLD (sanskrit_gold.py + Phase A DA/MQM in the wmt-mqm format)
        │
        ▼
OUR METRICS:  chrF/bleu (have) · semantic-judge (have) · COMET (adopt Unbabel__COMET) ·
              school/period-conditioned COMET (novel, Phase C) · school-instructed LLM judge (span-mt-metaeval pattern)
        │
        ▼
META-EVAL:   MTME (adopt google-research__mt-metrics-eval) → Kendall/Spearman vs human gold
        │
        ▼
THE PROOF:   our metric's tau > chrF/bleu's tau, per school × per period, on the same fixed gold
             → "our benchmark is scientifically better" (logged, not asserted)
```

## The VERIFY + PROVE layer (the novel crypto addition)

```
1. SEMANTIC VERIFY   — COMET/ML (quality)              → "is it a faithful translation?"
2. DIAGNOSE          — xCOMET/GemSpanEval error spans  → "where does it diverge?"
3. META-EVALUATE     — MTME tau vs human gold          → "is our metric better?"
4. CRYPTO COMMIT     — hash/Merkle (src,hyp,ref,score) + signed timestamp + model-ID
                       (optionally wrapped in an EZKL/RISC-Zero proof) → "did this run → this output, unaltered?"
```

**The honest rule:** step 4 proves **integrity** (this run produced this output), never **quality**. Only
steps 1–3 prove quality. Keep the two domains distinct in every claim — **never call a zkML proof "proof
of a good translation."**

---

## What to adopt NOW (no torch needed) vs LATER (needs torch/GPU/Phase A)

| Repo | Now | Later (torch/GPU/Phase A) |
|---|---|---|
| mt-metrics-eval | ✅ adopt `stats.py` for the real tau/spearman meta-eval | — |
| wmt-mqm-human-evaluation | ✅ copy the MQM format into our gold spec | build our Sanskrit MQM gold (Phase A) |
| span-mt-metaeval | ✅ borrow the judge-config pattern | school-instructed judge (Phase C) |
| COMET | ⚠️ needs torch — scaffold ready (`comet_scorer.py`) | Phase B baseline + Phase C training |
| ezkl / risc0 | — | ⭐ the crypto-proof layer (prove the metric ran) |
| IndicTrans2 | — | generate/validate Sanskrit + scaffolding |
| MT-Lens | — | leaderboard visualization |

---

*These are mature, standard toolkits — we adopt, we don't reimplement. The novel contribution is NOT
rebuilding COMET or zkML; it is (1) a Sanskrit DA/MQM gold, (2) school + period conditioning, (3) the
per-school × per-period leaderboard, and (4) a **proof-of-translation** scheme that binds a metric score
(quality) to a cryptographic commitment (integrity) — nobody does that combination. Full citations:
`research/DEEP-DIVE-COMET-CRYPTO-VERIFICATION.md`.*

