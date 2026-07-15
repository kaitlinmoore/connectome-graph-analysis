"""OPTIONAL stretch: community structure.

Not on the critical path for the headline question. Left as a documented stub
with a stable API so the analysis stage can call it once v1's parity +
recovery result is committed. Implement one of:

* spectral embedding — Fiedler vector of the graph Laplacian (numpy eigsh on a
  hand-built Laplacian), bisection by sign; recurse for k>2.
* Louvain — greedy modularity maximisation with the resolution-limit caveat.

Both must remain from-scratch (no ``networkx.algorithms.community``). The
Laplacian route reuses only numpy linear algebra, consistent with the rest of
the library.
"""

from __future__ import annotations

from typing import Dict, Hashable, List

from connectome_graph.graph.graph import Graph

Node = Hashable


def spectral_bisection(graph: Graph) -> Dict[Node, int]:  # pragma: no cover
    """Partition nodes into two communities by the Fiedler vector sign.

    Not yet implemented — see module docstring. Kept so import sites are stable.
    """
    raise NotImplementedError(
        "community detection is a Phase-1 stretch goal; implement spectral "
        "bisection or Louvain from scratch before enabling the analysis hook."
    )


def louvain(graph: Graph, resolution: float = 1.0) -> List[set]:  # pragma: no cover
    """Greedy modularity communities (Louvain). Not yet implemented."""
    raise NotImplementedError(
        "community detection is a Phase-1 stretch goal; see module docstring."
    )
