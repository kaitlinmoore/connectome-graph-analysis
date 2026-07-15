#!/usr/bin/env python
"""Stage 04 — THE PUNCHLINE.

For each graph variant and each centrality measure:
  1. Recovery — precision@k and mean rank of the command-interneuron set.
  2. Beyond-degree null test — does the measure concentrate on the command set
     MORE than a degree-preserving configuration-model null? Empirical p-value.

Prints a per-variant table and writes ``results/hub_recovery.csv``. The verdict
is reported whichever way the data falls: if degree explains everything, that is
the honest finding.

Usage:
    uv run python scripts/04_hub_recovery.py
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from connectome_graph.analysis import (  # noqa: E402
    load_command_interneurons,
    null_enrichment_test,
    recovery_report,
)
from connectome_graph.graph import (  # noqa: E402
    betweenness_centrality,
    degree_centrality,
    eigenvector_centrality,
    pagerank,
)
from connectome_graph.io.celegans import build_variants, read_edge_records  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
EDGES = REPO_ROOT / "data" / "processed" / "celegans_edges.csv"
RESULTS = REPO_ROOT / "results"

# Metric name -> score function. Degree is the baseline the others must clear.
METRICS = {
    "degree": lambda g: degree_centrality(g),
    "betweenness": lambda g: betweenness_centrality(g, normalized=True, weighted=False),
    "eigenvector": lambda g: eigenvector_centrality(g, max_iter=5000, tol=1e-8),
    "pagerank": lambda g: pagerank(g, alpha=0.85),
}


def main() -> int:
    if not EDGES.exists():
        print(f"[04] missing {EDGES} — run scripts/00-03 first.")
        return 1
    RESULTS.mkdir(exist_ok=True)

    targets = load_command_interneurons("primary")
    print(f"[04] command-interneuron target set ({len(targets)}): {sorted(targets)}")

    variants = build_variants(read_edge_records(EDGES))
    out_path = RESULTS / "hub_recovery.csv"
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            ["variant", "metric", "p@5", "p@10", "mean_rank",
             "observed_conc", "null_mean", "z", "p_beyond_degree", "beyond_degree"]
        )
        for v in variants:
            print(f"\n[04] === {v.name} ===")
            for name, fn in METRICS.items():
                try:
                    scores = fn(v.graph)
                except Exception as exc:
                    print(f"     {name:<12} skipped: {exc}")
                    continue
                rec = recovery_report(scores, targets, name, ks=(5, 10, 20))
                null = null_enrichment_test(
                    v.graph, fn, targets, name, num_nulls=100, seed=0
                )
                print(
                    f"     {name:<12} p@5={rec.precision_at_k[5]:.2f} "
                    f"p@10={rec.precision_at_k[10]:.2f} "
                    f"mean_rank={rec.mean_rank:.1f} | {null}"
                )
                writer.writerow([
                    v.name, name,
                    f"{rec.precision_at_k[5]:.3f}", f"{rec.precision_at_k[10]:.3f}",
                    f"{rec.mean_rank:.2f}",
                    f"{null.observed:.4f}", f"{null.null_mean:.4f}",
                    f"{null.z_score:.3f}", f"{null.p_value_right:.4f}",
                    null.beyond_degree,
                ])

    print(f"\n[04] wrote {out_path}")
    print("[04] TL;DR = read the 'beyond_degree' column: True only where the "
          "specific wiring concentrates the metric on the command set beyond "
          "a degree-preserving null.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
