"""Null models, from scratch.

Two nulls, for two different questions:

* ``erdos_renyi_gnm`` — a random graph with the same node and edge count. The
  crude "is there any structure at all?" baseline for small-world sigma.
* ``double_edge_swap`` / ``configuration_model`` — degree-preserving
  randomisation. This is the load-bearing null for the headline question:
  it holds every node's degree fixed and destroys everything else, so a metric
  that concentrates on the command interneurons MORE than this null does is
  concentrating on structure *beyond* degree. That is the non-circular test.

Randomness is seeded through ``random.Random(seed)`` so every null is
reproducible from ``scripts/``.
"""

from __future__ import annotations

import random
from typing import List, Optional, Sequence

from connectome_graph.graph.graph import Graph


def erdos_renyi_gnm(
    n: int,
    m: int,
    directed: bool = False,
    seed: Optional[int] = None,
    nodes: Optional[Sequence] = None,
) -> Graph:
    """G(n, m): ``n`` nodes and exactly ``m`` distinct edges, uniformly random.

    Node labels default to ``0..n-1``; pass ``nodes`` to reuse real names.
    """
    rng = random.Random(seed)
    labels = list(nodes) if nodes is not None else list(range(n))
    if len(labels) != n:
        raise ValueError("len(nodes) must equal n")
    g = Graph(directed=directed, weighted=False)
    g.add_nodes_from(labels)

    max_edges = n * (n - 1) if directed else n * (n - 1) // 2
    if m > max_edges:
        raise ValueError(f"m={m} exceeds max {max_edges} for n={n}")

    added = 0
    while added < m:
        u = rng.randrange(n)
        v = rng.randrange(n)
        if u == v:
            continue
        a, b = labels[u], labels[v]
        if g.has_edge(a, b):
            continue
        g.add_edge(a, b)
        added += 1
    return g


def double_edge_swap(
    graph: Graph,
    num_swaps: int = 100,
    seed: Optional[int] = None,
    max_tries: Optional[int] = None,
) -> Graph:
    """Randomise a graph by repeated double-edge swaps, preserving all degrees.

    Undirected swap: pick edges ``(a,b)`` and ``(c,d)`` → ``(a,c)`` and
    ``(b,d)``. Directed swap: pick ``a->b`` and ``c->d`` → ``a->d`` and
    ``c->b`` (preserves every in- and out-degree exactly). Swaps that would
    create a self-loop or a parallel edge are rejected and retried.

    Returns a new graph; the input is not mutated. Weights are dropped
    (degree-preserving nulls are defined on the binary topology).
    """
    rng = random.Random(seed)
    g = Graph(directed=graph.directed, weighted=False)
    g.add_nodes_from(graph.nodes())
    for u, v, _ in graph.edges():
        g.add_edge(u, v)

    if max_tries is None:
        max_tries = num_swaps * 10 + 100

    edges = [(u, v) for u, v, _ in g.edges()]
    if len(edges) < 2:
        return g

    swaps = 0
    tries = 0
    while swaps < num_swaps and tries < max_tries:
        tries += 1
        i = rng.randrange(len(edges))
        j = rng.randrange(len(edges))
        if i == j:
            continue
        a, b = edges[i]
        c, d = edges[j]

        if graph.directed:
            # a->b, c->d  =>  a->d, c->b
            if a == d or c == b:
                continue
            if g.has_edge(a, d) or g.has_edge(c, b):
                continue
            _remove_directed(g, a, b)
            _remove_directed(g, c, d)
            g.add_edge(a, d)
            g.add_edge(c, b)
            edges[i] = (a, d)
            edges[j] = (c, b)
        else:
            # {a,b}, {c,d}  =>  {a,c}, {b,d}
            nodes4 = {a, b, c, d}
            if len(nodes4) < 4:
                continue
            if g.has_edge(a, c) or g.has_edge(b, d):
                continue
            _remove_undirected(g, a, b)
            _remove_undirected(g, c, d)
            g.add_edge(a, c)
            g.add_edge(b, d)
            edges[i] = (a, c)
            edges[j] = (b, d)
        swaps += 1
    return g


def configuration_model(
    graph: Graph,
    swaps_per_edge: int = 10,
    seed: Optional[int] = None,
) -> Graph:
    """Degree-preserving randomised copy of ``graph``.

    Convenience wrapper that runs ``double_edge_swap`` with a swap budget
    scaled to the edge count (the usual ``~10 * |E|`` mixing rule of thumb).
    """
    num_swaps = swaps_per_edge * max(1, graph.num_edges)
    return double_edge_swap(graph, num_swaps=num_swaps, seed=seed)


def _remove_directed(g: Graph, u, v) -> None:
    del g._adj[u][v]
    del g._pred[v][u]


def _remove_undirected(g: Graph, u, v) -> None:
    del g._adj[u][v]
    del g._pred[v][u]
    del g._adj[v][u]
    del g._pred[u][v]
