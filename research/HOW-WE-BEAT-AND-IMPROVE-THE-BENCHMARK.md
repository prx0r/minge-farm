# HOW WE PROVABLY BEAT + IMPROVING THE BENCHMARK (the core answer)

*2026-08-16 · Direct answer to: "how can we provably beat the existing benchmarks? what is the benchmark?
can the benchmark itself be improved?" — grounded in the frontier labs' actual code (Sāmayik, Itihāsa,
IndicTrans2) and the WMT meta-eval standard.*

---

## 1. WHAT "PROVABLY BEAT" MEANS (the WMT-standard proof)

Frontier labs don't "beat" by having a better translator — they beat by having a better **metric**, proven
via **meta-evaluation**. The protocol (what `google-research/mt-metrics-eval` is for):

```
1. N test sentences with human quality scores (DA / MQM gold)
2. Compute each automatic metric's score per segment:
     BLEU · chrF · COMET · our semantic-judge · (later) our school/period-conditioned metric
3. Compute Kendall's tau / Spearman between each metric's ranking and the HUMAN GOLD ranking
4. The metric with the higher tau "beats" BLEU/chrF  ← that is how COMET beat BLEU
```

**So "provably beat" = our metric's tau vs human gold > chrF's tau vs human gold, on the same fixed test
set, logged.** That is the falsifiable claim in `VISION.md`. It is a real, reproducible number.

## 2. WHAT THE FRONTIER ACTUALLY DOES (verified from their code)

| Lab | Dataset | Model | Metrics | Learned? | School/period? |
|---|---|---|---|---|---|
| **Sāmayik** (LREC-COLING 2024) | 2,417 test En→Sa | NLLB-200-1.3B (`san_Deva`) | **BLEU + chrF** only | ❌ | ❌ |
| **Itihāsa** | 11,721 test śloka | (MT baselines) | BLEU | ❌ | ❌ |
| **IndicTrans2** (AI4Bharat) | 22 Indic langs incl. Sa | IndicTrans2 | **COMET** + BLEU/chrF + significance | ✅ | ❌ |

**The gap:** none condition on school/period, none use a Sanskrit-specific learned metric, none *prove their
metric beats chrF on their own gold*. **That's our opening.**

## 3. THE BENCHMARK ITSELF IS IMPROVABLE — YES, THIS IS THE WHOLE POINT

The benchmark is not fixed; it is the thing we improve. Five axes:

| Axis | Now | Improved | How it raises tau vs human |
|---|---|---|---|
| **Metric** | chrF/bleu (surface) | COMET (learned) → school/period-conditioned (novel) | learned metrics correlate better with humans |
| **Gold** | Mitrasamgraha 5,552 + IPVV 49 | **+ Sanskrit DA/MQM human-judgment set** (Phase A) | higher-quality gold = more trustworthy proof |
| **Splits** | one "Sanskrit" number | **per-school × per-period** (the *vimarśa* test) | finer, more honest |
| **Data** | Mitrasamgraha + IPVV | **+ Sāmayik, Itihāsa, MITRA** (imported) | more coverage = stronger external validation |
| **Proof** | lexical metrics | metric tau + **cryptographic commitment** (integrity) | adds provable integrity |

**The meta-eval loop (the improvement mechanism):** run tau → see which metric/error-family is weakest →
hypothesis_lab proposes a better metric/config → run → re-validate → keep if tau improved. The benchmark
*scores itself upward* toward higher human correlation.

## 4. THE IMPORTED FRONTIER DATASETS (already in the project)

Imported into `data/frontier/` (from the cloned repos):
- **Sāmayik** — `data/frontier/saamayik/{test.en,test.sa}` — 2,417 En→Sa contemporary-prose pairs.
- **Itihāsa** — `data/frontier/itihasa/{test.en,test.sn}` — 11,721 En→Sa classical-śloka pairs.

Loader: `pipeline/frontier_gold.py` (registers as `frontier:saamayik`, `frontier:itihasa` test sources, so
the lab + validation can run `--test frontier:saamayik`). **External gold = an honest cross-check**: if our
metric beats chrF on *their* data too, not just our own, the proof is far stronger.

## 5. THE CONCRETE STEPS (in order)

1. **Run the meta-eval on our OWN gold now** (mitrasamgraha) — the first real tau (chrF vs bleu vs our
   semantic-judge), using hermes. Baseline number.
2. **Run the same meta-eval on the imported Sāmayik + Itihāsa gold** — does our metric beat chrF there too?
   (External validation.)
3. **Add COMET** (Phase B, needs torch) — compare its tau vs ours.
4. **Add school/period conditioning** (Phase C) — the *vimarśa* test.
5. **Build the Sanskrit DA/MQM gold** (Phase A) — the highest-value long-term asset.

**The honest rule:** the benchmark is proven better only by a logged tau vs human gold on the same fixed
data, resolved to a reproducible experiment. If it isn't a logged number, it isn't real.

---

*The frontier gave us the data and the standard (Sāmayik/Itihāsa + MTME tau). We bring the learned,
school/period-conditioned metric + the crypto proof — the part nobody has done for Sanskrit. The benchmark
improves itself via the meta-eval loop until our metric correlates with human judgment better than chrF.*
