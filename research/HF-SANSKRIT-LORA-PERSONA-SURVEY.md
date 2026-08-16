# HF + RESEARCH SURVEY — Sanskrit style/persona translation, LoRA, lemmatization, licensing

*2026-08-16 · A live-verified survey (HuggingFace + arXiv + GitHub) powering the product vision in
`VISION.md` (§ translate-as-different-people · verify · license). Every URL was fetched and confirmed.*

---

## 1. HuggingFace orgs/labs doing Sanskrit

| Org / model | URL | What | Reusable? |
|---|---|---|---|
| **AI4Bharat** (IIT Madras) | huggingface.co/AI4Bharat | 143 models, 78 datasets; **IndicTrans3-beta** (Gemma3-based) covers 22 Indic langs **incl. Sanskrit**; IndicTrans2 earlier | ✅ general Sanskrit MT (GGUF on CPU); Sanskrit is a tiny low-resource corner, not style-aware |
| **BharatGen AI** (IIT Bombay) | huggingface.co/bharatgenai | Param family (Indic + domain); **no Sanskrit translation model** | ❌ core |
| **ambuda / buddhist-nlp / chronbmm** (Nehrdich) | huggingface.co/chronbmm | the real Sanskrit lab: **`sanskrit5-multitask`** (0.6B ByT5 for segmentation + **lemmatization** + morphotagging), `nllb-3B-sanskrit-eng`, ByT5-Sanskrit, OCR post-correction | ✅ **the lemmatization layer** (CPU-runnable) |
| **ayushbits** | huggingface.co/ayushbits | datasets (Sāmayik, OCR); no strong model | ⚠️ |
| `diabolic6045/Sanskrit-qwen-7B-Translate-v2` | HF | Qwen2.5-7B fine-tune, Devanagari+IAST | ⚠️ 7B → only at 4-bit, not style-conditioned |

**Verdict:** no org has built *style-persona Sanskrit translation*. Reusable infrastructure = AI4Bharat
(general MT) + the ambuda/buddhist-nlp cluster (lemmatization).

## 2. LoRA / PEFT for translation STYLE + PERSONA

- **LoRA** — arXiv:2106.09685 (no added inference latency — key for serving N adapters).
- **QLoRA** — arXiv:2305.14314 (4-bit NF4; train a persona adapter cheaply).
- **The working multi-adapter pattern (verified):** the `ascerfcefc/sanskrit-poetry-qwen3-4b-*-lora` family —
  dozens of **LoRA SFT adapters on ONE base** with register-encoding names (`modern-strict-v1`,
  `modern-full-v1`, `cleanmix`, `goldmix`, `anti-regression`, …). **Proves the stack**, but ~0–8 downloads,
  no eval/data → a template, not an asset.
- **Style/persona-conditioned translation: essentially unbuilt.** Closest academic precedent:
  - Personalized MT preserving author traits — arXiv:1610.05461 (EACL 2017)
  - Compact personalized NMT (group-lasso per-user offsets) — arXiv:1811.01990 (EMNLP 2018)
- **Temperature/strictness:** no dedicated "loose vs literal" paper; combine low-temp+beam (literal) vs
  high-temp (loose) with per-persona LoRA. Standard decoding practice.
- **Junk flagged:** `Sudhanshu1106Shekhar/qwen-sanskrit-translation-adapter` is an empty stub (no
  adapter_config.json) — do not use.

## 3. Sanskrit lemmatization / morphology through the ages

| Resource | What | CPU? |
|---|---|---|
| **ByT5-Sanskrit** (arXiv:2409.13920) | byte-level, SOTA segmentation/lemmatization/morphotagging/Vedic parsing | ✅ `chronbmm/sanskrit5-multitask` 0.6B ≈1.2GB |
| **Vidyut** (ambuda-org/vidyut) | Rust + Python bindings: `vidyut-prakriya` (Pāṇinian generation), `vidyut-kosha`, `vidyut-cheda` (segmentation+morphology), sandhi, chandas | ✅ `pip install vidyut` |
| **CDSL** (sanskrit-lexicon/csl-orig) | raw data for ALL Cologne dictionaries, incl. Monier-Williams 1899; `csl-atlas` comparative across 9 | ✅ data |
| **DCS** (OliverHellwig/sanskrit) | annotated Vedic/Sanskrit corpus the ByT5 paper trained on | ✅ data |

**The honest gap:** no public resource maps **lemma → sense → (school, period)** (the *vimarśa*-in-
Pratyabhijñā vs Śaiva-Siddhānta problem). CDSL + DCS give lemma→sense inventories **without** school/period
metadata. **Mapping lemma→(school,period)→sense is our moat + our research problem** — built from the
dictionaries + Pāṭala.

## 4. Translation verification as a product / licensing

- **COMET** (`Unbabel/wmt22-comet-da`, Apache-2.0) scores (src,mt,ref) 0–1, **CPU-runnable** (~1.5GB).
  **Caveat:** XLM-R covers Sanskrit only weakly → **unvalidated on classical Sanskrit** (we need our own
  eval set).
- **MQM** — the human error-annotation rubric (no model; the standard for verification).
- **Licensing precedent: none.** No established "license a verified MT capability" market. What you can
  actually do: license **model weights** (Apache/CC for open base+adapters, or a commercial EULA for
  proprietary adapters), license **data** (MW 1899 is public-domain; CDSL corrections are GPL/CC-BY-SA),
  and offer **verification-as-a-service** (COMET/QE score + MQM audit as a paid guarantee). The "verified
  translation" guarantee is a **product/legal construct we define** — not an existing artifact.

## 5. Diachronic / school-conditioned translation

**Direct work: none exists (verified).** No paper/model translates Sanskrit conditioned on tradition,
school, or period. ByT5-Sanskrit handles **Vedic vs Classical** partially; **post-classical schools
(Pratyabhijñā/Vedānta/Nyāya) are unbuilt.** This is the highest-risk, highest-value part — design the
conditioning (per-(school,period) LoRA, or a condition token/embedding) from scratch.

## 6. Multi-LoRA serving on 8GB CPU vs GPU

| Stack | 8GB CPU? | Note |
|---|---|---|
| **HF PEFT** | ✅ | load base once, `load_adapter`/`set_adapter` to switch styles; serial, fine for a small base |
| **vLLM multi-LoRA** | ❌ GPU | cleanest production path but CUDA (Punica kernels) |
| **TGI multi-LoRA** | ❌ GPU-preferred | CUDA-oriented |
| **llama.cpp / GGUF** | ✅ | quantized single base on CPU; no multi-LoRA for MT |

**Honest split:** train per-persona LoRAs (QLoRA) on a **GPU**; serve a **≤2B base** with **PEFT** on this
8GB box. Don't serve 7B+ multi-LoRA here.

---

## The bottom line (aspirational vs built)

- **Built & CPU-runnable:** ByT5-Sanskrit lemmatization, Vidyut morphology, CDSL/DCS data, COMET/QE scoring
  (Sanskrit-validation caveat), AI4Bharat IndicTrans3 general MT, and the LoRA mechanism via PEFT.
- **Pattern proven but not product-grade:** multi-style-LoRA-on-one-base (`ascerfcefc` family).
- **Must build ourselves (the actual moat):** per-persona *translator-style* LoRAs; **school/period sense
  disambiguation (*vimarśa*)** — no prior art; the **verified/licensed-translation commercial wrapper** —
  no precedent; and a **Sanskrit-specific COMET/MQM eval set** (off-the-shelf COMET is unvalidated on
  classical Sanskrit).

*Day-1 prototype on this box: ByT5-Sanskrit lemmatization → lemma→sense disambiguation from CDSL/DCS →
a "verified" COMET-gated output.*
