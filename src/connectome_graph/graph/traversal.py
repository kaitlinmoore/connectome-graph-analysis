"""Traversal and shortest paths, from scratch.

* ``bfs`` / ``bfs_distances`` — unweighted hop distances via breadth-first
  search. Exact-agreement territory in the NetworkX parity check.
* ``connected_components`` — flood fill. For directed graphs this returns
  *weakly* connected components (edge direction ignored), matching the
  ``nx.weakly_connected_components`` convention we validate against.
* ``dijkstra`` — weighted shortest paths with a binary heap. Requires
  non-negative weights, which synapse counts always satisfy.
"""

from __future__ import annotations

import heapq
from collections import deque
from typing import Dict, Hashable, List, Set

from connectome_graph.graph.graph import Graph

Node = Hashable


def bfs(graph: Graph, source: Node) -> Dict[Node, Node]:
    """Breadth-first search from ``source``.

    Returns a predecessor tree ``{node: parent}`` (``source`` maps to itself)
    covering every node reachable following out-edges.
    """
    if not graph.has_node(source):
        raise KeyError(f"source {source!r} not in graph")
    parent: Dict[Node, Node] = {source: source}
    q: deque = deque([source])
    while q:
        u = q.popleft()
        for v in graph.neighbors(u):
            if v not in parent:
                parent[v] = u
                q.append(v)
    return parent


def bfs_distances(graph: Graph, source: Node) -> Dict[Node, int]:
    """Hop distance from ``source`` to every reachable node (source = 0)."""
    if not graph.has_node(source):
        raise KeyError(f"source {source!r} not in graph")
    dist: Dict[Node, int] = {source: 0}
    q: deque = deque([source])
    while q:
        u = q.popleft()
        d = dist[u] + 1
        for v in graph.neighbors(u):
            if v not in dist:
                dist[v] = d
                q.append(v)
    return dist


def shortest_path_lengths(graph: Graph, source: Node, weighted: bool = False):
    """Convenience dispatcher: BFS hops or Dijkstra weighted distances."""
    if weighted:
        return dijkstra(graph, source)
    return bfs_distances(graph, source)


def connected_components(graph: Graph) -> List[Set[Node]]:
    """Connected components (weakly connected for directed graphs).

    Returned largest-first so ``connected_components(g)[0]`` is the giant
    component — the substrate for characteristic-path-length analysis.
    """
    # For a directed graph, traverse the underlying undirected structure by
    # considering both successors and predecessors.
    def undirected_neighbors(u: Node):
        if graph.directed:
            yield from graph.neighbors(u)
            yield from graph.predecessors(u)
        else:
            yield from graph.neighbors(u)

    seen: Set[Node] = set()
    components: List[Set[Node]] = []
    for start in graph.nodes():
        if start in seen:
            continue
        comp: Set[Node] = set()
        q: deque = deque([start])
        seen.add(start)
        while q:
            u = q.popleft()
            comp.add(u)
            for v in undirected_neighbors(u):
                if v not in seen:
                    seen.add(v)
                    q.append(v)
        components.append(comp)
    components.sort(key=len, reverse=True)
    return components


def dijkstra(graph: Graph, source: Node) -> Dict[Node, float]:
    """Single-source shortest path distances with a binary heap.

    Weights must be non-negative. Distances are summed edge weights along out
    edges. Only reachable nodes appear in the result.
    """
    if not graph.has_node(source):
        raise KeyError(f"source {source!r} not in graph")
    dist: Dict[Node, float] = {source: 0.0}
    heap: List = [(0.0, source)]
    finalized: Set[Node] = set()
    while heap:
        d, u = heapq.heappop(heap)
        if u in finalized:
            continue
        finalized.add(u)
        for v, w in graph.adjacency(u).items():
            if w < 0:
                raise ValueError("dijkstra requires non-negative edge weights")
            nd = d + w
            if v not in dist or nd < dist[v]:
                dist[v] = nd
                heapq.heappush(heap, (nd, v))
    return dist
