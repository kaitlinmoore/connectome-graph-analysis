"""Traversal on tiny hand-verifiable graphs (path / cycle / star / components)."""

import pytest

from connectome_graph.graph import Graph
from connectome_graph.graph.traversal import (
    bfs_distances,
    connected_components,
    dijkstra,
)


def path_graph(n):
    g = Graph(directed=False)
    for i in range(n - 1):
        g.add_edge(i, i + 1)
    return g


def star_graph(k):
    g = Graph(directed=False)
    for i in range(1, k + 1):
        g.add_edge(0, i)
    return g


def cycle_graph(n):
    g = Graph(directed=False)
    for i in range(n):
        g.add_edge(i, (i + 1) % n)
    return g


def test_bfs_distances_path():
    g = path_graph(5)  # 0-1-2-3-4
    d = bfs_distances(g, 0)
    assert d == {0: 0, 1: 1, 2: 2, 3: 3, 4: 4}


def test_bfs_distances_star():
    g = star_graph(4)  # center 0, leaves 1..4
    d = bfs_distances(g, 0)
    assert d == {0: 0, 1: 1, 2: 1, 3: 1, 4: 1}
    # from a leaf: 1 hop to center, 2 hops to other leaves
    d2 = bfs_distances(g, 1)
    assert d2[0] == 1 and d2[2] == 2


def test_bfs_distances_cycle():
    g = cycle_graph(6)  # ring 0..5
    d = bfs_distances(g, 0)
    assert d == {0: 0, 1: 1, 2: 2, 3: 3, 4: 2, 5: 1}


def test_connected_components_disjoint():
    g = Graph(directed=False)
    g.add_edge("a", "b")
    g.add_edge("b", "c")
    g.add_edge("x", "y")
    g.add_node("lonely")
    comps = connected_components(g)
    sizes = sorted(len(c) for c in comps)
    assert sizes == [1, 2, 3]
    assert comps[0] == {"a", "b", "c"}  # largest first


def test_weakly_connected_for_directed():
    g = Graph(directed=True)
    g.add_edge("a", "b")  # one-way, but weakly connected
    comps = connected_components(g)
    assert len(comps) == 1 and comps[0] == {"a", "b"}


def test_dijkstra_weighted():
    g = Graph(directed=False, weighted=True)
    g.add_edge("a", "b", 1.0)
    g.add_edge("b", "c", 1.0)
    g.add_edge("a", "c", 5.0)  # longer direct edge
    dist = dijkstra(g, "a")
    assert dist["a"] == 0.0
    assert dist["b"] == 1.0
    assert dist["c"] == 2.0  # via b, not the weight-5 direct edge


def test_dijkstra_rejects_negative():
    g = Graph(directed=False, weighted=True)
    g.add_edge("a", "b", -1.0)
    with pytest.raises(ValueError):
        dijkstra(g, "a")
