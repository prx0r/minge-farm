# SANSKRIT BENCHMARK — the COMET + school/time-period VISION (state + plan)

*2026-08-16 · The next evolution of the Sanskrit benchmark: build OUR OWN learned metric (COMET-style)
+ ML methods that beat the existing benchmarks (Sāmayik/Itihāsa/IndicParam all use BLEU/chrF), and make
it **school-aware** (tantric schools: Pratyabhijñā, Śaiva Siddhānta, Krama, …) and **time-period-adjusted**
(old Hindu / Vedic vs classical vs tantric), so the metric recognizes when a term like *vimarśa* means
different things in different schools/periods. This doc records the verified research landscape and the
honest, incremental path to a real, non-bullshit benchmark.*

---

## 1. THE HONEST CURRENT STATE (what the lab has now)

**What's real + working:**
- `sanskrit_gold.py` — 5,601 fixed gold exemplars, tagged by tradition:
  - **Pratyabhijñā/Trika: 373** · **Krama: 123** · **Śaiva Siddhānta: 278** · **Vedic/General: 4,827**
- The 49 real IPVV scholarly passages (source Sanskrit + `l2_text` gold) — the richest scholarly gold.
- Mitrasamgraha test (5,552) + val — the post-corrected translation gold.
- 23 kramasadbhava gold_records (deterministic, Śaiva).
- The experiment lab (3 logged), proof gate, Kendall's-tau validation v2, benchmark leaderboard, cost router.

**The honest limitation (why BLEU/chrF understate good Sanskrit):**
- BLEU/chrF are **lexical n-gram overlap** — they punish synonymous-but-valid rephrasing and reward
  reference-copying; they fail on Sanskrit's morphology-rich, free-word-order, polysemous-scholarly text.
- Measured already: Mitrasamgraha avg **chrF ~0.55 but semantic-fidelity ~0.8–0.9** — the surface metrics
  systematically understate good translation.
- **Tradition tagging today is keyword-heuristic** (`_TRADITION_HINTS`) — best-effort, not verified.

---

## 2. THE VERIFIED RESEARCH LANDSCAPE (what exists — from live arXiv/GitHub fetches)

### 2.1 Learned MT metrics (the thing we want to adopt)
| Metric | What it is | Sanskrit? | Runnable? |
|---|---|---|---|
| **COMET** (Unbabel) | neural regression: encoder `[src, hyp, ref]` → quality score, supervised on human DA/MQM labels | XLM-R covers Sanskrit **nominally but unreliably** (little training data); **no Sanskrit DA/MQM set exists** | ✅ `pip install unbabel-comet`, `wmt22-comet-da`, ref-free `cometkiwi`; repo cloned at `source-evidence/repos/Unbabel__COMET` (v2.2.7) |
| **XCOMET** | COMET + MQM error spans; highest human-correlation | same as COMET | ⚠️ needs 3.5B/10.7B (not on this 8GB box) |
| **MetricX** (Google) | mT5-based regression onto MQM, hybrid ref+QE | mT5 nominally covers Sanskrit | ✅ `google-research/metricx` (needs big model) |
| **afriCOMET** | COMET for African low-resource languages | — | ✅ **the template for a low-resource COMET** |
| BLEURT / BARTScore / UniTE | other learned metrics | weak | ✅ |
| **LLM-as-judge** | reference-grounded, school-instructed | **bad for creative/śāstric text if naive** (Creativity Bias 2605.13596; worst on poetry) | ✅ |

### 2.2 Existing Sanskrit benchmarks (all use BLEU/chrF — none use learned/diachronic metrics)
| Name | arXiv | What | Metric |
|---|---|---|---|
| Itihāsa | 2106.03269 | 93K ślokas (Rāmāyaṇa/Mahābhārata) | BLEU |
| Sāmayik | 2305.14004 | ~53K contemporary prose | BLEU/chrF |
| Samasāmayik | 2603.24307 | 92K Hindi–Sa | BLEU |
| **Mitrasamgraha** | 2601.07314 | **391K Sa–En, spans 3+ millennia, temporal + domain annotated** | BLEU/chrF (drift analysis, no learned metric) |
| MITRA | 2601.06400 | 1.74M Sa/Pāli/Buddhist-Ch/Tib | open weights + semantic benchmark |
| IndicParam | 2512.00333 | 13K MCQ LLM leaderboard incl. Sanskrit | accuracy |

### 2.3 Diachronic / tradition-aware NLP (the gap)
- **Diachronic word embeddings** (Hamilton 1605.09096; Kutuzov survey 1806.03537) — for modern languages, **none for Sanskrit, none conditioning an MT metric on period**.
- **School/tradition-aware Sanskrit** — **zero published work**; no school-classification dataset exists.
- **Time-period-adjusted evaluation** — **nothing exists**; Mitrasamgraha annotates period+domain but only *reports* drift with off-the-shelf metrics.

---

## 3. THE GAP (what nobody does — our opportunity)

**No one trains a COMET-style learned metric on Sanskrit DA/MQM labels. No Sanskrit human-judgment dataset
exists. Nothing conditions an MT metric on philosophical school or historical period.** That intersection
is open space. Our vision fills it by being:

1. **A Sanskrit DA/MQM expert-judgment set** (the prerequisite — without human labels, no COMET can be
   trained or validated for Sanskrit; "beats BLEU/chrF" is then shown by *meta-evaluation* = correlation
   with experts, the honest WMT standard).
2. **A school- and period-conditioned learned metric** — fine-tune COMET with a conditioning token/embedding
   for school + period, or a learned "doctrine/register" head. Genuinely novel.
3. **School- and time-period-aware benchmark splits as first-class axes** — Mitrasamgraha annotates but
   doesn't make it the evaluation axis; we would (so the metric recognizes *vimarśa* differs by school/period).
4. **A reference-grounded, school-instructed LLM judge** calibrated for Sanskrit śāstra (naive LLM judges
   penalize creative/culturally-appropriate translations — worst on poetry; a school-instructed, ref-grounded
   judge is the fix).

---

## 4. THE CONCRETE BUILD PATH (incremental, honest, fits the 8GB/4-core box)

### Phase A — the DA/MQM gold (the prerequisite, hardest, most valuable)
- Build a **Sanskrit human-quality-judgment set**: sample N pairs from Mitrasamgraha (period/domain-
  annotated) + the 49 IPVV scholarly passages; have experts (or a school-instructed judge distilled to
  expert calibration) rate each candidate on DA (0–100) + MQM error spans. **Without this, no real COMET.**
- Store as `data/da-mqm/gold.jsonl` with full lineage (judge, version, school, period).

### Phase B — evaluate existing learned metrics on OUR gold (the honest baseline)
- Run off-the-shelf **COMET (`wmt22-comet-da`)** + ref-free `cometkiwi` on the same Mitrasamgraha/IPVV
  gold the lab already has; compute **Kendall's tau / Spearman vs the DA/MQM gold** (the WMT meta-eval).
- Compare against our semantic-judge + chrF/bleu. **This alone proves whether "COMET > BLEU/chrF" holds
  for Sanskrit** — the first falsifiable number, before we train anything.

### Phase C — the school + period conditioning (the novel part)
- Add school/period as **conditioning input** to the metric: either a prepended token (e.g. `[Pratyabhijñā]`,
  `[classical]`) or a learned "doctrine head".
- **Test the key hypothesis directly:** *does the metric rank translations better when it knows the school/
  period?* (tau with school-conditioning vs without). If *vimarśa* in Pratyabhijñā vs Śaiva Siddhānta is
  translated differently, a school-aware metric should rank the school-appropriate candidate higher.
- Sanskrit-backbone option: ByT5-Sanskrit (2409.13920) / Gemma2-MITRA (2601.06400) may beat XLM-R as the
  COMET encoder for Sanskrit — worth testing, not assuming.

### Phase D — the school/time-period leaderboard
- Make the leaderboard **per-school × per-period** (Pratyabhijñā / Śaiva Siddhānta / Krama / Vedic / …),
  not just a single "Sanskrit" number. Each model gets a per-school, per-period quality+proof+cost score.
- The `vimarśa` test: a fixed set of polysemous-scholarly-term items where the correct rendering depends on
  school/period — the benchmark's sharpest discriminator.

---

## 5. THE HONEST RISKS (the anti-theatre guard)

1. **No Sanskrit DA/MQM labels exist** → you cannot *supervise-train* a real COMET without first building
   expert-judgment data (costly, needs śāstric expertise). **Do not claim "we trained a COMET" until Phase A
   is real.**
2. **XLM-R/mT5 "cover" Sanskrit but are weak there** → `wmt22-comet-da` may be unreliable for Sanskrit;
   test a Sanskrit-first backbone (ByT5-Sanskrit/Gemma2-MITRA) rather than assuming.
3. **"Diachronic" in Sanskrit is contested** — classical Sanskrit is idealized/timeless; period labels need
   philological grounding (Vedic vs Epic vs Classical vs Tantric), not just source metadata.
4. **Compute** — this is an 8GB/4-core box; XCOMET (10.7B) is not feasible here. Use `wmt22-comet-da`
   (XLM-R base, ~278M) on CPU, or run big models on the other box/GPU. **Stream, never bulk-load.**
5. **The vision is proven by a number, not by assertion** — a real COMET/Sanskrit metric "beats BLEU/chrF"
   only when its Kendall/Spearman vs expert DA/MQM gold is higher, measured on the same fixed gold, logged
   in the registry. Same anti-theatre rule as the rest of the lab.

---

## 6. THE IMMEDIATE NEXT STEP (what to actually do now)

1. **Phase B first** — it needs no new human data: install `unbabel-comet`, run `wmt22-comet-da` +
   `cometkiwi` on the existing Mitrasamgraha/IPVV gold, compute tau vs our current semantic-judge. This
   gives the first honest, falsifiable number: **does off-the-shelf COMET actually beat chrF/bleu on
   Sanskrit, on our own gold?**
2. **Verify the school/period conditioning hypothesis** on the gold we have (even with the keyword tags) —
   a quick probe of whether school-tagged subsets score differently.
3. Then, only if Phase B justifies it, begin **Phase A (the DA/MQM gold)** — the real long-term asset.

---

*The benchmark is real and works. The next evolution — a COMET-style learned metric that is school- and
time-period-aware — is open space nobody occupies, but it is only "real" when it has (a) a Sanskrit DA/MQM
gold, (b) a measured correlation with experts that beats chrF/bleu, and (c) a logged number in the registry.
Build Phase B → C → A in that order; never present Phase A as done before the gold exists.*
