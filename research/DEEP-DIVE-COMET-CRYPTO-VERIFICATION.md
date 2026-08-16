# DEEP-DIVE — COMET/ML translation verification + cryptographic proofs for translations

*2026-08-16 · A citation-verified deep-dive (arXiv + GitHub, live-fetched) on two threads that power the
sanskritbenchy vision: (A) using COMET/ML to VERIFY translation quality, and (B) creating CRYPTOGRAPHIC
proofs / commitments for AI-generated translations. This grounds the "verify + prove" architecture of the
benchmark. **The single most important finding is stated first: verification of computation ≠ verification
of semantics.***

---

## 0. THE CENTRAL DISTINCTION (read before anything)

> **zkML / verifiable inference / TEE attestation prove that a SPECIFIC COMPUTATION RAN CORRECTLY (with
> the claimed weights, on the claimed input, via a committed execution trace). They do NOT prove the
> output is semantically correct, faithful, or a good translation.**

Two orthogonal problems:
- **Semantic verification** (is this a faithful Sanskrit translation?) → **COMET/ML learned metrics**.
- **Computational / provenance verification** (did this specific model/run produce this exact string,
  unaltered?) → **zkML / commitments / attestation / watermarking**.

For a Sanskrit fidelity benchmark: zkML answers "did the advertised model really produce this string?",
COMET answers "is this string a faithful translation?" **The honest architecture binds the two, keeping
them distinct in every claim.**

---

## PART A — VERIFYING TRANSLATION QUALITY WITH COMET / ML

### A.1 The COMET family (the flagship learned metric)

| Model | arXiv | What it does | Sanskrit? | Code |
|---|---|---|---|---|
| **COMET** | 2009.09025 | neural regressor `[src, hyp, ref]` → 0..1; trained on human DA/HTER/MQM | XLM-R covers it (unreliable) | ✅ Unbabel/COMET |
| **COMET-22** | *no arXiv* (WMT22 system report) | retrained on WMT21+22 DA; `wmt22-comet-da` + ref-free `cometkiwi-da` | covered (unreliable) | ✅ in Unbabel/COMET |
| **CometKiwi** | 2209.06243, 2309.11925 | **reference-free QE** `(src, hyp)`; 1st place WMT22/23 | covered (unreliable) | ✅ |
| **xCOMET** | 2310.10482 | score **+ MQM error spans** + hallucination detection | covered | ✅ (+xCOMET-lite 2406.14553) |

**Key point for Sanskrit:** COMET models inherit XLM-R's language coverage — Sanskrit is nominally
covered but **poorly trained**, and XLM-R tokenizes Sanskrit's long compounding (sandhi/avyayībhāva)
badly. **Reference-free QE (CometKiwi) is the most valuable for us** because Sanskrit references are scarce.

### A.2 Beyond COMET

| Metric | arXiv | Note | Runnable |
|---|---|---|---|
| **MetricX-24/25** | 2410.03983, 2510.24707 | Google, hybrid ref+QE, mT5/Gemma-based; strong | ✅ (needs GPU for XL/XXL) |
| **BLEURT** | 2004.04696 | BERT regression; aging | ✅ |
| **UniTE** | 2204.13346 | unified ref/source/combined | ✅ |
| **BARTScore** | 2106.11520 | evaluation-as-generation; unsupervised | ⚠️ English-biased |
| **afriCOMET** | (NAACL'24) | COMET for 13 African low-resource pairs — **the exact recipe to replicate for Sanskrit** | ✅ |
| **GemSpanEval** | 2510.24707 | decoder-only error-span + severity | ✅ |
| **HiMATE** | 2505.16281 | multi-agent MQM span detection | ✅ |

### A.3 Verified limitations of ALL learned metrics (the honesty guard)
- **None are trained on Sanskrit** — you must fine-tune a Sanskrit-aware COMET (like AfriCOMET did for
  African languages), on a **Sanskrit human-judgment set you build** (Phase A DA/MQM).
- Learned metrics **reward fluency over meaning** and show **metric bias** under reward-hacking
  (arXiv:2411.03524).
- **Data contamination inflates COMET-22/BLEU badly** on low-resource NMT (arXiv:2605.07453: 83.8 vs
  30.9–39.2). **Decontaminate the Sanskrit test set at the token level.**
- The right Sanskrit encoder base is **byte-level (ByT5-Sanskrit, 2409.13920)** or a Sanskrit-capable LLM
  (**Gemma-2-MITRA, 2601.06400**) — **not XLM-R.**

### A.4 Meta-evaluation (proving "metric X beats BLEU")
- **MTME** (`google-research/mt-metrics-eval`) — the standard toolkit: Kendall/Spearman/Pearson of a metric
  vs human gold, significance tests. **Adopt it** (replaces our hand-rolled tau). Runs on CPU.
- `wmt-mqm-human-evaluation` (Google) — the expert MQM human-gold **format** to emulate for our Sanskrit gold.
- `span-mt-metaeval` (Amazon) — LLM-as-judge meta-eval pattern.

---

## PART B — CRYPTOGRAPHIC PROOFS FOR AI-GENERATED TRANSLATIONS

### B.1 zkML / verifiable inference (prove "this model ran → this output")

| Project | arXiv / repo | What it actually proves | Usable for a small proof? |
|---|---|---|---|
| **zkLLM** | 2404.16109 | ZK proof an LLM produced an output (13B in <15 min, <200 kB) | ⚠️ research; folded into NilFoundation zkLLVM monorepo |
| **NanoZK** | 2603.18046 | layerwise ZK proofs, SHA-256 commitment chain (~83 kB, ~22 ms verify) | ⚠️ research |
| **VeriLoRA** | 2508.21393 | ZK verification of LoRA fine-tuning | ⚠️ if we fine-tune |
| **TensorCommitments** | 2602.12630 | tensor-native proof-of-inference, low overhead | ⚠️ not open-sourced (404) |
| **sampling-based verifiable inference** | 2603.19025 | Merkle-tree commitments over trace, ms proving (trades soundness) | ✅ cheap but lossy |
| **RISC Zero** | risc0/risc0 | general zkVM → **receipt** (journal+seal) tamper-evident | ✅ most general, GPU-heavy |
| **EZKL** | zkonduit/ezkl | ONNX→ZK-SNARK, proves a public network ran on inputs → output; audited (Trail of Bits) | ✅ **primary candidate** (small models on 8GB CPU) |
| **=nil; zkLLVM / zkML** | NilFoundation | circuit compiler; zkML/ZKFHE | ⚠️ heavy C++, not turnkey |
| **proof-of-learning** | 2103.05633 | proves model OWNERSHIP (SGD compute); **forgeable** (2108.09454) | ❌ don't build on it |
| **AEX** | 2603.14283 | signed attestation binding request→response | ⚠️ proposal, no mature repo |

**Honest verdict:** every zkML tool proves **compute integrity, not quality**. EZKL (ONNX→proof) is the
most practical to prove "we ran this COMET model on these inputs → this score"; RISC Zero gives the most
general tamper-evident receipt. **Neither proves the translation is good.**

### B.2 Cryptographic commitments + watermarking (prove provenance / unaltered)

| Project | arXiv | What it does | Fit |
|---|---|---|---|
| **LLM watermark** | 2301.10226 | statistical "green token" signature; proven provenance | ✅ if we control the generator |
| **Complementary watermarks** | 2608.12713 | robust (provenance) + fragile (tamper-evident); 3-state Intact/Tampered/None | ✅ tamper-evidence |
| **DHMark** | 2608.03093 | public-key watermark, third-party verifiable | ✅ |
| **hash/Merkle commitment** | (2604.25200 grant-eval pattern) | commit `(src, hyp, ref, metric_score)`; signed/timestamped attestation bundle | ✅ **the practical pattern** |

**The practical commitment for our benchmark:** commit the `(source, hypothesis, reference, metric_score)`
tuple with a hash/Merkle root, plus a signed timestamp + model-ID (the 2604.25200 attestation-bundle
pattern). This makes a translation **provably unaltered and attributable**, while COMET provides the
quality signal. Optional: wrap in an EZKL/RISC-Zero proof to attest "this metric scored these inputs."

---

## PART C — SANSKRIT-SPECIFIC TOOLING (what actually exists)

| Resource | arXiv/repo | What | Fit |
|---|---|---|---|
| **Mitrasamgraha** | 2601.07314 | 391K Sa–En bitext, 3,000+ yrs, period+domain annotated; **already benchmarks COMET-22** | ✅ **corpus anchor** |
| **Samasāmayik** | 2603.24307 | 92K Hindi–Sa, contemporary | ✅ data |
| **MITRA** | 2601.06400 | 1.74M Sa/Pāli/Buddhist-Ch/Tib + Gemma-2-MITRA semantic model | ✅ semantic-similarity verifier candidate |
| **IndicTrans2** | AI4Bharat/IndicTrans2 | SOTA NMT for 22 Indic langs **incl. Sanskrit `san_Deva`**; ships COMET eval scripts (`compute_comet_score.sh`) | ✅ generate/validate + scaffolding pattern |
| **ByT5-Sanskrit** | 2409.13920 | byte-level pretrained model for morphologically-rich Sanskrit | ✅ the encoder base for a Sanskrit COMET head |
| **Pingala** | 2603.24413 | prosody-aware decoding + **reference-free cross-encoder eval for Sanskrit poetry** | ✅ a Sanskrit-specific ref-free scorer precedent |
| **Chandomitra** | 2506.00815 | English→structured Sanskrit poetry, 99.86% metrical validity | ✅ scholarly-fidelity template |

**Direct finding:** `arXiv query "Sanskrit AND translation AND quality estimation" → 0 results.` **No
published Sanskrit MT quality-estimation or Sanskrit learned metric exists.** That is our open space.

---

## THE VERIFIED "VERIFY + PROVE" ARCHITECTURE (for the benchmark)

```
1. SEMANTIC VERIFY (quality)          — COMET (wmt22-comet-da / CometKiwi ref-free) on a
                                         byte-level/Sanskrit-aware encoder; per-school × per-period
2. DIAGNOSE (where it diverges)       — xCOMET / GemSpanEval error spans (hallucination, category, severity)
3. META-EVALUATE (prove "better")     — MTME: tau/Spearman of our metric vs Sanskrit human DA/MQM gold,
                                         beats chrF/bleu (logged)
4. CRYPTO COMMIT (prove "this run")   — hash/Merkle commit of (src, hyp, ref, score) + signed timestamp
                                         + model-ID (attestation-bundle pattern); optional EZKL/RISC-Zero
                                         compute-integrity proof that the metric scored these inputs
5. PROVENANCE (optional)              — watermark if we control the generator (2301.10226 / 2608.12713)
```

**The honest rule:** step 4 proves *integrity* (this run → this output), never *quality*. Only steps 1–3
prove quality. Keep the two domains distinct in every claim. **Do not call a zkML proof "proof of a good
translation."**

---

## KEY CORRECTED / VERIFIED IDs (so we cite right)
- proof-of-learning = **arXiv:2103.05633** (2007.15164 is physics).
- LLM watermark = **arXiv:2301.10226** (2303.15498 is astrophysics).
- COMET-22 = **no arXiv** (WMT22 system report, ACL anthology).
- **No "proof-of-translation" paper exists** — a genuine gap our benchmark could pioneer.

## KEY GAPS WE FILL (the open space)
1. **No Sanskrit DA/MQM human-judgment set** (the prerequisite — Phase A).
2. **No Sanskrit learned metric** (fine-tune COMET on a Sanskrit-aware encoder, AfriCOMET recipe).
3. **No school × period-conditioned metric** (Phase C, the *vimarśa* test).
4. **No proof-of-translation crypto scheme** — commit + attest (integrity) layered with metric (quality) is
   ours to define.
