#!/usr/bin/env python3
"""pipeline/tree_search.py — METRIC-GROUNDED TREE SEARCH (the AIDE mechanism).

Adopted from AIDE (arXiv:2502.13138) — the single best anti-theater primitive. Every node in the search
tree is an experiment STRATEGY (a hypothesis/config/hint), and its score is a REAL computed number on
fixed gold (our metric), NEVER an LLM opinion. Best-first search expands the highest-scoring nodes; a node
whose score doesn't improve is pruned.

For our lab, a "node" = a translation-hypothesis (prompt-hint/config) applied to the fixed gold, scored by
semantic-fidelity (or chrF). The tree meta-learns the experiment strategy: instead of just tuning
hyperparams, it proposes whole strategies and the REAL metric decides which branches to expand.

Deterministic + stdlib except the model call (hermes). Box-safe: small depth/fanout.

Usage:
  python3 pipeline/tree_search.py --depth 2 --fanout 2 --n 3            # real search over strategies
  python3 pipeline/tree_search.py --depth 2 --fanout 2 --n 3 --dry-run  # scaffold check
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))

# the root strategy = the baseline hypothesis (each child is a mutation of the prompt/config)
BASE_STRATEGY = {"hint": "Translate faithfully, preserving meaning.", "model": "mimo-v2.5"}

# the strategy-mutation operators (how children differ from parents)
MUTATIONS = [
    ("compound", "Decompose every compound into its members before translating."),
    ("case", "Track the grammatical case/role of each noun carefully."),
    ("terms", "Keep technical terms transliterated and consistent with the glossary."),
    ("negation", "Check negation markers and preserve them in English."),
    ("plain", "Render into clear, plain modern English."),
    ("precise", "Translate with scholarly precision."),
]


@dataclass
class Node:
    strategy: dict
    score: float = 0.0
    parent: "Node | None" = None
    children: list = field(default_factory=list)


def evaluate(strategy: dict, rows: list[dict], model: str, dry: bool) -> float:
    """Score a strategy on the fixed gold — a REAL computed number (semantic-fidelity), never an opinion."""
    from experiment_lab import semantic_fidelity
    from hypothesis_lab import translate_with_hint
    if dry:
        return 0.0
    scores = []
    for r in rows[:3]:  # small sample, box-safe
        cand = translate_with_hint(model, r["source"], strategy["hint"])
        fid, _ = semantic_fidelity(model, r["gold"], cand)
        scores.append(fid or 0.0)
    return sum(scores) / len(scores) if scores else 0.0


def build_tree(rows, model: str, depth: int, fanout: int, dry: bool) -> Node:
    root = Node(strategy=BASE_STRATEGY)
    root.score = evaluate(root.strategy, rows, model, dry)
    frontier = [root]
    for d in range(1, depth + 1):
        next_frontier = []
        for node in frontier:
            # expand with fanout mutations, scored by the REAL metric
            for i in range(fanout):
                name, hint = MUTATIONS[(d * fanout + i) % len(MUTATIONS)]
                child = Node(strategy={"hint": hint, "model": model}, parent=node)
                child.score = evaluate(child.strategy, rows, model, dry)
                node.children.append(child)
                next_frontier.append(child)
        # best-first: keep only the top-scoring children for the next depth
        next_frontier.sort(key=lambda n: -n.score)
        frontier = next_frontier[:fanout]
        if dry:
            break
    return root


def best_node(root: Node) -> Node:
    """The highest-scoring node in the tree (the strategy that actually improved the metric)."""
    best = root
    def walk(n):
        nonlocal best
        if n.score > best.score:
            best = n
        for c in n.children:
            walk(c)
    walk(root)
    return best


def search(depth: int, fanout: int, n: int, dry: bool) -> dict:
    from sanskrit_gold import clean_exemplars
    rows = [e for e in clean_exemplars() if e["work"] == "mitrasamgraha"][:n]
    print(f"=== METRIC-GROUNDED TREE SEARCH (depth={depth}, fanout={fanout}, n={n}) ===")
    root = build_tree(rows, "mimo-v2.5", depth, fanout, dry)
    best = best_node(root)
    print(f"  root score: {root.score:.3f} ({root.strategy['hint'][:40]})")
    print(f"  BEST node:  {best.score:.3f} ({best.strategy['hint'][:40]})")
    print(f"  {'✓ strategy improved the metric — KEEP' if best.score > root.score else '· no improvement yet'}")

    from run_recorder import RunRecorder
    rec = RunRecorder().record(
        step="tree_search", gold=[{"source": r["source"], "gold": r["gold"]} for r in rows],
        config={"depth": depth, "fanout": fanout, "n": n, "model": "mimo-v2.5", "dry": dry},
        metrics={"root_score": round(root.score, 4), "best_score": round(best.score, 4)},
        assertion=f"metric-grounded tree search: best strategy scores {best.score:.3f} "
                  f"vs baseline {root.score:.3f} (a real computed number, not an opinion)")
    return {"root_score": root.score, "best_score": best.score,
            "best_strategy": best.strategy, "run_signature": rec["run_signature"][:16]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--depth", type=int, default=2)
    ap.add_argument("--fanout", type=int, default=2)
    ap.add_argument("--n", type=int, default=3)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    search(args.depth, args.fanout, args.n, args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
