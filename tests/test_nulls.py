"""Null models: degree sequence preserved under swaps; ER edge count exact."""

from collections import Counter

from connectome_graph.graph import Graph
from connectome_graph.graph.nulls import (
    configuration_model,
    double_edge_swap,
    erdos_renyi_gnm,
)


def random_ish_graph(directed=False):
    g = Graph(directed=directed)
    edges = [
        ("a", "b"), ("a", "c"), ("b", "c"), ("b", "d"),
        ("c", "e"), ("d", "e"), ("e", "f"), ("a", "f"),
    ]
    for u, v in edges:
        g.add_edge(u, v)
    return g


def degree_multiset(g):
    if g.directed:
        return Counter({n: (g.in_degree(n), g.out_degree(n)) for n in g.nodes()})
    return Counter({n: g.degree(n) for n in g.nodes()})


def test_double_edge_swap_preserves_undirected_degree():
    g = random_ish_graph(directed=False)
    before = {n: g.degree(n) for n in g.nodes()}
    swapped = double_edge_swap(g, num_swaps=50, seed=123)
    after = {n: swapped.degree(n) for n in swapped.nodes()}
    assert before == after


def test_double_edge_swap_preserves_directed_in_out_degree():
    g = random_ish_graph(directed=True)
    before_in = {n: g.in_degree(n) for n in g.nodes()}
    before_out = {n: g.out_degree(n) for n in g.nodes()}
    swapped = double_edge_swap(g, num_swaps=50, seed=7)
    assert before_in == {n: swapped.in_degree(n) for n in swapped.nodes()}
    assert before_out == {n: swapped.out_degree(n) for n in swapped.nodes()}


def test_swap_does_not_change_edge_count():
    g = random_ish_graph()
    m = g.num_edges
    swapped = double_edge_swap(g, num_swaps=100, seed=1)
    assert swapped.num_edges == m


def test_swap_produces_no_self_loops_or_parallel_edges():
    g = random_ish_graph()
    swapped = double_edge_swap(g, num_swaps=100, seed=2)
    seen = set()
    for u, v, _ in swapped.edges():
        assert u != v, "self-loop introduced"
        key = frozenset((u, v))
        assert key not in seen, "parallel edge introduced"
        seen.add(key)


def test_configuration_model_preserves_degree_sequence():
    g = random_ish_graph()
    before = sorted(g.degree(n) for n in g.nodes())
    null = configuration_model(g, seed=99)
    after = sorted(null.degree(n) for n in null.nodes())
    assert before == after


def test_erdos_renyi_edge_count_exact():
    g = erdos_renyi_gnm(n=10, m=15, seed=42)
    assert g.num_nodes == 10
    assert g.num_edges == 15


def test_erdos_renyi_directed_edge_count():
    g = erdos_renyi_gnm(n=8, m=20, directed=True, seed=5)
    assert g.num_edges == 20
