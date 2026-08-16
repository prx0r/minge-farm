# PROOF OF TRANSLATION — verifiable LLM translation (research)

*2026-08-16 · how to make an LLM-produced translation a verifiable PĀṬALA PROOF, not an assertion.
Grounds the science-lab quality axis + the canonical translation gate. Built from the established
MT-evaluation literature (COMET-family, BLEURT, chrF/BLEU, error-span detection) + our own error-family
work from Mitrasamgraha.*

---

## 1. THE PROBLEM (what "proof of translation" means)

An LLM translation is not "true" because a model wrote it. It becomes a **Pāṭala PROOF** only when an
**independent, reproducible check** shows it does what its name claims (AGENTS.md §0: the ONE RULE).
For translation, "proof" = the output satisfies deterministic, checkable constraints:

```
SOURCE_BINDING   every rendered clause traces to source words (no hallucinated content)
TERM_CONSISTENCY technical terms map 1:1 to a canonical glossary (no drift)
ABSTENTION       unsure spans are flagged AMBIGUOUS, never invented
COVERAGE         the whole source verse is addressed (no dropped pādas)
SEMANTIC_FIDELITY the meaning matches an independent gold (the quality axis)
```

A translation is **PASS** when all deterministically-checkable dimensions pass; the quality axis
(semantic fidelity vs gold) grades it, not gates it.

---

## 2. THE METRIC LITERATURE (what's established, what we use)

| Metric | What it measures | In our harness | Verifiable? |
|---|---|---|---|
| **BLEU** | n-gram precision (word overlap) | yes | weak — punishes correct-but-differently-worded |
| **chrF** | char-n-gram F1 | yes | better than BLEU for morphologically rich Sa |
| **BLEURT** | learned regression, BERT-based, handles paraphrase | recommended | trained model |
| **COMET-20 / XCOMET** | learned quality estimate (reference-based / QE), **correlates best with human** | recommended | trained model |
| **LLM-as-judge** | a model rates semantic fidelity 1-5 + gives a reason | yes (our `fidelity`) | the actionable one |
| **Error-span** | marks WHERE the translation diverges (addition/omission/misread) | derived from judge | the "proof" evidence |

**Key finding from our Mitrasamgraha runs:** BLEU/chrF **understate** good Sanskrit translations
(correct wording ≠ gold wording). The **LLM-as-judge semantic-fidelity score + its free-text reasoning**
is the honest quality number, and the reasoning *is* the error-family evidence (the proof's audit trail).

---

## 3. THE PROOF CHAIN (how a translation becomes a Pāṭala PROOF)

```
SOURCE verse (immutable, sha256)
   → [LLM] translation  (candidate)
   → DETERMINISTIC CHECKS: SOURCE_BINDING · TERM_CONSISTENCY · ABSTENTION · COVERAGE   ← PASS/BLOCK
   → QUALITY AXIS: semantic_fidelity vs gold (LLM-judge) + error-family labels           ← 0-1 / PASS
   → if all deterministic PASS → the translation is a verifiable PROOF (published)
        lineage: {result_id, gold_version, model_version, source_sha, checks, fidelity, date}
```

The deterministic checks are the **gate** (fail-closed: a dropped pāda or hallucinated clause BLOCKS).
The semantic score is the **grade**. Both are logged with full lineage.

---

## 4. THE ERROR FAMILIES (the proof's evidence categories, from Mitrasamgraha)

The judge's reasoning is classified into the known error families:

```
compound semantic loss · scope loss · case-role inversion · negation loss
implicit-subject error · technical-term substitution · metaphor literalisation
unlicensed explicitation · dropped pāda (COVERAGE) · hallucination (SOURCE_BINDING)
```

Each family maps to a **deterministic L200/translation_gate check** where possible, so the proof is
not just a score but a **categorized audit** of *what could be wrong and whether it was checked*.

---

## 5. HOW THIS BECOMES THE SCIENCE-LAB QUALITY AXIS

Every science-lab experiment scores against the **fixed gold** (sanskrit_gold.py, per tradition) using:
- `score_vs_gold()` → semantic fidelity 0-1 (LLM-judge vs the IPVV exemplars)
- + the deterministic proof checks (PASS/BLOCK)

So an experiment reports **speed + cost + quality** on the SAME fixed data — the "compare, not assert"
rule with a real quality axis, not just wall-clock.

---

## 5.5 VERIFIED LITERATURE (arXiv, fetched 2026-08-16)

| Paper | arXiv | Why it matters |
|---|---|---|
| Translation as a Scalable Proxy | 2601.11778 | **xCOMET correlates 0.91, MetricX 0.89** with downstream — learned QE is the strongest proxy |
| COMET-poly | 2508.18549 | evaluate a translation **against multiple candidates** (+0.08-0.12 tau) — better than single-ref |
| SSA-COMET | 2506.04557 | learned metrics **vs LLM-judge for under-resourced langs** — directly relevant to Sanskrit |
| Error Span Annotation (ESA) | 2509.13980 | predict **WHERE** the translation is wrong — the proof's evidence, not just a score |
| Reflective Translation | 2601.19871 | self-reflection (critique→revise) improves BLEU +0.22 / COMET +0.18 — a candidate method |
| Ref-Free QE / COMET-Kiwi | 2605.15976 | quality estimation **without a gold reference** — QE for untranslated works |
| QE-informed retranslation | 2511.13884 | select best of N candidates by QE (Delta COMET +0.02) — the WMT25 winning approach |

**Implication for the Pāṭala proof:** the field has moved past BLEU/chrF. The verifiable proof should
combine: **COMET-family learned QE** (best human correlation) + **LLM-as-judge semantic fidelity** (the
actionable error-family reasoning) + **Error-Span detection** (WHERE it's wrong) + **multi-candidate
selection** (COMET-poly / QE-informed). chrF/bleu remain only the cheap surface baseline.

## 6. THE BETTER SANSKRIT BENCHMARK (beyond chrF)

Our benchmark is **per-tradition specialist + quality-axis**, not a single BLEU number:
- **Fixed gold controls per tradition** (Pratyabhijñā/Trika, Krama, Śaiva Siddhānta) — `sanskrit_gold.py`
- **Metric**: semantic fidelity (LLM-judge, 0-1) + deterministic proof checks + chrF/bleu as surface
- **Leaderboard axis**: quality × speed × cost, per tradition
- **Error-family profile**: what each model gets wrong (the actionable output)

This is what "nobody else has" — a *verifiable* Sanskrit translation benchmark, not just BLEU.

---

*The proof-of-translation: deterministic checks gate, semantic fidelity grades, error-family reasoning is
the audit. Science lab runs experiments on the same fixed gold → the winner is a proof, not an opinion.*
