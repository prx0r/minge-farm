# SCIENCE-LAB VISION — the goal that drives every hypothesis + experiment

*2026-08-16 · the VISION STATEMENT for the translation science lab. Every hypothesis generation and every
experiment works toward ONE falsifiable claim. This is the north star — nothing is built without asking
"does this serve the vision?"*

## THE VISION (the one falsifiable claim)

> **Our Sanskrit translation benchmark — per-tradition × quality × proof × cost — is SCIENTIFICALLY
> BETTER than the existing Sanskrit benchmarks (Sāmayik, Itihāsa, IndicParam), and we can PROVE it.**

"Better" is not a hope — it is a **measurable, falsifiable claim**: our metric(s) rank translations
**more like a human judge** than BLEU/chrF do. That is the WMT-standard definition of a good metric, and
it is how COMET/XCOMET proved themselves better than BLEU.

## THE PROOF PROTOCOL (how we demonstrate "better")

```
1. Take N gold Sanskrit verses (Mitrasamgraha test).
2. Produce M diverse candidate translations per verse (different configs → different quality).
3. The LLM-judge scores each candidate's semantic quality (the "human" signal).
4. For each automatic metric (chrF, bleu1, semantic, combined, proof-gate):
     rank candidates by that metric, rank them by the judge, compute KENDALL'S TAU.
5. Higher tau = the metric correlates with human judgment better.
   If our combined/quality metric beats raw chrF → the benchmark is proven better.
```

**The deliverable:** a measured Kendall's-tau table showing our metric > chrF/bleu, on real gold, with
full lineage. That number is the PROOF.

## HOW EVERYTHING SERVES THE VISION

| Piece | Role in the vision |
|---|---|
| `sanskrit_gold.py` | the fixed control (per-tradition) the proof runs on — same data, comparable |
| `experiment_lab.py` | runs the experiments that feed the tau computation |
| `translation_proof.py` | the verifiable PASS/BLOCK gate (a candidate axis to test) |
| `validate_benchmark.py` | **THE proof: Kendall's tau of each metric vs the judge** |
| `hypothesis_lab.py` | generates the next hypothesis from what the tau/proof reveals |
| `tools/sanskrit_benchmark.py` | the leaderboard view (per-tradition × quality × proof × cost) |

## THE CLOSED LOOP (autonomous, open-ended)

```
validate (measure tau of each metric)
   → observe which metric is weakest / which error family hurts
   → hypothesis_lab generates the next metric/config hypothesis
   → run it as a new experiment
   → re-validate → did tau improve? → keep or discard → repeat
```

Every loop either improves the benchmark (higher tau = provably better) or is discarded. The registry is
the evidence ledger: **if it isn't in the registry, it isn't decided.**

## THE RULE

> No claim of "better" is made without a logged Kendall's-tau on the same fixed gold. The vision is
> proven by a number, not by assertion.
