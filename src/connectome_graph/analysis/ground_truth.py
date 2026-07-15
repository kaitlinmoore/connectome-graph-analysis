"""Load the command-interneuron ground-truth set from ``reference/``.

One source of truth: every code path that needs the target set reads the same
``reference/command_interneurons.csv``, whose provenance is documented in
``reference/functional_labels.md``. The set is functional (ablation /
electrophysiology), independent of the graph — that independence is what makes
the recovery test non-circular.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List, Optional, Set

# repo root = three parents up from this file:
# .../src/connectome_graph/analysis/ground_truth.py -> repo root
_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_CSV = _REPO_ROOT / "reference" / "command_interneurons.csv"


def load_command_interneurons(
    which: str = "primary", path: Optional[Path] = None
) -> Set[str]:
    """Return the set of command-interneuron cell names.

    ``which`` ∈ {``"primary"``, ``"extended"``, ``"all"``}. ``"primary"`` is the
    canonical ten-cell headline set (AVA/AVB/AVD/AVE/PVC × L/R); ``"extended"``
    adds the weaker-evidence cells for sensitivity checks only.
    """
    rows = _read_rows(path)
    if which == "all":
        return {r["neuron"] for r in rows}
    return {r["neuron"] for r in rows if r["set"] == which}


def load_class_map(path: Optional[Path] = None) -> Dict[str, str]:
    """Return ``{cell_name: class}`` (e.g. ``{"AVAL": "AVA"}``)."""
    return {r["neuron"]: r["class"] for r in _read_rows(path)}


def _read_rows(path: Optional[Path]) -> List[Dict[str, str]]:
    csv_path = Path(path) if path is not None else _DEFAULT_CSV
    if not csv_path.exists():
        raise FileNotFoundError(
            f"command-interneuron ground truth not found at {csv_path}. "
            "See reference/functional_labels.md."
        )
    with csv_path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))
