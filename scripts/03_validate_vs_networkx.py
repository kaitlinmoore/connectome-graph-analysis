#!/usr/bin/env python
"""Stage 03 — validate every hand-rolled metric against NetworkX.

Runs the parity suite (the ONE place networkx is used) on each graph variant
and prints a table: exact metrics must match exactly; iterative metrics must
match to their documented tolerance. Exits non-zero if anything fails, so this
doubles as a CI gate.

Usage:
    uv run python scripts/03_validate_vs_networkx.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from connectome_graph.io.celegans import build_variants, read_edge_records  # noqa: E402
from connectome_graph.validation.networkx_parity import parity_report  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
EDGES = REPO_ROOT / "data" / "processed" / "celegans_edges.csv"


def main() -> int:
    if not EDGES.exists():
        print(f"[03] missing {EDGES} — run scripts/00 and 01 first.")
        return 1

    variants = build_variants(read_edge_records(EDGES))
    all_ok = True
    for v in variants:
        print(f"\n[03] parity for {v.name}")
        for result in parity_report(v.graph):
            print("     " + str(result))
            all_ok = all_ok and result.agree

    print("\n[03] " + ("ALL PARITY CHECKS PASSED" if all_ok else "PARITY FAILURES — investigate"))
    return 0 if all_ok else 2


if __name__ == "__main__":
    sys.exit(main())
