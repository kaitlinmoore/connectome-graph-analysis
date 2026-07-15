"""Cross-check every hand-rolled metric against NetworkX on the identical graph.

THIS IS THE ONLY MODULE UNDER ``src/`` THAT MAY IMPORT NETWORKX. If you find
yourself wanting ``import networkx`` anywhere else, that is the exact failure
mode this repo exists to avoid — stop and use the from-scratch implementation.

Parity discipline (CLAUDE.md):

* Exact agreement expected — BFS distances, degree, connected components,
  clustering. Any mismatch is a bug.
* Tolerance-based agreement — eigenvector, PageRank, betweenness. Normalisation
  and convergence details differ; a small max-abs-diff is fine, a large one is
  a bug in the hand-rolled code until proven otherwise.

Parity with NetworkX is triangulation, not a crutch: the unit tests also pin
the algorithms to closed-form answers on tiny graphs (path/cycle/star/complete).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

import networkx as nx  # the one sanctioned import in src/

from connectome_graph.graph import (
    Graph,
    average_clustering,
    betweenness_centrality,
    bfs_distances,
    clustering_coefficient,
    connected_components,
    degree_centrality,
    eigenvector_centrality,
    pagerank,
)


def to_networkx(graph: Graph):
    """Build the NetworkX graph corresponding exactly to ``graph``."""
    G = nx.DiGraph() if graph.directed else nx.Graph()
    G.add_nodes_from(graph.nodes())
    for u, v, w in graph.edges():
        G.add_edge(u, v, weight=w)
    return G


@dataclass
class ParityResult:
    metric: str
    kind: str  # "exact" or "tolerance"
    agree: bool
    max_abs_diff: float
    tolerance: float
    detail: str = ""

    def __str__(self) -> str:
        status = "OK " if self.agree else "FAIL"
        return (
            f"[{status}] {self.metric:<24} {self.kind:<9} "
            f"max_abs_diff={self.max_abs_diff:.3e} tol={self.tolerance:.1e} {self.detail}"
        )


def _max_dict_diff(a: Dict, b: Dict) -> float:
    keys = set(a) | set(b)
    return max((abs(a.get(k, 0.0) - b.get(k, 0.0)) for k in keys), default=0.0)


def parity_report(
    graph: Graph,
    betweenness_tol: float = 1e-9,
    eigen_tol: float = 1e-6,
    pagerank_tol: float = 1e-6,
) -> List[ParityResult]:
    """Run the full parity suite and return one result per metric.

    Exact metrics use an effective tolerance of 0; iterative metrics use the
    documented tolerances (defaults chosen to pass on well-conditioned graphs
    while still catching real bugs).
    """
    G = to_networkx(graph)
    results: List[ParityResult] = []

    # --- exact: degree ---
    ours = {n: graph.degree(n) for n in graph.nodes()}
    if graph.directed:
        theirs = {n: G.in_degree(n) + G.out_degree(n) for n in G.nodes()}
    else:
        theirs = dict(G.degree())
    diff = _max_dict_diff(ours, theirs)
    results.append(ParityResult("degree", "exact", diff == 0, diff, 0.0))

    # --- exact: BFS distances from a representative source ---
    if graph.num_nodes:
        source = graph.nodes()[0]
        ours_d = bfs_distances(graph, source)
        theirs_d = dict(nx.single_source_shortest_path_length(G, source))
        diff = _max_dict_diff(ours_d, theirs_d)
        agree = ours_d.keys() == theirs_d.keys() and diff == 0
        results.append(
            ParityResult("bfs_distances", "exact", agree, diff, 0.0, f"src={source}")
        )

    # --- exact: connected components (weak, for digraphs) ---
    ours_cc = sorted((sorted(map(str, c)) for c in connected_components(graph)))
    if graph.directed:
        theirs_cc = sorted(
            (sorted(map(str, c)) for c in nx.weakly_connected_components(G))
        )
    else:
        theirs_cc = sorted(
            (sorted(map(str, c)) for c in nx.connected_components(G))
        )
    agree = ours_cc == theirs_cc
    results.append(
        ParityResult(
            "connected_components", "exact", agree, 0.0 if agree else 1.0, 0.0,
            f"{len(ours_cc)} vs {len(theirs_cc)} components",
        )
    )

    # --- exact-ish: clustering (undirected projection) ---
    Gu = G.to_undirected() if graph.directed else G
    ours_c = clustering_coefficient(graph)
    theirs_c = nx.clustering(Gu)
    diff = _max_dict_diff(ours_c, theirs_c)
    results.append(
        ParityResult("clustering", "exact", diff < 1e-12, diff, 1e-12)
    )
    ours_avg = average_clustering(graph)
    theirs_avg = nx.average_clustering(Gu)
    diff = abs(ours_avg - theirs_avg)
    results.append(
        ParityResult("average_clustering", "exact", diff < 1e-12, diff, 1e-12)
    )

    # --- tolerance: betweenness ---
    ours_b = betweenness_centrality(graph, normalized=True, weighted=False)
    theirs_b = nx.betweenness_centrality(G, normalized=True)
    diff = _max_dict_diff(ours_b, theirs_b)
    results.append(
        ParityResult("betweenness", "tolerance", diff <= betweenness_tol, diff, betweenness_tol)
    )

    # --- tolerance: eigenvector ---
    try:
        ours_e = eigenvector_centrality(graph, max_iter=5000, tol=1e-8)
        theirs_e = nx.eigenvector_centrality(G, max_iter=5000, tol=1e-8, weight="weight")
        diff = _max_dict_diff(ours_e, theirs_e)
        results.append(
            ParityResult("eigenvector", "tolerance", diff <= eigen_tol, diff, eigen_tol)
        )
    except Exception as exc:  # convergence differences can legitimately diverge
        results.append(
            ParityResult("eigenvector", "tolerance", False, float("nan"), eigen_tol, str(exc))
        )

    # --- tolerance: pagerank ---
    ours_p = pagerank(graph, alpha=0.85, tol=1e-10, max_iter=5000)
    theirs_p = nx.pagerank(G, alpha=0.85, tol=1e-10, max_iter=5000, weight="weight")
    diff = _max_dict_diff(ours_p, theirs_p)
    results.append(
        ParityResult("pagerank", "tolerance", diff <= pagerank_tol, diff, pagerank_tol)
    )

    return results


def all_agree(results: List[ParityResult]) -> bool:
    return all(r.agree for r in results)
