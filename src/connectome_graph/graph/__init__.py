"""From-scratch graph algorithms. No third-party graph library is imported here.

Public surface re-exported for convenience so callers can do e.g.
``from connectome_graph.graph import Graph, betweenness_centrality``.
"""

from connectome_graph.graph.graph import Graph
from connectome_graph.graph.traversal import (
    bfs,
    bfs_distances,
    connected_components,
    dijkstra,
    shortest_path_lengths,
)
from connectome_graph.graph.distributions import (
    average_clustering,
    clustering_coefficient,
    degree_distribution,
    transitivity,
)
from connectome_graph.graph.centrality import (
    betweenness_centrality,
    degree_centrality,
    eigenvector_centrality,
    pagerank,
)
from connectome_graph.graph.smallworld import (
    average_shortest_path_length,
    characteristic_path_length,
    small_world_sigma,
)
from connectome_graph.graph.nulls import (
    configuration_model,
    double_edge_swap,
    erdos_renyi_gnm,
)

__all__ = [
    "Graph",
    # traversal
    "bfs",
    "bfs_distances",
    "connected_components",
    "dijkstra",
    "shortest_path_lengths",
    # distributions
    "degree_distribution",
    "clustering_coefficient",
    "average_clustering",
    "transitivity",
    # centrality
    "degree_centrality",
    "betweenness_centrality",
    "eigenvector_centrality",
    "pagerank",
    # small world
    "average_shortest_path_length",
    "characteristic_path_length",
    "small_world_sigma",
    # nulls
    "erdos_renyi_gnm",
    "double_edge_swap",
    "configuration_model",
]
