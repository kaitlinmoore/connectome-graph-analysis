"""Phase 2: FlyWire whole-brain loader (Codex static CSV export).

Out of scope for v1 (see CLAUDE.md "Phase scope"): do not build against this
until C. elegans parity + the recovery result are committed. FlyWire is ~140k
neurons, so the loader must stream the Codex ``connections.csv`` export rather
than materialise it, and the dense-matrix centrality paths will need a sparse
rewrite. Left as a documented stub so the import site is stable.
"""

from __future__ import annotations

from pathlib import Path

from connectome_graph.graph.graph import Graph


def load_flywire(connections_csv: str | Path) -> Graph:  # pragma: no cover
    """Load the FlyWire connectome from a Codex static CSV export.

    Not implemented in v1. Expected Codex schema is
    ``pre_root_id,post_root_id,neuropil,syn_count,nt_type``; build a directed,
    synapse-count-weighted graph, streaming rows to stay within memory.
    """
    raise NotImplementedError(
        "FlyWire is Phase 2; commit C. elegans parity + recovery first (CLAUDE.md)."
    )
