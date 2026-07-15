"""NetworkX parity: exact where exact, tolerance where iterative.

Skipped automatically if networkx is not installed (it is a dev-only dep). The
parity module is the one sanctioned home of `import networkx` in the tree.
"""

import pytest

nx = pytest.importorskip("networkx")

from connectome_graph.graph import Graph
from connectome_graph.validation.networkx_parity import parity_report, to_networkx


def build_test_graph(directed):
    """A small graph with hubs and a triangle — exercises every metric."""
    g = Graph(directed=directed, weighted=True)
    edges = [
        ("h1", "a", 3), ("h1", "b", 1), ("h1", "c", 2), ("h1", "d", 1),
        ("a", "b", 2), ("b", "c", 1), ("c", "a", 1),  # triangle a-b-c
        ("h2", "d", 2), ("h2", "e", 1), ("h2", "h1", 4),
        ("d", "e", 1), ("e", "f", 2), ("f", "h2", 1),
    ]
    for u, v, w in edges:
        g.add_edge(u, v, w)
    return g


@pytest.mark.parametrize("directed", [False, True])
def test_full_parity_suite(directed):
    g = build_test_graph(directed)
    results = parity_report(g)
    failures = [r for r in results if not r.agree]
    assert not failures, "parity failures:\n" + "\n".join(str(r) for r in failures)


def test_to_networkx_roundtrip_counts():
    g = build_test_graph(directed=True)
    G = to_networkx(g)
    assert G.number_of_nodes() == g.num_nodes
    assert G.number_of_edges() == g.num_edges


def test_exact_metrics_are_flagged_exact():
    g = build_test_graph(directed=False)
    results = {r.metric: r for r in parity_report(g)}
    for exact_metric in ("degree", "bfs_distances", "connected_components"):
        assert results[exact_metric].kind == "exact"
        assert results[exact_metric].agree
        assert results[exact_metric].max_abs_diff == 0.0
