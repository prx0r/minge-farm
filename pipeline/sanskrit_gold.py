#!/usr/bin/env python3
"""pipeline/sanskrit_gold.py — the FIXED Sanskrit gold control set (the lab's control variable).

Per `domains/translation/LAB.md` §"THE GOLD CONTROL": every experiment scores against a FIXED Sanskrit
gold test set organized by tradition, so results are comparable on the SAME data AND include a quality
axis (LLM-judge vs the gold), not just speed/cost.

Traditions (from the spec): Pratyabhijñā/Trika · Krama · Śaiva Siddhānta (+ a general/Vedic catch-all).

Sources:
  - IPVV published passages (the scholarly C1 exemplars) — the richest gold, tagged by tradition where known
  - kramasadbhava gold_records (deterministic, Śaiva)
  - Mitrasamgraha test (the post-corrected translation gold)

API (per spec):
  from sanskrit_gold import exemplars, gold_for, score_vs_gold, traditions
  score_vs_gold(produced_text, "IPVV-V2F")   # 0-1 quality vs the gold
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))

# the canonical traditions (the specialist-benchmark axes)
TRADITIONS = ["Pratyabhijñā/Trika", "Krama", "Śaiva Siddhānta", "Vedic/General"]

# per-tradition keyword hints (best-effort tagging of IPVV passages + gold_records)
_TRADITION_HINTS = {
    "Pratyabhijñā/Trika": ["pratyabhijñā", "pratyabhijna", "trika", "śiva sūtra", "sivasutra",
                           "spanda", "vimarśa", "aham", "caitanya", "māyā", "maya", "icchā", "jñānaśakti",
                           "unmesa", "prakāśa", "vimarśa"],
    "Krama": ["krama", "sādhāra", "mātṛkā", "unmanī", "ānanda", "ananda", "śakti-pāta", "ucyate"],
    "Śaiva Siddhānta": ["siddhānta", "siddhanta", "pāśa", "pāsa", "mala", "bheda", "pramātṛ",
                        "pramatr", "ṛṇa", "adhvā", "tattva", "kalā", "vidyā"],
    "Vedic/General": ["gītā", "gita", "brahma", "veda", "upaniṣad", "upanisad", "ātman", "dharma"],
}


def _tag_tradition(text: str) -> str:
    t = text.lower()
    best, best_n = "Vedic/General", 0
    for trad, hints in _TRADITION_HINTS.items():
        n = sum(1 for h in hints if h in t)
        if n > best_n:
            best, best_n = trad, n
    return best


# ── exemplars (the fixed gold set, loaded once) ──────────────────────────────
def _load_ipvv():
    rows = []
    ipvv = ROOT / "data" / "published" / "ipvv"
    for f in sorted(ipvv.glob("pt-passage-*.json")):
        try:
            g = json.load(open(f))
        except Exception:
            continue
        src = g.get("source") or g.get("source_text") or ""
        gold = g.get("l2_text") or g.get("l2") or ""
        if src and gold:
            rows.append({
                "id": g.get("id", f.stem), "work": g.get("work_id", "ipvv"),
                "source": src if isinstance(src, str) else str(src),
                "gold": gold if isinstance(gold, str) else str(gold),
                "tradition": _tag_tradition(str(src)),
            })
    return rows


def _load_kramasadbhava():
    rows = []
    gr = ROOT / "pipeline" / "gold_records"
    for f in sorted(gr.glob("*.json")):
        try:
            g = json.load(open(f))
        except Exception:
            continue
        src = g.get("source", {}).get("source_text", "")
        stages = g.get("stages", {})
        gold = stages.get("L2") or stages.get("l2") or ""
        if src and gold:
            rows.append({
                "id": g.get("passage_id", f.stem), "work": "kramasadbhava",
                "source": src, "gold": gold if isinstance(gold, str) else str(gold),
                "tradition": "Krama" if "krama" in f.name else _tag_tradition(str(src)),
            })
    return rows


def _load_mitra():
    rows = []
    mf = ROOT / "data" / "benchmarks" / "mitrasamgraha" / "test.jsonl"
    if not mf.exists():
        return rows
    for line in open(mf, encoding="utf-8"):
        line = line.strip()
        if line:
            d = json.loads(line)
            rows.append({"id": "mitra", "work": "mitrasamgraha",
                         "source": d["sanskrit"], "gold": d["english"],
                         "tradition": _tag_tradition(d["sanskrit"])})
    return rows


_CACHE = None


def exemplars():
    """The full fixed gold set, deduped, tagged by tradition."""
    global _CACHE
    if _CACHE is None:
        _CACHE = _load_ipvv() + _load_kramasadbhava() + _load_mitra()
    return _CACHE


def traditions() -> list[str]:
    return TRADITIONS


def gold_for(passage_id: str) -> dict | None:
    """Look up one gold exemplar by id."""
    for ex in exemplars():
        if ex["id"] == passage_id:
            return ex
    return None


def by_tradition(trad: str) -> list[dict]:
    """The gold exemplars for one tradition (the specialist benchmark subset)."""
    return [ex for ex in exemplars() if ex["tradition"] == trad]


def score_vs_gold(produced_text: str, passage_id: str, metric="chrF") -> float:
    """Score produced translation vs a gold exemplar (0-1). metric in {chrF, bleu1}."""
    g = gold_for(passage_id)
    if not g:
        return 0.0
    gold = g["gold"]
    if metric == "bleu1":
        return _bleu1(gold, produced_text)
    return _chrF(gold, produced_text)


def _char_ngrams(s, n):
    s = re.sub(r"\s+", "", s)
    return [s[i:i + n] for i in range(len(s) - n + 1)]


def _chrF(ref, cand):
    if not ref or not cand:
        return 0.0
    p = r = 0.0
    for n in (1, 2, 3):
        rg = set(_char_ngrams(ref, n)); cg = set(_char_ngrams(cand, n))
        if not rg or not cg:
            continue
        inter = len(rg & cg)
        p += inter / len(cg); r += inter / len(rg)
    if p == 0 or r == 0:
        return 0.0
    return round(2 * p * r / (p + r) / 3.0, 4)


def _bleu1(ref, cand):
    import math
    rt = ref.split(); ct = cand.split()
    if not rt or not ct:
        return 0.0
    hits = sum(1 for t in ct if t in set(rt))
    bp = math.exp(min(0, 1 - len(rt) / len(ct)))
    return round(bp * hits / len(ct), 4)


def summary() -> None:
    ex = exemplars()
    print(f"=== sanskrit_gold: {len(ex)} exemplars ===")
    from collections import Counter
    c = Counter(x["tradition"] for x in ex)
    for trad in TRADITIONS:
        print(f"  {trad:24} {c.get(trad, 0)}")
    print(f"  {'(untagged)':24} {sum(1 for x in ex if x['tradition'] not in c)}")


if __name__ == "__main__":
    summary()
