# VISION ADVICE — the frontier-research blueprint for a legitimate Sanskrit MT system

*2026-08-16 · Saved verbatim from a wide frontier sweep across Sanskrit NLP, MT research, COMET/QE,
uncertainty calibration, preference/RL training, retrieval, and classical-language benchmark design. This
is the architectural blueprint. Use it to drive the build; the infra list is in `INFRA-REQUIREMENTS.md`.*

---

Yes. I did a fairly wide sweep across **Sanskrit NLP, current MT research, COMET/QE, uncertainty
calibration, preference/RL training, retrieval, translation evaluation, and classical-language benchmark
design**. The main conclusion is that a genuinely cutting-edge Sanskrit translator in 2026 should **not be
one model**.

It should be a system:

**Sanskrit-specialized translator → parallel-text RAG → multiple candidate generation → Sanskrit-aware linguistic verification → learned QE/error detection → calibrated uncertainty → evidence/provenance certificate.**

That is substantially more defensible than "fine-tune Qwen/Gemma and report BLEU."

## 1. The Sanskrit landscape changed dramatically in 2026

The biggest new resource is **Mitrasaṃgraha, arXiv:2601.07314**. It contains **391,548 Sanskrit→English aligned pairs**, spans Vedic, Epic, Classical and Medieval material, covers six literary domains, preserves document-level metadata, and provides **5,587 validation + 5,552 manually post-corrected test pairs**. There is also a 372,791-pair research-friendly CC BY-SA subset.

This immediately replaces Itihāsa as the obvious base Sanskrit-English training resource.

More interestingly, its authors actually tested Sanskrit MT metrics against Sanskrit experts. **BLEU and chrF were much weaker than BLEURT and GEMBA/GEMBA***. They also compared seven legitimate human translations of 100 Bhagavad-gītā verses and found average pairwise BLEU only **25.2** and chrF **44.0**. In other words, perfectly legitimate Sanskrit translations can look dramatically different under surface-overlap metrics.

That's extremely important for the benchmark you want.

The same paper gives a strong hint about architecture. Claude 3.7 Sonnet went from GEMBA **86.24** to **89.32** with retrieval from Sanskrit-English training examples; Gemini 1.5 Pro rose from **79.61** to **84.70** with RAG. But explicitly inserting grammatical analysis alongside RAG slightly *hurt* performance relative to RAG alone.

So my interpretation is:

> **Use Sanskrit grammar primarily as a verifier and structured representation, not as a giant block of morphology dumped into the translator prompt.**

That is a surprisingly useful result.

---

# 2. There is now effectively a Sanskrit foundation-model project

The other major 2026 development is **MITRA, arXiv:2601.06400**.

MITRA contains **1,742,786 aligned Sanskrit/Chinese/Tibetan sentence pairs**, including roughly **596,812 Sanskrit↔Tibetan alignments**. The authors continuously pretrained Gemma 2 9B on **4.4B domain-specific tokens**, then produced **MITRA-MT** for translation and **MITRA-E** for semantic retrieval. Their published evaluation reports MITRA-MT outperforming substantially larger generic open models on Sanskrit/Pāli/Tibetan/Buddhist-Chinese→English tasks.

MITRA is particularly valuable because it gives you three things rather than merely another checkpoint:

| Component          | Why it matters                                 |
| ------------------ | ---------------------------------------------- |
| **MITRA-MT**       | Sanskrit-specialized translator baseline       |
| **MITRA-E**        | Sanskrit-aware semantic retrieval model        |
| **MITRA-parallel** | Cross-canonical multilingual parallel evidence |

The MITRA training recipe itself is worth stealing: strong general model → continued pretraining on monolingual + parallel domain material → translation instruction tuning → separate contrastive retrieval specialization. The authors explicitly say this follows the Tower specialization recipe.

There is also something newer. The DharmaMitra Hugging Face organization now contains **experimental Qwen3.5-based MITRA models**, including `mitra-qwen35-base-stage1`, `stage2`, `mitra-qwen35-it`, 2B versions and an embedder, updated only weeks ago. I found the checkpoints, but not yet a corresponding research paper sufficiently documenting their training/evaluation. Treat these as **high-priority experimental baselines, not established SOTA claims**.

That should probably be one of your very first experiments: **published MITRA-MT vs current MITRA-Qwen3.5 vs your own adapted model on a blind Sanskrit benchmark.**

---

# 3. Sanskrit datasets worth acquiring

| Dataset                        |                            Size | Character                                             | How I would use it                                                                                                                                                             |
| ------------------------------ | ------------------------------: | ----------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Mitrasaṃgraha**              |                   391,548 Sa→En | Vedic → Medieval, multiple genres                     | **Primary Sanskrit-English SFT corpus + starting benchmark**.                                                                                                                    |
| **MITRA-parallel**             |                     1.74M total | Sanskrit/Chinese/Tibetan Buddhist parallels           | Auxiliary representation learning, retrieval, multilingual consistency verification.                                                                                             |
| **Itihāsa**                    |                          93,000 | Rāmāyaṇa + Mahābhārata verses, one English translator | Useful epic-domain auxiliary data, but far too narrow to be the main corpus.                                                                                                    |
| **Sāmayik**                    |                          52,961 | Contemporary Sanskrit prose ↔ English                 | Useful modern/prose domain control and English↔Sanskrit experiments.                                                                                                            |
| **Samasāmayik**                |                          92,196 | Contemporary Hindi↔Sanskrit                           | Auxiliary multilingual transfer; published in 2026 with ByT5/NLLB/IndicTrans-v2 baselines.                                                                                     |
| **SAHAAYAK 2023**              |                            1.5M | Sanskrit↔Hindi, multiple domains                      | Potentially huge auxiliary corpus, but because it combines several mining routes I would audit noise/provenance carefully before using it heavily.                               |
| **SansTib**                    |                         317,289 | Sanskrit↔Classical Tibetan                            | Especially valuable for Buddhist Sanskrit semantic representation and triangulation.                                                                                           |
| **Digital Corpus of Sanskrit** | >650k annotated units/sentences | Sandhi-split + lexical/morphological annotation       | Linguistic auxiliary training rather than translation SFT.                                                                                                                      |

There is a particularly nice opportunity here: **multilingual triangulation**.

Suppose Sanskrit passage (S) survives alongside Tibetan (T), Chinese (C), and one English translation (E). Your translator outputs (E'). Instead of merely asking whether (E') looks like (E), test whether S↔E' and T↔E', C↔E' all preserve approximately the same semantic content.

MITRA is practically tailor-made for this kind of cross-witness verification.

For Buddhist Sanskrit, that's a potentially very powerful additional evidence channel.

---

# 4. Sanskrit analysis components you should steal rather than rebuild

**ByT5-Sanskrit, arXiv:2409.13920** is one of the highest-value components. It uses byte-level modeling and established new results for Sanskrit segmentation, Vedic dependency parsing and OCR correction, while also supplying a multitask DCS-derived model for segmentation, lemmatization and morphosyntactic tagging. The authors explicitly report using it as preprocessing in Sanskrit MT.

The associated DharmaMitra analyzer repo exposes the inference components.

**Vidyut** is also excellent infrastructure. `vidyut-cheda` provides fast segmentation plus morphological annotation; other components handle sandhi, transliteration, inflectional lexica, meter and Pāṇinian derivation.

**Samsaadhanii/SCL** gives another independent linguistic channel: morphological analyzer/generator, sandhi joiner/splitter, compounds, Sanskrit-Hindi MT, Amarakosha and an Aṣṭādhyāyī simulator.

The key word there is **independent**. If both a neural ByT5 analyzer and symbolic/lexicon-oriented analyzer agree on a segmentation and morphology, that is useful evidence. If they disagree, the translation should become less confident.

---

# 5. COMET is useful — but COMET is absolutely not your confidence score

This distinction matters.

The official COMET project says directly that its raw score generally **does not have a direct probabilistic interpretation**. It is useful for ranking translations and systems, but `COMET = 0.86` does **not** mean "86% probability this translation is correct."

For your project I would distinguish four separate things:

| Quantity              | Question                                                   |
| --------------------- | ---------------------------------------------------------- |
| **Quality score**     | How good does the translation appear overall?              |
| **Error probability** | How likely is a major/critical error?                      |
| **Uncertainty**       | How unsure is the evaluator about its prediction?          |
| **Evidence coverage** | How much of the source can independently be accounted for? |

Those are not the same number.

### xCOMET

**xCOMET** is substantially more interesting than plain COMET for your system because it jointly predicts sentence quality **and locates error spans with severity information**. This makes it useful for your audit layer rather than merely returning a scalar.

### COMETKiwi

COMETKiwi performs **reference-free quality estimation**: source + candidate translation, without needing a gold English reference. That's essential when translating previously untranslated Sanskrit.

### Instant Confidence COMET

Very relevant and very recent: **Early-Exit and Instant Confidence Translation Quality Estimation**, EACL 2026. It augments QE with an inexpensive uncertainty estimate and uses confidence-aware early exits/reranking; the authors report roughly **50% compute reduction** with little quality degradation.

This is much closer to what you mean by legitimate ML confidence.

But even this should be **recalibrated on Sanskrit**.

A 2026 massively multilingual QE study covering more than 41,000 translation directions found that **no evaluator was universally reliable across directions**, and even naive ensembles could dilute useful signals.

That is another major reason not to blindly average five evaluator scores.

---

# 6. I would build your own Sanskrit evaluator

This is potentially a research contribution in itself.

Call the conceptual thing **SaCOMET / SanskritQE** for now.

Train it on triples such as (Sanskrit source, English candidate, human error annotations) and optionally quadruples with an English reference.

Instead of giving it just a scalar supervision target, annotate error spans.

Your Sanskrit extension to MQM should distinguish ordinary MT errors from Sanskrit-specific ones:

| Error family          | Sanskrit-specific examples                                            |
| --------------------- | --------------------------------------------------------------------- |
| Accuracy              | omission, unsupported addition, mistranslation                        |
| Segmentation          | incorrect sandhi split                                                |
| Morphology            | wrong number, case, gender, verbal person/tense/mood/voice            |
| Syntax                | wrong kāraka/argument relation                                        |
| Compounding           | wrong samāsa decomposition or semantic head                           |
| Scope                 | negation, restriction, quantification                                 |
| Lexical semantics     | wrong sense of a polysemous term                                      |
| Coreference           | implicit subjects, pronouns, ellipsis                                 |
| Technical terminology | philosophical/ritual/grammatical technical term mistranslated         |
| Poetic semantics      | metaphor/image flattened or incorrectly literalized                   |
| Textual structure     | quotation/commentary boundary confusion                               |
| Style                 | register or readability problems, kept separate from factual adequacy |

Then predict both Q_segment and per-span labels (e_i, category_i, severity_i).

That follows the direction of xCOMET and Google's **GemSpanEval**, rather than merely regressing one fuzzy number. MetricX-25 simultaneously shows where learned MT scoring itself is heading: Gemma-3-derived MetricX-25 predicts MQM/ESA quality scores, while GemSpanEval produces error spans with categories and severities.

There is now research showing that **token-level xCOMET error/severity rewards can improve MT training more effectively than a single sentence reward**, which is extremely relevant if you eventually use your Sanskrit evaluator as a training reward.

---

# 7. The strongest confidence system I can see

Define something measurable first.

Do **not** train a model to estimate vague "confidence."

Define Y=1 iff a Sanskrit expert judges the translation to contain **no major/critical semantic error** and to meet your chosen acceptability threshold.

Now collect a feature vector z = [q_xCOMET, q_MetricX, q_SaQE, N_major spans, N_critical spans, A_alignment, M_morph, R_retrieval, D_ensemble, C_crosslingual, B_backtranslation]

where, for example:
- A_alignment = source→target semantic/word alignment coverage.
- M_morph = how completely the candidate accounts for source morphology/arguments.
- R_retrieval = evidence strength from genuinely similar human translation examples.
- D_ensemble = semantic disagreement across independently sampled translations.
- C_crosslingual = agreement with Tibetan/Chinese parallels where available.

Then learn P(Y=1 | z) from human-labelled Sanskrit data.

A relatively boring calibrated logistic model or monotonic boosting model may actually be preferable here to another gigantic LLM because you want the final calibration layer to be inspectable.

Then calibrate on **data the model has never trained on**, using isotonic calibration, Platt/logistic calibration or similar.

Finally add **conformal prediction**.

---

# 8. Conformal prediction is probably the missing piece in your idea

The TACL paper **"Conformalizing Machine Translation Evaluation"** is one of the most important papers for what you're proposing.

The authors show that ordinary MT uncertainty estimators often produce confidence intervals that are **too narrow and fail to cover the true human quality value**. They apply split conformal prediction to turn existing uncertainty estimates into intervals with a desired marginal coverage guarantee, given the conformal assumptions and a representative calibration set. They also investigate conditional/equalized conformal methods because coverage can differ across languages and translation difficulty.

This gives you something much more scientifically respectable than "confidence = 91%".

You can output something like:

**Estimated expert quality:** 86/100
**90% conformal interval:** 78–92
**P(no major accuracy error):** 0.94
**Evidence coverage:** 97%
**Abstention:** No

Or:

**Estimated quality:** 73/100
**90% interval:** 49–87
**P(no major error):** 0.61
**Evidence coverage:** 81%
**Abstention:** **YES — human review required**

That is much closer to a legitimate production confidence system.

And I would calibrate separately or conditionally for **Vedic / Epic / Classical prose / kāvya / Buddhist Hybrid Sanskrit / philosophical commentary / technical śāstra**, because the error distribution will plainly not be homogeneous.

---

# 9. Your benchmark should be considerably better than existing Sanskrit benchmarks

The most useful blueprint I found isn't Sanskrit. It's **PaliBench, arXiv:2605.16881**, published this year specifically as a **multi-reference blueprint for classical-language translation benchmarking**.

Its central premise is exactly your problem: single-reference evaluation unfairly penalizes valid alternative interpretations of classical texts. It aligns classical passages with multiple independently produced scholarly English translations and treats the methodology as reusable for other classical languages.

Combine **PaliBench's methodology + Mitrasaṃgraha's Sanskrit coverage + WMT MQM-style human evaluation**.

I would make your gold benchmark roughly **5,000–10,000 passages**, eventually, but begin with a beautifully annotated 1,000–2,000 rather than 20,000 questionable samples.

The split must be by **work/document/author/translator**, not random sentence splitting. Otherwise neighboring verses, recurring formulae and one translator's stylistic fingerprints leak between train and test.

And create a private test component.

A particularly strong design would look like this:

| Dimension               | Strata                                                                       |
| ----------------------- | ---------------------------------------------------------------------------- |
| Period                  | Vedic / Epic / Classical / Medieval                                          |
| Religious/philosophical | Vedic, Vedānta, Buddhist, Jain, Nyāya, Mīmāṃsā, Śaiva, Śākta etc.            |
| Genre                   | prose, epic verse, kāvya, sūtra, commentary, ritual, narrative               |
| Technical               | grammar, medicine, astronomy/mathematics, law, philosophy                    |
| Difficulty              | ordinary / difficult / adversarial                                           |
| Linguistics             | sandhi, long compounds, ellipsis, free word order, negation, rare morphology |
| Semantics               | technical sense, metaphor, ambiguity, polysemy                               |
| Context                 | isolated sentence / paragraph / document-aware                               |
| Input quality           | clean edition / variant spelling / OCR corruption                            |
| Script                  | Devanāgarī / normalized IAST                                                 |

Mitrasaṃgraha itself acknowledges astronomy/mathematics and other technical material remain missing or severely underrepresented. That means deliberately filling these holes could make **your benchmark genuinely better than the training corpora rather than another random slice of them**.

---

# 10. Multi-reference evaluation is essential

Don't assign one sacred English sentence to each Sanskrit source.

Store S → {R1, R2, R3, ..., Rn} along with provenance.

For passages where independent published translations exist, use them.

For untranslated texts, have experts independently produce or adjudicate translations.

More importantly, retain **interpretive alternatives**.

Example: a source term may legitimately allow senses A and B. Your gold representation can say sense(x) ∈ {A,B} rather than pretending the benchmark knows that one English string is uniquely correct.

The low BLEU agreement between expert Bhagavad-gītā translations found in Mitrasaṃgraha is direct empirical evidence that this matters for Sanskrit.

---

# 11. Create challenge sets instead of relying only on natural sentences

This is where your benchmark could become really powerful.

For every good translation, manufacture **controlled bad translations**:

Original: candidate correctly preserves negation. Perturbation: remove the negation.

Or swap singular/plural, agent/patient, technical senses, compound heads, temporal relation, quoted speaker, etc.

Then the benchmark asks: Can the evaluator distinguish T+ from T-?

This lets you measure evaluator competence independently from translator competence.

For a Sanskrit-specific COMET-like metric, this is incredibly valuable training material too.

MetricX-24/25 and modern MT evaluator research increasingly use synthetic errors and explicit error spans because generic sentence-level scores are not enough.

---

# 12. "Translation proof" can actually become a rigorous artifact

I would not call it a mathematical proof of translation correctness; natural-language interpretation doesn't permit that in general.

But you can create a **proof-carrying translation**.

Every generated translation gets an immutable evidence object:

| Evidence               | Stored artifact                                       |
| ---------------------- | ----------------------------------------------------- |
| Source                 | original text + normalized text + hash                |
| Segmentation           | candidate word boundaries and alternatives            |
| Morphology             | lemma + case/number/gender/verb morphology            |
| Syntax                 | argument/kāraka relations where available             |
| Alignment              | Sanskrit tokens/spans ↔ English spans                 |
| Lexical evidence       | dictionary senses supporting each difficult rendering |
| Parallel evidence      | nearest human translated passages                     |
| Intertextual evidence  | Sanskrit/Tibetan/Chinese parallels                    |
| Candidate distribution | several independent translation hypotheses            |
| Evaluator evidence     | xCOMET/GemSpanEval/Sanskrit-QE error spans            |
| Terminology            | prior translations of technical terms                 |
| Uncertainty            | calibrated probability + conformal interval           |
| Provenance             | model/checkpoint/data/retrieval/version hashes        |
| Decision               | accepted / needs review / abstain                     |

The important shift is:

**Don't merely store the answer. Store enough intermediate evidence that another model—or eventually a human Sanskritist—can attack the answer.**

That is much stronger than having the translator explain itself after the fact.

---

# 13. Retrieval should become a translation-memory system, not generic RAG

Mitrasaṃgraha already demonstrated that retrieved Sanskrit-English exemplars work. MITRA gives you a Sanskrit-specialized retrieval model.

For every source passage (S), retrieve separately from:

**Translation memory:** semantically similar Sanskrit with human English.

**Lexical memory:** same lemma/compound/technical term in scholarly translations.

**Author/work memory:** translations of surrounding passages or the same author.

**Intertextual memory:** Sanskrit parallels and quotations elsewhere.

**Cross-canonical memory:** Tibetan/Chinese equivalents.

Do not combine them blindly into one vector database.

Keep the evidence classes separate so that the verifier knows whether support came from "a nearly identical Sanskrit parallel" versus "a semantically vaguely similar passage."

That's also important for a meaningful confidence score.

The open DharmaMitra ecosystem now exposes `mitra-parallel`, ByT5 analyzers, DharmaNexus resources and even an **agentic translation/philology starter project**.

`fojin-cli` is another useful recent project: it repackages **908,620 cross-canon MITRA alignments**, including **231,722 Sanskrit-linked entries**, into a deterministic offline lookup system. It isn't a translator, but the architecture is useful for building evidence retrieval that doesn't depend on an opaque online search.

---

# 14. Candidate generation + reranking is superior to trusting one decode

Instead of S → T, generate S → {T1, T2, ..., T16} using sampling, different prompts/checkpoints, or specialist models.

Then estimate T* = argmax_T E[U(T)] where U is a learned human-aligned utility.

That's the idea behind **Minimum Bayes Risk decoding**.

Recent work has developed efficient MBR libraries and approaches specifically using COMET-family metrics; QE-fusion goes further and synthesizes improved outputs using spans from multiple candidates rather than merely selecting one whole sentence.

This is particularly appealing in Sanskrit because candidate disagreement itself contains information.

If sixteen candidates all independently converge on basically the same semantics: H_semantic ↓

If they split into three radically different interpretations of a compound: H_semantic ↑

That latter passage should be sent to review regardless of whether one candidate happens to get COMET 0.91.

---

# 15. Training frontier: don't stop at supervised fine-tuning

There has been a clear evolution in high-end MT training:

| Work                                                   | Key idea                                                                                          | What to steal                                                     |
| ------------------------------------------------------ | ------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| **Tower**                                              | continued multilingual/domain pretraining → translation instruction tuning                        | Core specialization recipe.                                       |
| **ALMA-R / CPO**                                       | preference optimization rather than blindly imitating references                                  | Use good/bad Sanskrit translation pairs.                          |
| **MT-R1-Zero**                                         | GRPO-style RL with rule + semantic metric rewards                                                 | Interesting later-stage experiment for Sanskrit.                  |
| **Fine-Grained Reward Optimization**                   | xCOMET error severity provides token-level RL reward                                              | Extremely relevant once Sanskrit error spans exist.               |
| **TranslateGemma**                                     | high-quality synthetic + human SFT, then RL using an ensemble of MetricX-QE + AutoMQM rewards     | Probably the cleanest current general blueprint.                  |
| **ReMedy**                                             | learn evaluation as pairwise reward modeling instead of noisy scalar regression                   | Very attractive for Sanskrit evaluator training.                  |

**TranslateGemma is particularly important.**

Google's 2026 recipe is effectively: foundation model → high-quality SFT → multi-reward RL where the rewards include MetricX-QE and AutoMQM rather than optimizing a single automatic score.

That is almost exactly how I would approach Sanskrit eventually.

---

# 16. Don't optimize directly against COMET indefinitely

There is a nasty failure mode called **reward hacking / metric overoptimization**.

Research specifically on using QE as an MT reward found that reward can increase while actual translation quality declines because the generator finds weaknesses in the evaluator.

So never train max_θ COMET(T_θ) forever and assume you're improving Sanskrit.

Instead use a reward mixture such as R = w1·R_SaQE + w2·R_xCOMET + w3·R_MetricX + w4·R_coverage + w5·R_terminology − w6·R_critical

and maintain a **private human-evaluated benchmark none of those reward models can train against**.

Even better, rotate or ensemble evaluators.

This is one place where your philological checks become more than decorative explainability: they make it harder for the generator to game one neural metric.

---

# 17. A potentially better evaluator than COMET: pairwise preference learning

Scalar human scores are noisy.

It is often much easier for a Sanskritist to answer "A or B: which preserves the Sanskrit better?" than "Give translation A a score between 0.00 and 1.00."

**ReMedy** explicitly treats MT evaluation as reward modeling over pairwise human preferences and reports strong results against conventional regression-based metrics.

For your annotation UI I'd therefore collect BOTH T_A > T_B and MQM errors.

That gives you two different training objectives:

**SaReward:** pairwise ranking model.

**SaError:** span-level error detector.

Their agreement becomes another confidence feature.

---

# 18. Your actual model architecture

If I were designing the strongest practical research system today:

```
                         ┌─────────────────────┐
Sanskrit ───────────────►│ Normalization layer │
                         └──────────┬──────────┘
                                    │
                   ┌────────────────┴───────────────┐
                   │                                │
             ByT5-Sanskrit                     Vidyut/SCL
             morphology                         symbolic
                   │                                │
                   └──────────────┬─────────────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │      MITRA-E retrieval     │
                    │ TM / lexica / parallels    │
                    └─────────────┬─────────────┘
                                  │
                    ┌─────────────▼──────────────┐
                    │ Sanskrit specialist LLM     │
                    │ MITRA/Qwen/Gemma derivative │
                    └─────────────┬──────────────┘
                                  │
                      generate 8–32 candidates
                                  │
           ┌──────────────────────▼─────────────────────┐
           │              verifier ensemble              │
           │ xCOMET • MetricX • SaQE • align • morphology│
           │ retrieval support • terminology • disagreement│
           └──────────────────────┬─────────────────────┘
                                  │
                          MBR / QE reranking
                                  │
                            conservative APE
                                  │
                 ┌────────────────▼────────────────┐
                 │ Sanskrit confidence calibrator  │
                 │ + conformal prediction          │
                 └────────────────┬────────────────┘
                                  │
                 translation + error spans + evidence
                        + confidence + provenance
```

The crucial architectural separation is:

**generation ≠ verification ≠ confidence estimation.**

A model should not be allowed to say "I generated this translation and I am 98% confident." That's almost meaningless.

---

# 19. The benchmark I would actually build

I'd call the methodological design something like **SanskritMT-MQM**.

Have three levels:

| Level         | Purpose                                                                         |
| ------------- | ------------------------------------------------------------------------------- |
| **Gold**      | Human Sanskritists, multiple references, complete MQM/error annotation          |
| **Silver**    | Reliable published parallel translations with automated checks                  |
| **Challenge** | Deliberately corrupted near-correct translations targeting linguistic phenomena |

Then report four independent leaderboards:

| Track                    | Main criterion                   |
| ------------------------ | -------------------------------- |
| Translation              | human MQM / preference           |
| Critical-error detection | F1/AUROC for major errors        |
| Quality estimation       | correlation with human judgment  |
| Calibration              | probability/interval reliability |

Your calibration leaderboard matters enormously.

A model that gets 94% translation accuracy but is wildly overconfident when wrong may be substantially less useful for scholarship than one at 92% with extremely good abstention and calibration.

Measure selective prediction: Risk(τ) = P(error | confidence ≥ τ), and plot risk vs coverage.

That lets you state something genuinely useful such as: "At 60% automatic coverage, only 1.2% of translations accepted automatically contain a major semantic error."

That is far more meaningful than saying "COMET = 0.87."

---

# 20. Your "proof score" could be multidimensional

I would deliberately **not collapse everything into one number in the UI**.

For example:

| Signal                   |   Example |
| ------------------------ | --------: |
| Translation quality      |    91/100 |
| P(no major error)        |     96.4% |
| 90% quality interval     |     86–95 |
| Source semantic coverage |       98% |
| Morphological accounting |       97% |
| Technical-term support   |       92% |
| Parallel-text support    |    strong |
| Candidate agreement      |      high |
| Critical errors detected |         0 |
| Review status            | auto-pass |

And let the user expand each claim.

That is a genuine scholarly machine rather than a chatbot with a confidence badge.

---

# 21. One especially interesting research contribution: confidence per Sanskrit span

Instead of only P(T is correct) = .91, produce P(t_i is correctly rendered) for every meaningful source unit.

For a compound such as X-Y-Z you might expose:

```
segmentation             0.98
morphological analysis   0.97
compound relation        0.62
lexical senses           0.84
English realization      0.69
```

Then highlight only the uncertain semantic relation.

xCOMET's error-span approach and 2026 token-level reward work make this direction technically plausible.

For actual philology this is arguably more valuable than another +1.2 BLEU paper.

---

# 22. Sanskrit model training order I would use

| Phase                        | Training                                                        |
| --------------------------- | --------------------------------------------------------------- |
| **0. Baselines**             | MITRA-MT, experimental MITRA-Qwen3.5, generic Gemma/Qwen, APIs  |
| **1. Continued pretraining** | curated Sanskrit + scholarly English + parallel/domain material |
| **2. SFT**                   | Mitrasaṃgraha + carefully weighted auxiliary corpora            |
| **3. Context SFT**           | passages/documents rather than only sentence pairs              |
| **4. Retrieval training**    | Sanskrit↔English + Sanskrit↔Sanskrit contrastive examples       |
| **5. Preference tuning**     | expert A/B translation preferences                              |
| **6. Fine-grained reward**   | Sanskrit MQM/error-span reward                                  |
| **7. RL**                    | cautiously optimize multi-reward objective                      |
| **8. Calibration**           | completely held-out human data                                  |
| **9. Conformal layer**       | independent calibration set                                     |
| **10. Blind benchmark**      | private test material                                           |

Document-level MT deserves special attention. A 2025 method, **Multilingual Contextualization of LLMs for Document-Level MT**, builds translation specialization with high-quality contextual document blocks rather than relying purely on sentence-wise translation. More recent 2026 work continues exploring structured context selection for document MT.

For philosophical Sanskrit, context is plainly critical because technical terms and implicit arguments can depend on sentences many lines away.

---

# 23. Papers I would read first

This is the one ordered reading queue I think gives you almost the entire architecture:

1. **Mitrasaṃgraha: A Comprehensive Classical Sanskrit Machine Translation Dataset — arXiv:2601.07314.** Your immediate Sanskrit baseline, data, evaluation and RAG paper.
2. **MITRA — arXiv:2601.06400.** Sanskrit domain pretraining + multilingual parallels + semantic retrieval.
3. **PaliBench — arXiv:2605.16881.** Best direct blueprint I found for a serious multi-reference classical-language benchmark.
4. **One Model Is All You Need: ByT5-Sanskrit — arXiv:2409.13920.** Your linguistic sidecar.
5. **xCOMET: Transparent MT Evaluation through Fine-grained Error Detection.** Foundation for the verifier/error-span layer.
6. **MetricX-25 and GemSpanEval — arXiv:2510.24707.** Current learned quality + span-error architecture.
7. **Early-Exit and Instant Confidence Translation Quality Estimation — EACL 2026.** Directly relevant to trustworthy confidence.
8. **Conformalizing Machine Translation Evaluation — TACL 2024.** The statistical foundation for defensible confidence intervals.
9. **ReMedy — arXiv:2504.13630.** Pairwise preference reward model as evaluator.
10. **TranslateGemma — arXiv:2601.09012.** Probably the cleanest modern general-purpose MT post-training blueprint.
11. **Tower — arXiv:2402.17733.** Continued pretraining → translation specialization recipe; MITRA itself follows this lineage.
12. **Contrastive Preference Optimization / ALMA-R — arXiv:2401.08417.** Preference tuning specialized for MT.
13. **MT-R1-Zero — arXiv:2504.10160.** GRPO/R1-style MT training and mixed rewards.
14. **Fine-Grained Reward Optimization for MT — arXiv:2411.05986.** Train from xCOMET error spans rather than sparse sentence rewards.
15. **Improving MT with Human Feedback: QE as Reward Model — arXiv:2401.12873.** Read specifically for the warning about evaluator reward hacking.
16. **QE-Fusion.** Candidate-span synthesis based on quality estimation.
17. **MBRS.** Open MBR decoding framework useful for actually implementing candidate selection experiments.
18. **GEMBA-MQM.** LLM-based reference-free error-span evaluation; especially relevant because Mitrasaṃgraha found GEMBA strong on Sanskrit expert judgments.
19. **Sāmayik — arXiv:2305.14004.** Contemporary Sanskrit-English dataset and baselines.
20. **Itihāsa — arXiv:2106.03269.** Older but still useful for an independent epic-domain evaluation/training slice.

---

# 24. The opportunity I think is actually frontier

I would **not** frame the project merely as "best Sanskrit translation model."

That's increasingly a parameter/data race with DharmaMitra and large labs.

The more defensible research objective is:

> **The first calibrated, proof-carrying Sanskrit machine translation system.**

The moat becomes: translation + philological evidence + fine-grained error detection + multi-reference benchmarking + uncertainty calibration + abstention.

DharmaMitra is already attacking Sanskrit translation and retrieval extremely seriously.

What still looks comparatively open is **proving when the machine should be trusted**.

A publishable sequence could therefore be:

**Paper A — SanskritMT-MQM:** expert benchmark + multi-reference + Sanskrit error taxonomy.

**Paper B — SaQE:** Sanskrit-specialized quality estimator/error detector trained on A.

**Paper C — Calibrated Sanskrit MT:** conditional conformal prediction + selective translation/abstention.

**Paper D — Proof-Carrying Sanskrit Translation:** lexical, morphological, alignment, parallel-text and calibrated neural evidence combined into an auditable translation artifact.

Then improve the generator.

The evaluation infrastructure becomes useful **regardless of which foundation model wins six months from now**.

---

## What I would build first

If I were beginning implementation immediately, I'd actually **delay expensive model training**.

First reproduce the Mitrasaṃgraha test suite. Run **MITRA-MT, the new MITRA-Qwen3.5 checkpoints, a strong generic current model, and several API models** over the identical passages. Store every candidate.

Then run **xCOMET, MetricX-25/GemSpanEval, GEMBA-MQM, morphology/alignment checks and candidate disagreement** over those outputs.

Then manually annotate only a strategically sampled **500–1,000 passages**, heavily oversampling evaluator disagreement.

With that single dataset you can already answer an extremely valuable unknown:

**Which automatic signals actually predict Sanskrit translation errors?**

Then train the calibration/meta-evaluator.

Only **after** you have that instrument should you use CPO/GRPO/RL to optimize the Sanskrit translator. Otherwise you're essentially modifying a machine without a trustworthy measuring instrument.

That is the direction I'd pursue. It gives you a benchmark, evaluator, confidence framework and eventually a better model—and the first three remain valuable even as foundation models rapidly improve.

This area is moving quickly in 2026. I can track new Sanskrit MT datasets, DharmaMitra/MITRA releases, COMET/QE research and relevant arXiv papers for you as they appear.
