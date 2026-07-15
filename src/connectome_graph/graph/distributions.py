"""Degree distributions and clustering, from scratch.

Clustering is defined on the **undirected projection** of the graph: neighbour
sets ignore edge direction and reciprocal edges collapse to one. This matches
``nx.clustering`` applied to ``G.to_undirected()``, which is what the parity
check compares against, and it is the biologically standard convention for
connectome clustering.
"""

from __future__ import annotations

from typing import Dict, Hashable, Optional, Set

from connectome_graph.graph.graph import Graph

Node = Hashable


def degree_distribution(graph: Graph, mode: str = "total") -> Dict[int, int]:
    """Map degree -> number of nodes with that degree.

    ``mode`` is ``"total"`` (default), ``"in"``, or ``"out"``. For an
    undirected graph all three coincide.
    """
    if mode == "in":
        deg = graph.in_degree
    elif mode == "out":
        deg = graph.out_degree
    else:
        deg = graph.degree
    hist: Dict[int, int] = {}
    for n in graph.nodes():
        k = deg(n)
        hist[k] = hist.get(k, 0) + 1
    return hist


def _undirected_neighbor_set(graph: Graph, u: Node) -> Set[Node]:
    if graph.directed:
        nbrs = set(graph.neighbors(u)) | set(graph.predecessors(u))
    else:
        nbrs = set(graph.neighbors(u))
    nbrs.discard(u)  # ignore self-loops for clustering
    return nbrs


def clustering_coefficient(
    graph: Graph, node: Optional[Node] = None
) -> "Dict[Node, float] | float":
    """Local clustering coefficient.

    For node ``v`` with undirected neighbour set ``N(v)`` of size ``k``::

        C(v) = 2 * (# edges among neighbours) / (k * (k - 1)),  k >= 2
        C(v) = 0                                                 otherwise

    Pass a ``node`` for a single float; omit it for ``{node: C(node)}``.
    """
    if node is not None:
        return _local_clustering(graph, node)
    return {n: _local_clustering(graph, n) for n in graph.nodes()}


def _local_clustering(graph: Graph, v: Node) -> float:
    nbrs = _undirected_neighbor_set(graph, v)
    k = len(nbrs)
    if k < 2:
        return 0.0
    links = 0
    # Count unordered neighbour pairs that are themselves adjacent. Using the
    # undirected projection: an edge exists if either direction is present.
    nbr_list = list(nbrs)
    for i in range(len(nbr_list)):
        a = nbr_list[i]
        a_adj = _undirected_neighbor_set(graph, a)
        for j in range(i + 1, len(nbr_list)):
            if nbr_list[j] in a_adj:
                links += 1
    return (2.0 * links) / (k * (k - 1))


def average_clustering(graph: Graph) -> float:
    """Mean of the local clustering coefficients (Watts–Strogatz C)."""
    n = graph.num_nodes
    if n == 0:
        return 0.0
    total = sum(_local_clustering(graph, v) for v in graph.nodes())
    return total / n


def transitivity(graph: Graph) -> float:
    """Global clustering: 3 * (# triangles) / (# connected triples).

    Computed on the undirected projection. Returns 0.0 for a graph with no
    connected triples.
    """
    triangles_times_6 = 0  # each triangle counted 6× (once per ordered pair per apex)
    triples_times_2 = 0
    for v in graph.nodes():
        nbrs = _undirected_neighbor_set(graph, v)
        k = len(nbrs)
        if k < 2:
            continue
        triples_times_2 += k * (k - 1)
        nbr_list = list(nbrs)
        for i in range(len(nbr_list)):
            a_adj = _undirected_neighbor_set(graph, nbr_list[i])
            for j in range(i + 1, len(nbr_list)):
                if nbr_list[j] in a_adj:
                    triangles_times_6 += 2  # symmetric pair (i,j)/(j,i)
    if triples_times_2 == 0:
        return 0.0
    return triangles_times_6 / triples_times_2
