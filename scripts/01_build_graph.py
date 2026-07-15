#!/usr/bin/env python
"""Stage 01 — build the family of graph variants and report basic stats.

Graph construction is a modelling decision (CLAUDE.md), so we build the whole
family — combined / chemical / gap × directed/undirected × binary/weighted —
and print node/edge counts and component structure for each. No single graph is
privileged.

Usage:
    uv run python scripts/01_build_graph.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from connectome_graph.graph import connected_components  # noqa: E402
from connectome_graph.io.celegans import build_variants, read_edge_records  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
EDGES = REPO_ROOT / "data" / "processed" / "celegans_edges.csv"


def main() -> int:
    if not EDGES.exists():
        print(f"[01] missing {EDGES} — run scripts/00_fetch_celegans.py first.")
        return 1

    records = read_edge_records(EDGES)
    print(f"[01] loaded {len(records)} edge records from {EDGES.name}")

    variants = build_variants(records)
    header = f"{'variant':<32} {'nodes':>6} {'edges':>7} {'components':>11} {'giant':>6}"
    print(header)
    print("-" * len(header))
    for v in variants:
        comps = connected_components(v.graph)
        giant = len(comps[0]) if comps else 0
        print(
            f"{v.name:<32} {v.graph.num_nodes:>6} {v.graph.num_edges:>7} "
            f"{len(comps):>11} {giant:>6}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
