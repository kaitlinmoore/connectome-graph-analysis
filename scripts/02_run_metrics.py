#!/usr/bin/env python
"""Stage 02 — compute the metric suite on each graph variant.

Runs degree / betweenness / eigenvector / PageRank centralities plus the
small-world summary (C, L, sigma vs ER null) on every variant and writes a tidy
table to ``results/metrics.csv``. Exploration only lives in notebooks/; this is
the reproducible path.

Usage:
    uv run python scripts/02_run_metrics.py
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from connectome_graph.graph import (  # noqa: E402
    betweenness_centrality,
    degree_centrality,
    eigenvector_centrality,
    pagerank,
    small_world_sigma,
)
from connectome_graph.io.celegans import build_variants, read_edge_records  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
EDGES = REPO_ROOT / "data" / "processed" / "celegans_edges.csv"
RESULTS = REPO_ROOT / "results"


def main() -> int:
    if not EDGES.exists():
        print(f"[02] missing {EDGES} — run scripts/00 and 01 first.")
        return 1
    RESULTS.mkdir(exist_ok=True)

    variants = build_variants(read_edge_records(EDGES))
    out_path = RESULTS / "metrics.csv"
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["variant", "node", "degree", "betweenness", "eigenvector", "pagerank"])
        for v in variants:
            g = v.graph
            print(f"[02] metrics for {v.name} ...")
            deg = degree_centrality(g)
            btw = betweenness_centrality(g, normalized=True, weighted=False)
            try:
                eig = eigenvector_centrality(g, max_iter=5000, tol=1e-8)
            except Exception as exc:
                print(f"      eigenvector skipped: {exc}")
                eig = {n: float("nan") for n in g.nodes()}
            pr = pagerank(g, alpha=0.85)
            for n in g.nodes():
                writer.writerow([v.name, n, deg[n], btw[n], eig[n], pr[n]])

            sw = small_world_sigma(g, num_nulls=10, seed=0)
            print(
                f"      small-world: C={sw['C']:.3f} L={sw['L']:.3f} "
                f"sigma={sw['sigma']:.2f}"
            )

    print(f"[02] wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
