"""Centrality measures, from scratch.

Four measures, each a candidate answer to the headline question (which best
recovers the command interneurons, and does any beat raw degree):

* ``degree_centrality`` — the baseline the "beyond degree" test must clear.
* ``betweenness_centrality`` — Brandes' algorithm (BFS accumulation for the
  unweighted case, Dijkstra accumulation for the weighted case).
* ``eigenvector_centrality`` — power iteration.
* ``pagerank`` — power iteration with damping and dangling-node handling.

The iterative measures replicate NetworkX's update conventions so the parity
check compares like with like; agreement is expected only to a tolerance
because normalisation and convergence details differ slightly.
"""

from __future__ import annotations

import heapq
from math import sqrt
from typing import Dict, Hashable, List, Optional

from connectome_graph.graph.graph import Graph

Node = Hashable


# --------------------------------------------------------------------------- #
# degree
# --------------------------------------------------------------------------- #
def degree_centrality(graph: Graph, mode: str = "total") -> Dict[Node, float]:
    """Degree centrality, normalised by the max possible degree ``n - 1``.

    ``mode`` selects ``"total"`` / ``"in"`` / ``"out"`` for directed graphs.
    """
    n = graph.num_nodes
    if n <= 1:
        return {v: 0.0 for v in graph.nodes()}
    scale = 1.0 / (n - 1)
    if mode == "in":
        deg = graph.in_degree
    elif mode == "out":
        deg = graph.out_degree
    else:
        deg = graph.degree
    return {v: deg(v) * scale for v in graph.nodes()}


# --------------------------------------------------------------------------- #
# betweenness (Brandes 2001)
# --------------------------------------------------------------------------- #
def betweenness_centrality(
    graph: Graph, normalized: bool = True, weighted: bool = False
) -> Dict[Node, float]:
    """Shortest-path betweenness via Brandes' algorithm.

    ``weighted=True`` uses Dijkstra shortest paths (summed edge weights);
    otherwise BFS hop-distance shortest paths. Normalisation matches NetworkX:
    divide by ``(n-1)(n-2)`` for directed graphs and ``(n-1)(n-2)/2`` for
    undirected, and undirected accumulation is halved.
    """
    betweenness: Dict[Node, float] = {v: 0.0 for v in graph.nodes()}
    for s in graph.nodes():
        if weighted:
            S, P, sigma = _sssp_dijkstra(graph, s)
        else:
            S, P, sigma = _sssp_bfs(graph, s)
        # back-propagation of dependencies
        delta: Dict[Node, float] = {v: 0.0 for v in S}
        while S:
            w = S.pop()
            coeff = (1.0 + delta[w]) / sigma[w]
            for v in P[w]:
                delta[v] += sigma[v] * coeff
            if w != s:
                betweenness[w] += delta[w]
    return _rescale_betweenness(betweenness, graph.num_nodes, normalized, graph.directed)


def _sssp_bfs(graph: Graph, s: Node):
    """Single-source shortest paths (unweighted) with sigma path counts."""
    S: List[Node] = []
    P: Dict[Node, List[Node]] = {v: [] for v in graph.nodes()}
    sigma: Dict[Node, float] = {v: 0.0 for v in graph.nodes()}
    dist: Dict[Node, int] = {}
    sigma[s] = 1.0
    dist[s] = 0
    queue: List[Node] = [s]
    qi = 0
    while qi < len(queue):
        v = queue[qi]
        qi += 1
        S.append(v)
        dv = dist[v]
        for w in graph.neighbors(v):
            if w not in dist:
                dist[w] = dv + 1
                queue.append(w)
            if dist[w] == dv + 1:
                sigma[w] += sigma[v]
                P[w].append(v)
    return S, P, sigma


def _sssp_dijkstra(graph: Graph, s: Node):
    """Single-source shortest paths (weighted) with sigma path counts."""
    S: List[Node] = []
    P: Dict[Node, List[Node]] = {v: [] for v in graph.nodes()}
    sigma: Dict[Node, float] = {v: 0.0 for v in graph.nodes()}
    sigma[s] = 1.0
    dist: Dict[Node, float] = {}
    seen: Dict[Node, float] = {s: 0.0}
    heap: List = [(0.0, s, s)]
    while heap:
        d, _, v = heapq.heappop(heap)
        if v in dist:
            continue
        dist[v] = d
        S.append(v)
        for w, weight in graph.adjacency(v).items():
            vw = d + weight
            if w not in dist and (w not in seen or vw < seen[w]):
                seen[w] = vw
                sigma[w] = sigma[v]
                P[w] = [v]
                heapq.heappush(heap, (vw, w, w))
            elif vw == seen.get(w):
                sigma[w] += sigma[v]
                P[w].append(v)
    return S, P, sigma


def _rescale_betweenness(betweenness, n, normalized, directed):
    # Mirrors nx.betweenness_centrality._rescale exactly, so parity is exact.
    # Normalisation divides by (n-1)(n-2) for BOTH directed and undirected; the
    # undirected double-counting from Brandes' sum-over-all-sources is halved
    # ONLY in the unnormalised branch (scale = 0.5).
    if normalized:
        scale = None if n <= 2 else 1.0 / ((n - 1) * (n - 2))
    else:
        scale = None if directed else 0.5
    if scale is not None:
        for v in betweenness:
            betweenness[v] *= scale
    return betweenness


# --------------------------------------------------------------------------- #
# eigenvector centrality (power iteration)
# --------------------------------------------------------------------------- #
def eigenvector_centrality(
    graph: Graph,
    max_iter: int = 1000,
    tol: float = 1.0e-6,
    weight: bool = True,
) -> Dict[Node, float]:
    """Eigenvector centrality by power iteration.

    Update follows NetworkX: each node pushes its current score along its out
    edges (``x[nbr] += x[node] * w``), then the vector is L2-normalised.
    Raises ``PowerIterationFailedError`` if it does not converge.
    """
    nodes = graph.nodes()
    n = len(nodes)
    if n == 0:
        return {}
    x: Dict[Node, float] = {v: 1.0 / n for v in nodes}
    for _ in range(max_iter):
        xlast = x
        x = dict.fromkeys(xlast, 0.0)
        for node in x:
            for nbr, w in graph.adjacency(node).items():
                x[nbr] += xlast[node] * (w if weight else 1.0)
        norm = sqrt(sum(v * v for v in x.values())) or 1.0
        x = {k: v / norm for k, v in x.items()}
        if sum(abs(x[k] - xlast[k]) for k in x) < n * tol:
            return x
    raise PowerIterationFailedError(
        f"eigenvector_centrality did not converge in {max_iter} iterations"
    )


# --------------------------------------------------------------------------- #
# pagerank (power iteration with damping)
# --------------------------------------------------------------------------- #
def pagerank(
    graph: Graph,
    alpha: float = 0.85,
    max_iter: int = 1000,
    tol: float = 1.0e-6,
    weight: bool = True,
) -> Dict[Node, float]:
    """PageRank by power iteration.

    Row-normalises out-edge weights into a stochastic matrix, damps with
    ``alpha``, and redistributes dangling (sink) mass uniformly. Matches the
    NetworkX default convention (uniform personalisation, uniform dangling).
    """
    nodes = graph.nodes()
    n = len(nodes)
    if n == 0:
        return {}

    # out-weight sums for row normalisation
    out_w: Dict[Node, float] = {}
    for node in nodes:
        s = sum((w if weight else 1.0) for w in graph.adjacency(node).values())
        out_w[node] = s
    dangling = [node for node in nodes if out_w[node] == 0.0]

    x: Dict[Node, float] = {v: 1.0 / n for v in nodes}
    base = (1.0 - alpha) / n
    for _ in range(max_iter):
        xlast = x
        x = dict.fromkeys(nodes, 0.0)
        dangling_sum = alpha * sum(xlast[d] for d in dangling)
        for node in nodes:
            share = alpha * xlast[node] / out_w[node] if out_w[node] else 0.0
            if share:
                for nbr, w in graph.adjacency(node).items():
                    x[nbr] += share * (w if weight else 1.0)
        for node in nodes:
            x[node] += base + dangling_sum / n
        err = sum(abs(x[node] - xlast[node]) for node in nodes)
        if err < n * tol:
            return x
    raise PowerIterationFailedError(
        f"pagerank did not converge in {max_iter} iterations"
    )


class PowerIterationFailedError(Exception):
    """Raised when a power-iteration method fails to converge."""
