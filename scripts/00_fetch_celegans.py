#!/usr/bin/env python
"""Stage 00 — fetch + harmonise the C. elegans connectome into processed CSVs.

Thin, reproducible entry point. Downloads the Cook et al. 2019 supplement (via
the OpenWorm ConnectomeToolbox mirror) into ``data/raw/celegans/`` and writes
two tidy files to ``data/processed/``:

    celegans_edges.csv   source,target,type,synapses
    celegans_nodes.csv   neuron,cell_class,neurotransmitter

Both processed files are gitignored; provenance and the exact download URL live
in the README. Actual download/parse of the Excel supplement is intentionally
left as a documented TODO so this stays a clear entry point rather than a
brittle scraper — fill it in when wiring up real data.

Usage:
    uv run python scripts/00_fetch_celegans.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = REPO_ROOT / "data" / "raw" / "celegans"
PROCESSED_DIR = REPO_ROOT / "data" / "processed"

# Provenance — record the exact source you actually download from in the README.
COOK_2019_SOURCE = (
    "Cook et al. 2019, Nature 571:63-71 — connectome supplement. "
    "Mirror: OpenWorm ConnectomeToolbox (github.com/openworm/ConnectomeToolbox)."
)


def main() -> int:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[00] raw dir:       {RAW_DIR}")
    print(f"[00] processed dir: {PROCESSED_DIR}")
    print(f"[00] source:        {COOK_2019_SOURCE}")

    edges_out = PROCESSED_DIR / "celegans_edges.csv"
    if edges_out.exists():
        print(f"[00] {edges_out.name} already present — nothing to do.")
        return 0

    print(
        "[00] TODO: download the Cook 2019 supplement into data/raw/celegans/ "
        "and harmonise it to Cook-2019 neuron identities (relabel any "
        "White-1986 edge list; fix PVCL/PVCR and DVB/PVT). Then write "
        "celegans_edges.csv and celegans_nodes.csv. See "
        "reference/functional_labels.md for the identity rule."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
