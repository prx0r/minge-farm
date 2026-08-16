#!/usr/bin/env python3
"""pipeline/sanskrit_texts.py — the PROGRESSIVE-DIFFICULTY Sanskrit benchmark suite.

Our own benchmark: test how well LLMs translate Sanskrit texts of INCREASING difficulty, tracking:
  - philosophical school / tradition (Pratyabhijñā, Śaiva Siddhānta, Krama, Vedānta, Nyāya, Buddhist logic)
  - time period (Vedic, Epic, Classical, Tantric)
  - specialist-term density (% of tokens that are unique technical terms to that school)

SOURCE: the Digital Corpus of Sanskrit (DCS / OliverHellwig, CC-BY) — 256 GRETIL machine-readable texts
covering every target school, + gold translations for some. Plus the imported frontier datasets.

The difficulty tiers (a fixed, reproducible ladder):
  T1 EASY    — modern/contemporary prose (Sāmayik) — low term density
  T2 MEDIUM  — Epic narrative (Itihāsa) — moderate
  T3 HARD    — Classical śāstric prose/verse (Nyāya, Vedānta, Yoga) — high term density
  T4 EXPERT  — Tantric/Śaiva/Pratyabhijñā scholastic (Abhinavagupta, Śaiva Tantras) — very high
             school-specific term density

A benchmark "row" = {source(IAST), school, period, difficulty_tier, term_density, passage_id}.
Deterministic + stdlib. The source of truth is the DCS clone; we index it once.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DCS = Path("/root/patalacheckpoints/source-evidence/repos/OliverHellwig__sanskrit/corpus/GRETIL")
FRONTIER = ROOT / "data" / "frontier"

# school → period → the GRETIL text-name fragments that belong to it
# (best-effort philological tagging; refined over time as the lemma-sense map grows)
SCHOOL_TEXTS: dict[str, list[str]] = {
    "Pratyabhijñā/Trika": ["abhinavagupta-", "kramastotra", "paryantapaJcAzikA", "anuttarASTikA",
                           "paramArthasAra", "mAlinIzlokavArttika", "ziva", "svacchanda", "vijaya",
                           "kubjika", "vInAzikha"],
    "Śaiva Siddhānta": ["siddhAnta", "tantra", "mata", "nibandha", "zivadRSTi"],
    "Krama": ["krama", "mAtRkA", "unmanI", "Ananda"],
    "Vedānta": ["vedAnta", "brahmasUtra", "siddhAntabindu", "upaniSad", "gauda", "zaGkara", "vivaraNa"],
    "Nyāya": ["nyAya", "pramANa", "anumAna", "tarka", "vAda", "hetu", "bAdarAyaNa"],
    "Yoga": ["yoga", "sAMkhya", "kArikA", "pataJjali"],
    "Buddhist": ["buddha", "sUtra", "mahAyAna", "jAtaka", "avadAna", "prajJA", "dharmakIrti",
                 "asaGga", "kArikA", "mAdhyamaka", "nAgArjuna", "vijJapti", "zAntideva"],
}

# the canonical difficulty tier for each school (the ladder)
SCHOOL_TIER: dict[str, int] = {
    "Pratyabhijñā/Trika": 4, "Śaiva Siddhānta": 4, "Krama": 4,   # Tantric/Expert
    "Nyāya": 3, "Vedānta": 3, "Yoga": 3, "Buddhist": 3,          # Classical/Hard
}

PERIOD_BY_SCHOOL = {
    "Pratyabhijñā/Trika": "Tantric", "Śaiva Siddhānta": "Tantric", "Krama": "Tantric",
    "Nyāya": "Classical", "Vedānta": "Classical", "Yoga": "Classical", "Buddhist": "Classical",
}


def _detect_school(filename: str) -> str | None:
    for school, frags in SCHOOL_TEXTS.items():
        if any(f in filename for f in frags):
            return school
    return None


def list_dcs_texts() -> list[dict]:
    """Index the DCS GRETIL texts: {file, school, tier, period, lines, size}."""
    out = []
    if not DCS.exists():
        return out
    for f in sorted(DCS.glob("*.txt")):
        lines = [l for l in f.read_text(encoding="utf-8", errors="ignore").splitlines()
                 if l and not l.startswith("#")]
        school = _detect_school(f.name)
        out.append({"file": f.name, "school": school or "Unclassified",
                    "tier": SCHOOL_TIER.get(school, 2) if school else 2,
                    "period": PERIOD_BY_SCHOOL.get(school, "Epic") if school else "Epic",
                    "lines": len(lines), "chars": sum(len(l) for l in lines)})
    return out


def load_dcs_text(filename: str, max_chars: int = 2000) -> str:
    """Load a DCS text, stripped of header/metadata, truncated for a benchmark passage."""
    p = DCS / filename
    if not p.exists():
        return ""
    lines = [l for l in p.read_text(encoding="utf-8", errors="ignore").splitlines()
             if l and not l.startswith("#")]
    return "\n".join(lines)[:max_chars]


# the specialist terms per school (the moat — for term-density + the vimarśa-style test).
# Seed set; grown from the MW lexicon + the lemma-sense map over time.
SCHOOL_TERMS: dict[str, list[str]] = {
    "Pratyabhijñā/Trika": ["vimarśa", "prakāśa", "śakti", "icchā", "jñānaśakti", "kriyāśakti",
                           "svātantrya", "pratyabhijñā", "aham", "caitanya", "unmeṣa", "sphurattā",
                           "viśrānti", "ābhāsa", "śambhu"],
    "Śaiva Siddhānta": ["pāśa", "mala", "bheda", "pramātṛ", "adhvā", "tattva", "kalā", "vidyā",
                        "kriyā", "dīkṣā", "nirodha", "māyā", "āṇava", "kārmika", "māyīya"],
    "Krama": ["krama", "mātṛkā", "unmanī", "ānanda", "sādhāra", "icchā", "śakti-pāta", "ucyate",
              "anuttara", "saṃvit", "akula"],
    "Vedānta": ["brahman", "ātman", "māyā", "avidyā", "jñāna", "bhakti", "mokṣa", "saguṇa",
                "nirguṇa", "āvaraṇa", "vikṣepa", "adhyāsa", "sat-cit-ānanda"],
    "Nyāya": ["pramāṇa", "anumāna", "pratyakṣa", "śabda", "upamāna", "hetu", "vyāpti", "pakṣa",
              "sādhya", "dṛṣṭānta", "nigraha", "tarka", "āpatti", "prasaṅga"],
    "Yoga": ["yoga", "samādhi", "dhyāna", "dhāraṇā", "kriyā", "viveka", "kaivalya", "puruṣa",
             "prakṛti", "guṇa", "sattva", "rajas", "tamas"],
    "Buddhist": ["śūnyatā", "prajñā", "upāya", "dharma", "nirvāṇa", "skandha", "kṣaṇikatva",
                 "pratītyasamutpāda", "bodhicitta", "śīla", "samādhi", "vijñapti", "mādhya", "śrotra"],
}


def term_density(text: str, school: str) -> dict:
    """% of content tokens that are specialist terms of `school` (the term-density axis).

    Uses STEM matching (a term like 'śambhu' matches inflected 'śambhuṃ', 'śambhoḥ' etc.) because
    Sanskrit is morphologically rich. A token is a specialist-term hit if it STARTS WITH a school term
    (or a school term starts with it, for sandhi-merged forms). Deterministic + stdlib.
    """
    terms = [t.lower() for t in SCHOOL_TERMS.get(school, [])]
    tokens = re.findall(r"[a-zA-Zāīūṛṝḷḹṃṁñṅśṣṭḍḥ]+", text.lower())
    if not tokens:
        return {"term_density": 0.0, "n_terms": 0, "n_tokens": 0, "school_terms_found": []}
    # a token is a specialist hit if it shares a significant stem with a school term
    n_terms = 0
    for tok in tokens:
        for term in terms:
            if (len(term) >= 4 and tok.startswith(term)) or (len(tok) >= 4 and term.startswith(tok)):
                n_terms += 1
                break
    found = [t for t in SCHOOL_TERMS.get(school, []) if t.lower() in text.lower()]
    return {"term_density": round(n_terms / len(tokens), 4), "n_terms": n_terms,
            "n_tokens": len(tokens), "school_terms_found": found}


def benchmark_rows(n_per_school: int = 5, max_chars: int = 2000) -> list[dict]:
    """Build the progressive-difficulty benchmark: N passages per school, tagged + tiered + density."""
    rows = []
    texts = list_dcs_texts()
    for school in SCHOOL_TEXTS:
        school_texts = [t for t in texts if t["school"] == school][:n_per_school]
        for t in school_texts:
            src = load_dcs_text(t["file"], max_chars)
            if not src:
                continue
            d = term_density(src, school)
            rows.append({"source": src, "school": school, "tier": t["tier"],
                         "period": t["period"], "passage_id": t["file"],
                         "term_density": d["term_density"],
                         "n_terms": d["n_terms"], "school_terms_found": d["school_terms_found"][:8]})
    return rows


def summary() -> dict:
    texts = list_dcs_texts()
    from collections import Counter
    by_school = Counter(t["school"] for t in texts)
    return {"n_texts": len(texts), "by_school": dict(by_school),
            "by_tier": dict(Counter(t["tier"] for t in texts))}


if __name__ == "__main__":
    s = summary()
    print(f"=== sanskrit_texts: {s['n_texts']} DCS texts ===")
    print("  by school:", s["by_school"])
    print("  by tier:", s["by_tier"])
    rows = benchmark_rows(n_per_school=2)
    print(f"\n  benchmark_rows(sample 2/school) = {len(rows)}")
    for r in rows[:4]:
        print(f"  [{r['tier']}] {r['school']:22} term_density={r['term_density']:.3f} "
              f"terms={r['n_terms']} → {r['source'][:50]}")
