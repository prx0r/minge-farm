# MITRASAMGRAHA — the Sanskrit→English translation gold + eval harness

*2026-08-16 · the post-corrected Sanskrit–English translation gold, staged on R2 + wired to an eval
harness with full result lineage. This is the ONE-RULE calibration set for the translation gate: it
makes "our L2 translation is good" verifiable instead of assumed.*

---

## 1. WHAT IT IS

**Mitrasamgraha** (arXiv 2601.07314) is the most important Sanskrit→English translation dataset:

- **391,548 Sanskrit–English bitext pairs** spanning 3,000+ years and multiple genres
- **5,552 post-corrected TEST pairs** + **5,587 post-corrected VAL pairs** (human-reviewed gold)
- Designed to expose **translation error families** the paper documents:
  `compound semantic loss · scope loss · case-role inversion · negation loss · implicit-subject error ·
  technical-term substitution · metaphor literalisation · unlicensed explicitation`

These error families map directly to our **L200 audit** + `translation_proof` checks.

## 2. WHERE IT LIVES

| Location | What |
|---|---|
| **HuggingFace** | `buddhist-nlp/mitrasamgraha-released-data-only` (parquet: test/val/train) |
| **R2** | `source/ingestion/MITRASAMGRAHA/snapshots/mitrasamgraha-2026-08-16/` (test.jsonl + val.jsonl + manifest) |
| **Local** | `data/benchmarks/mitrasamgraha/{test,val}.jsonl` |

Format (jsonl): `{"sanskrit": "…", "english": "…"}` — real IAST Sanskrit + human gold English.

## 3. THE EVAL HARNESS

`tools/eval_mitrasamgraha.py` — samples test pairs, calls the model to translate, scores vs gold:

```bash
python3 tools/eval_mitrasamgraha.py --n 20 --model deepseek-v4-flash                # chrF + bleu
python3 tools/eval_mitrasamgraha.py --n 20 --model deepseek-v4-flash --judge-model deepseek-v4-flash  # + LLM semantic judge
python3 tools/eval_mitrasamgraha.py --n 3 --dry-run                                   # print sample only
```

**Metrics:** `chrF` (char-n-gram F1) + `bleu1` (token overlap w/ brevity penalty) + **`semantic_fidelity`
(1-5, LLM-as-judge)** — the semantic score matters because chrF/bleu understate good Sanskrit
translations (correct wording ≠ gold wording).

**Result lineage** (AGENTS.md §9): every row logs `result_id · gold_version · model_version · split ·
seed · config · date`, appended to `data/corpus/mitrasamgraha-eval-log.jsonl`.

**Error-family analysis:** `tools/analyze_mitra_errors.py` reads the log and surfaces low-chrF / low-
fidelity rows side-by-side (SANSK/GOLD/MODEL) for manual error-family classification.

## 4. FIRST MEASURED RESULTS (deepseek-v4-flash)

| n | avg chrF | avg bleu1 | semantic |
|---|---|---|---|
| 4 | 0.539 | 0.368 | — |
| 2 | 0.548 | 0.316 | — |
| 10 | 0.549 | ~0.35 | (pending) |

**Key finding:** the model output is *semantically strong* (meaning preserved) but *wording-different*
from gold → chrF 0.54 understates true quality. This confirms the project docs' "BLEU + chrF +
LLM-as-judge" requirement. The semantic judge is the honest quality number — and it produces **specific,
actionable error reports** (e.g. "Misreads the core clause: gold's imperative 'take the best…'" → 2/5;
"Core meaning preserved" → 4/5). Those judgments are the error families to wire into L200.

## 5. HOW IT'S USED (the translation gate calibration)

Mitrasamgraha makes the **translation gate real** (ONE-RULE):
- Run our **L2 / translation_proof** against the post-corrected test pairs
- Does the gate catch the documented error families (case-role inversion, negation loss, …)?
- Those become **deterministic L200/translation_gate validators** — not vague quality claims

## 6. WHAT'S BUILT + WHAT'S NEXT

**Built:** gold staged (R2 + local), eval harness (chrF/bleu/semantic-judge + lineage), error analyzer.

**Next:** bigger honest samples (n=50+), cross-model comparison, wire into translation_gate as the
calibration set, derive the error-family validators for L200.
