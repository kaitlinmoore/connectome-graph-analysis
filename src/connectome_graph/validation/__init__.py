"""Validation by triangulation against NetworkX.

This subpackage is the ONE sanctioned home for a NetworkX import in the whole
``src/`` tree (see CLAUDE.md). Its sole job is to cross-check the hand-rolled
implementations. Nothing here is imported by the algorithms it validates.
"""

from connectome_graph.validation.networkx_parity import (
    ParityResult,
    to_networkx,
    parity_report,
)

__all__ = ["ParityResult", "to_networkx", "parity_report"]
