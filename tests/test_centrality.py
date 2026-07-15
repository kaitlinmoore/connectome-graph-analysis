"""Centrality on graphs with closed-form answers.

Parity with NetworkX is triangulation (see test_parity.py); these pin the
algorithms to answers derivable by hand, so a bug can't hide behind "both
implementations agree because both are wrong."
"""

import math

import pytest

from connectome_graph.graph import Graph
from connectome_graph.graph.centrality import (
    betweenness_centrality,
    degree_centrality,
    eigenvector_centrality,
    pagerank,
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


def complete_graph(n):
    g = Graph(directed=False)
    for i in range(n):
        for j in range(i + 1, n):
            g.add_edge(i, j)
    return g


def cycle_graph(n):
    g = Graph(directed=False)
    for i in range(n):
        g.add_edge(i, (i + 1) % n)
    return g


# --- betweenness closed forms ---
def test_betweenness_path_middle_node():
    # P3: 0-1-2. Node 1 lies on the single shortest path between 0 and 2.
    g = path_graph(3)
    b = betweenness_centrality(g, normalized=False)
    assert b[1] == pytest.approx(1.0)
    assert b[0] == pytest.approx(0.0)
    assert b[2] == pytest.approx(0.0)


def test_betweenness_star_center():
    # Star with 3 leaves: center is on all C(3,2)=3 leaf-leaf shortest paths.
    g = star_graph(3)
    b = betweenness_centrality(g, normalized=False)
    assert b[0] == pytest.approx(3.0)
    for leaf in (1, 2, 3):
        assert b[leaf] == pytest.approx(0.0)


def test_betweenness_complete_all_zero():
    # In K_n every pair is directly connected, so no node is an intermediary.
    g = complete_graph(4)
    b = betweenness_centrality(g, normalized=False)
    for v in g.nodes():
        assert b[v] == pytest.approx(0.0)


# --- eigenvector closed forms ---
def test_eigenvector_complete_uniform():
    g = complete_graph(5)
    e = eigenvector_centrality(g, max_iter=5000, tol=1e-10)
    vals = list(e.values())
    assert all(v == pytest.approx(vals[0], abs=1e-6) for v in vals)
    # L2-normalised uniform vector on n nodes -> each = 1/sqrt(n)
    assert vals[0] == pytest.approx(1 / math.sqrt(5), abs=1e-6)


def test_eigenvector_cycle_uniform():
    g = cycle_graph(6)  # 2-regular -> uniform eigenvector
    e = eigenvector_centrality(g, max_iter=5000, tol=1e-10)
    vals = list(e.values())
    assert all(v == pytest.approx(vals[0], abs=1e-6) for v in vals)


# --- pagerank closed forms ---
def test_pagerank_sums_to_one():
    g = complete_graph(4)
    pr = pagerank(g, alpha=0.85)
    assert sum(pr.values()) == pytest.approx(1.0, abs=1e-9)


def test_pagerank_regular_graph_uniform():
    g = cycle_graph(5)  # regular -> uniform stationary distribution
    pr = pagerank(g, alpha=0.85)
    for v in g.nodes():
        assert pr[v] == pytest.approx(1 / 5, abs=1e-6)


# --- degree ---
def test_degree_centrality_star():
    g = star_graph(4)  # center degree 4, leaves degree 1, n=5
    d = degree_centrality(g)
    assert d[0] == pytest.approx(4 / 4)  # (n-1)=4 normaliser
    assert d[1] == pytest.approx(1 / 4)
