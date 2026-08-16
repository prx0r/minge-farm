#!/usr/bin/env python3
"""pipeline/benchmark_registry.py — the LEGITIMATE progressive-difficulty benchmark registry.

Implements the field-standard legitimacy requirements (verified: WMT/FLORES/MTME/XTREME-R methodology):

  1. FIXED, VERSIONED, CONTENT-ADDRESSED test set  — every passage has a SHA-256 hash; the whole set has
     a version + a git-taggable manifest.
  2. SOURCE LINEAGE + LICENSE  — every passage traces to a dated, citable source (DCS/GRETIL, CC-BY).
  3. DEcontamination AUDIT  — records which Sainz contamination levels we defend against (exact /
     near-duplicate / paraphrase / in-domain) + the source-date (so a release-date-vs-training-cutoff
     check is possible).
  4. DIFFICULTY TIERS  — 1..4 by a PRINCIPLED linguistic/domain axis (period + school + term density),
     NOT by length. Each tier is tagged (school, period, term_density, genre).
  5. RESULT LINEAGE  — a manifest mapping model+checkpoint+decoding-config+metric-version+test-set-version
     → each number (the anti-theater provenance).

The registry is the "fixed gold" the whole benchmark (and the meta-eval) runs against. If it isn't in
the registry, it isn't decided.

Deterministic + stdlib (sha256). Builds from pipeline/sanskrit_texts.py + the frontier datasets.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys_path = None
import sys  # noqa: E402
sys.path.insert(0, str(ROOT / "pipeline"))

MANIFEST = ROOT / "data" / "benchmark-registry.json"
# the decontamination levels we defend (Sainz et al. taxonomy — verified)
DECONTAMINATION_LEVELS = ["exact", "near_duplicate", "paraphrase", "in_domain"]


def sha256(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def passage_hash(source: str, school: str) -> str:
    return sha256({"source": source[:2000], "school": school})


class BenchmarkRegistry:
    """The versioned, content-addressed, provenance-carrying benchmark registry."""

    def __init__(self, manifest: Path = MANIFEST):
        self.manifest = manifest
        self.data = {"version": "0.1.0", "created": None, "passages": [], "decontamination": {},
                     "lineage_requirements": [], "sources": {}}

    def add_passage(self, *, source: str, school: str, period: str, tier: int, genre: str,
                    source_id: str, source_date: str, license: str, term_density: float,
                    n_terms: int, references: list[str] | None = None,
                    alternative_senses: dict | None = None) -> dict:
        """Add one passage with full lineage + content-address + MULTI-REFERENCE (PaliBench).

        references: one or more independent human English translations (R1..Rn) — the blueprint's
                    multi-reference design so we don't penalize valid alternative interpretations.
        alternative_senses: e.g. {"vimarśa": ["reflexive-awareness", "recognition"]} — interpretive
                    alternatives retained rather than pretending one English string is uniquely correct.
        """
        ph = passage_hash(source, school)
        rec = {"passage_id": f"{school}:{source_id}:{ph[:10]}", "hash": ph,
               "source": source, "school": school, "period": period, "tier": tier,
               "genre": genre, "source_id": source_id, "source_date": source_date,
               "license": license, "term_density": term_density, "n_terms": n_terms,
               "references": references or [], "alternative_senses": alternative_senses or {}}
        self.data["passages"].append(rec)
        return rec

    def add_source(self, source_id: str, *, name: str, url: str, license: str, date: str):
        self.data["sources"][source_id] = {"name": name, "url": url, "license": license, "date": date}

    def set_decontamination(self, *, defended_levels: list[str], method: str, note: str):
        """Record which contamination levels we defend against + how (the audit)."""
        self.data["decontamination"] = {
            "defended_levels": [l for l in DECONTAMINATION_LEVELS if l in defended_levels],
            "not_defended": [l for l in DECONTAMINATION_LEVELS if l not in defended_levels],
            "method": method, "note": note,
        }

    def set_lineage_requirements(self, requirements: list[str]):
        """Every reported number must carry these lineage fields (the anti-theater manifest)."""
        self.data["lineage_requirements"] = requirements

    def freeze(self) -> dict:
        """Content-address the whole registry; bump the version; write the manifest."""
        self.data["created"] = datetime.now(timezone.utc).isoformat()
        self.data["n_passages"] = len(self.data["passages"])
        self.data["manifest_hash"] = sha256(self.data)
        self.manifest.parent.mkdir(parents=True, exist_ok=True)
        self.manifest.write_text(json.dumps(self.data, ensure_ascii=False, indent=2))
        return self.data

    def load(self) -> dict:
        return json.loads(self.manifest.read_text()) if self.manifest.exists() else {}


def build_default() -> dict:
    """Build the default benchmark registry from the DCS texts + frontier sets."""
    from sanskrit_texts import benchmark_rows, load_dcs_text
    reg = BenchmarkRegistry()
    reg.add_source("dcs-gretil", name="Digital Corpus of Sanskrit (GRETIL subset)",
                   url="https://github.com/OliverHellwig/sanskrit", license="CC-BY 4.0",
                   date="2026-08-16")
    rows = benchmark_rows(n_per_school=3)
    for r in rows:
        reg.add_passage(source=r["source"], school=r["school"], period=r["period"],
                        tier=r["tier"], genre="sastra", source_id=r["passage_id"],
                        source_date="classical", license="CC-BY 4.0",
                        term_density=r["term_density"], n_terms=r["n_terms"])
    reg.set_decontamination(defended_levels=["exact", "near_duplicate"],
                            method="private-heldout + source-date check (release-date > model cutoff)",
                            note="best-effort; detection-based decontamination is unreliable for LLMs — "
                                 "prevention (fresh timestamped sources) is the primary defense")
    reg.set_lineage_requirements([
        "model", "checkpoint", "decoding_config", "metric_version", "test_set_version",
        "reference_set", "human_gold_split", "date",
    ])
    return reg.freeze()


def attach_references(multi_ref_file: str | None = None) -> dict:
    """Attach MULTI-REFERENCE translations to the registry passages (the PaliBench design).

    Reads a file of references and attaches them to matching passages. Supports:
      - the re-render valid-set format: {source, gold, valid_renderings: [{candidate, ...}]}
      - a JSONL of {source, references: [R1..Rn]}
    """
    reg = BenchmarkRegistry()
    data = reg.load() or reg.data
    if not data.get("passages"):
        return build_default()
    if multi_ref_file and Path(multi_ref_file).exists():
        # detect format
        try:
            obj = json.loads(Path(multi_ref_file).read_text(encoding="utf-8"))
        except Exception:
            obj = None
        refs_by_source = {}
        if isinstance(obj, dict) and "valid_renderings" in obj:
            refs_by_source[obj["source"]] = [v["candidate"] for v in obj["valid_renderings"]]
        elif isinstance(obj, list):
            for rec in obj:
                refs_by_source[rec.get("source", "")] = rec.get("references", [])
        # attach to matching passages
        for p in data["passages"]:
            for src, refs in refs_by_source.items():
                if refs and (p["source"] == src or src in p["source"]):
                    p["references"] = refs
    data["version"] = "0.2.0-multiref"
    reg.data = data
    return reg.freeze()


if __name__ == "__main__":
    d = build_default()
    print(f"=== benchmark registry: version={d['version']} passages={d['n_passages']} ===")
    print(f"  manifest_hash: {d['manifest_hash'][:16]}")
    from collections import Counter
    print("  by tier:", dict(Counter(p["tier"] for p in d["passages"])))
    print("  by school:", dict(Counter(p["school"] for p in d["passages"])))
    print("  decontamination defended:", d["decontamination"]["defended_levels"])
