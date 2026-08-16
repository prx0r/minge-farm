# LEGITIMATE SANSKRIT BENCHMARK — design + the 15-step recipe applied

*2026-08-16 · How we make the progressive-difficulty Sanskrit→English benchmark genuinely legitimate (not
theater), per the verified WMT/FLORES/MTME/XTREME-R methodology. This doc applies the research recipe to
sanskritbenchy and records exactly what's built and what still needs human/private resources.*

---

## 1. THE OPPORTUNITY (the open gap, verified)

**No existing Sanskrit benchmark is legitimate by the field's standard.** Verified weaknesses of all
current ones (Itihāsa, Sāmayik, Mitrasamgraha, MITRA):
1. **Single reference** → BLEU-inflated/deflated, translationese bias.
2. **No expert MQM human gold** → no metric validation, no honest "harder" claim.
3. **No private, versioned, time-stamped holdout** → contamination risk unmanaged.
4. **No period/register/genre conditioning as a MEASURED axis.**
5. **BLEU-only / no significance** → no confidence intervals or significance clusters.

That's exactly what we build. The "progressive-difficulty by school/period/term-density" axis is open space.

## 2. WHAT'S BUILT (the legitimate infrastructure)

| Piece | File | What it does |
|---|---|---|
| **Difficulty-tagged source** | `pipeline/sanskrit_texts.py` | 254 DCS/GRETIL texts tagged by school (7) + tier (1-4) + period; computes specialist-term density per school |
| **The legitimate registry** | `pipeline/benchmark_registry.py` | content-addressed, versioned test set; source lineage + license; decontamination audit; result-lineage requirements |
| **The runner** | `pipeline/benchmark_runner.py` | dealradar picks the best model per tier → hermes translates → Pāṭala proof gate → content-addressed result |
| **Run recorder** | `pipeline/run_recorder.py` | content-addressed runs + nanopublication triples (assertion + evidence + provenance) |
| **Golden audit** | `agent/audit.py` | recompute on fixed gold; fail on mismatch (the executable ONE RULE) |

**Verified working:** 21 content-addressed passages across 7 schools × tiers 3-4, with lineage + a
decontamination audit; a real Pratyabhijñā passage was translated and the proof gate correctly BLOCKED it
(caught a source-repeat/abstention issue) — the benchmark catches real translation problems.

## 3. THE 15-STEP RECIPE — applied to sanskritbenchy (status per step)

### Phase A — Design
1. **Fix difficulty axes, linguistically.** ✅ TIERS: T1 simple prose → T4 Tantric/Pratyabhijñā scholastic,
   defined by period + school + term-density (a principled axis, not length). Extend to sandhi/compounding
   depth + metaphor/metre later (the Isabelle-challenge-set philosophy).
2. **Write translation + review guidelines** (MQM protocol: document context, max-5-errors, error
   categories, weights major5/minor1). ⬜ needs a human reviewer + the wmt-mqm format.

### Phase B — Test-set construction
3. **Curate fresh, timestamped, public-domain sources.** ✅ DCS/GRETIL (CC-BY), tagged tier/period/school/
   source-date. Add Itihāsa (Apache), Sāmayik, MITRA parallel.
4. **≥2 independent, linguistically-diverse human references.** ⬜ needs human translators — the hard,
   high-value asset. Ship as `refA`/`refB`.
5. **Private, versioned, content-addressed holdout.** ✅ content-addressing + manifest hash done. ⬜
   private-heldout (disjoint source documents, git-tagged, kept private until lock).

### Phase C — Decontamination
6. **Prevent** via private-heldout + source-date > model-cutoff. ✅ documented as the method (the only
   reliable defense). ⬜ enforce with a script.
7. **Detect & disclose** — n-gram + embedding screens; publish overlap per tier. ⬜ (honest flag:
   detection is unreliable for LLMs; prevention carries the weight).
8. **Cross-check CONDA contamination DB + register.** ⬜.

### Phase D — Human gold & metric validation
9. **Expert MQM gold** (professional translators, full-context, multi-rater + IAA). ⬜ needs human
   annotators — the long-term asset.
10. **Meta-evaluate every metric via MTME** (system/doc/seg granularities, tie-calibrated pairwise
    accuracy, significance). ⬜ adopt MTME `Correlation`/`Acc23`; ⚠️ do not trust COMET on Sanskrit until
    it passes meta-eval on our gold.
11. **Prove tiers are genuinely harder** — monotonicly lower human MQM + metric correlation as tier rises.
    ⬜ needs step 9.

### Phase E — Baselines, scoring, provenance, publication
12. **Fixed baseline battery** (NLLB, ByT5-Sanskrit, IndicTrans, an LLM) with seeded deterministic
    decoding. ⬜ (dealradar can recommend which — the bridge exists).
13. **Score with SacreBLEU + chrF + validated COMET**, per ref + per tier + significance clusters. ⬜
    (SacreBLEU/pinned tokenizer to add).
14. **Ship the eval harness + result manifest** (versioned data, pinned scorer, MANIFEST per number,
    public leaderboard). ✅ run_recorder + registry scaffold; ⬜ leaderboard.
15. **Publish decontamination + limitations.** ✅ documented; ⬜ paper.

## 4. HOW DEALRADAR FITS (the model-selection layer)

dealradar recommends the best model **per difficulty-tier task** (T3/T4 → reasoning-heavy; T1 → cheap/fast),
which the runner uses to pick WHICH model to test on each Sanskrit passage. We record both the dealradar
recommendation AND the hermes-executed model in the lineage (honest — the recommendation is tracked even
when the actual call uses deepseek-v4-flash).

## 5. THE HONEST GAPS (what needs humans/private resources — not code)

1. **The ≥2 independent human references** (step 4) — the hardest, highest-value asset.
2. **The expert MQM gold** (step 9) — needed to validate the metric + prove tiers are "harder."
3. **Private heldout** (step 5) — needs discipline to keep the test set private until lock.
4. **Enforce the decontamination prevention** (step 6) — a script checking source-date vs model cutoff.

**What code CAN do now:** build the registry (done), run the benchmark + proof gate (done), meta-evaluate
against whatever gold we can assemble, and wire dealradar's model selection. The paper-ready legitimacy
(wmulti-ref + MQM gold + private holdout) is the human-in-the-loop asset.

---

## 6. THE ONE RULE (unchanged, now executable)

> **A headline number is real only when it is a logged, machine-computed value in a content-addressed run
> record, on a fixed, versioned, lineage-carrying test set, with a significance-aware comparison. If it
> isn't in the registry, it isn't decided.**
