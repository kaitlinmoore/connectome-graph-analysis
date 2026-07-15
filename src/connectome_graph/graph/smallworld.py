"""Small-world metrics, from scratch.

Characteristic path length ``L`` and average clustering ``C``, plus the
Watts–Strogatz small-world coefficient ``sigma = (C/C_rand) / (L/L_rand)``
measured against an Erdős–Rényi null of matched size. C. elegans is the
canonical small-world nervous system; this is where we reproduce that.

Path length is computed over the largest connected component so that
unreachable pairs (finite in any real, not-fully-connected connectome) do not
send ``L`` to infinity. That restriction is stated explicitly rather than
silently dropping pairs.
"""

from __future__ import annotations

from typing import Optional

from connectome_graph.graph.distributions import average_clustering
from connectome_graph.graph.graph import Graph
from connectome_graph.graph.nulls import erdos_renyi_gnm
from connectome_graph.graph.traversal import bfs_distances, connected_components


def average_shortest_path_length(
    graph: Graph, on_giant_component: bool = True
) -> float:
    """Mean shortest-path (hop) distance over ordered reachable pairs.

    If ``on_giant_component`` (default) the average is taken within the largest
    connected component; otherwise every reachable ordered pair in the graph
    contributes and disconnected pairs are ignored.
    """
    if on_giant_component:
        comps = connected_components(graph)
        if not comps:
            return 0.0
        giant = comps[0]
        node_set = giant
    else:
        node_set = set(graph.nodes())

    total = 0.0
    count = 0
    for s in node_set:
        dist = bfs_distances(graph, s)
        for target, d in dist.items():
            if target == s or target not in node_set:
                continue
            total += d
            count += 1
    if count == 0:
        return 0.0
    return total / count


# Watts–Strogatz "characteristic path length" is exactly this quantity.
characteristic_path_length = average_shortest_path_length


def small_world_sigma(
    graph: Graph, num_nulls: int = 10, seed: Optional[int] = None
) -> dict:
    """Small-world coefficient sigma against an ER null of matched (n, m).

    Returns a dict with the observed ``C`` and ``L``, the null means
    ``C_rand`` / ``L_rand``, and ``sigma``. sigma >> 1 indicates small-world
    organisation (high clustering, short paths).
    """
    C = average_clustering(graph)
    L = average_shortest_path_length(graph, on_giant_component=True)

    n = graph.num_nodes
    m = graph.num_edges
    c_rand_vals = []
    l_rand_vals = []
    for i in range(num_nulls):
        null_seed = None if seed is None else seed + i
        null = erdos_renyi_gnm(
            n, m, directed=graph.directed, seed=null_seed, nodes=graph.nodes()
        )
        c_rand_vals.append(average_clustering(null))
        l_rand_vals.append(average_shortest_path_length(null, on_giant_component=True))

    c_rand = sum(c_rand_vals) / len(c_rand_vals) if c_rand_vals else 0.0
    l_rand = sum(l_rand_vals) / len(l_rand_vals) if l_rand_vals else 0.0

    sigma = 0.0
    if c_rand > 0 and l_rand > 0 and L > 0:
        sigma = (C / c_rand) / (L / l_rand)

    return {
        "C": C,
        "L": L,
        "C_rand": c_rand,
        "L_rand": l_rand,
        "sigma": sigma,
        "num_nulls": num_nulls,
    }
