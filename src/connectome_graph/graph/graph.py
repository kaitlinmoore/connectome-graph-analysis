"""From-scratch graph data structure.

Backs the entire library. No third-party graph package is imported here, or
anywhere else under ``src/`` (see CLAUDE.md). We keep an adjacency-list view
(``dict[node, dict[node, weight]]``) for fast, sparse-friendly neighbour
iteration, and can materialise a dense adjacency matrix on demand for the
linear-algebra-flavoured metrics (eigenvector centrality, PageRank).

Design decisions worth knowing:

* Nodes are any hashable (we use neuron-name strings such as ``"AVAL"``).
* For a directed graph we also maintain a predecessor map so ``in_degree`` and
  Brandes/PageRank backward passes are O(1)-neighbour rather than O(V).
* ``add_edge`` on a *weighted* graph **accumulates** weight for a repeated
  ``(u, v)`` pair. Connectome edge lists frequently emit one row per synaptic
  contact, and the natural weight is the summed synapse count. On a *binary*
  (unweighted) graph a repeated edge is idempotent (stays weight ``1.0``).
"""

from __future__ import annotations

from typing import Dict, Hashable, Iterable, Iterator, List, Tuple

Node = Hashable
Edge = Tuple[Node, Node, float]


class Graph:
    """A directed-or-undirected, weighted-or-binary graph."""

    def __init__(self, directed: bool = False, weighted: bool = False) -> None:
        self.directed = directed
        self.weighted = weighted
        # _adj[u][v] = weight of edge u->v (both directions stored if undirected)
        self._adj: Dict[Node, Dict[Node, float]] = {}
        # _pred[v][u] = weight of edge u->v; mirrors _adj for undirected graphs
        self._pred: Dict[Node, Dict[Node, float]] = {}

    # ------------------------------------------------------------------ #
    # construction
    # ------------------------------------------------------------------ #
    def add_node(self, n: Node) -> Node:
        if n not in self._adj:
            self._adj[n] = {}
            self._pred[n] = {}
        return n

    def add_nodes_from(self, nodes: Iterable[Node]) -> None:
        for n in nodes:
            self.add_node(n)

    def add_edge(self, u: Node, v: Node, weight: float = 1.0) -> Edge:
        """Add edge ``u -> v`` (and ``v -> u`` if undirected).

        On a weighted graph a repeated pair accumulates; on a binary graph the
        stored weight is always ``1.0``.
        """
        self.add_node(u)
        self.add_node(v)
        if self.weighted:
            w = self._adj[u].get(v, 0.0) + float(weight)
        else:
            w = 1.0
        self._adj[u][v] = w
        self._pred[v][u] = w
        if not self.directed:
            self._adj[v][u] = w
            self._pred[u][v] = w
        return (u, v, w)

    def add_edges_from(self, edges: Iterable[Iterable]) -> None:
        for e in edges:
            e = tuple(e)
            if len(e) == 3:
                self.add_edge(e[0], e[1], e[2])
            else:
                self.add_edge(e[0], e[1])

    # ------------------------------------------------------------------ #
    # queries
    # ------------------------------------------------------------------ #
    def has_node(self, n: Node) -> bool:
        return n in self._adj

    def has_edge(self, u: Node, v: Node) -> bool:
        return u in self._adj and v in self._adj[u]

    def nodes(self) -> List[Node]:
        return list(self._adj.keys())

    @property
    def num_nodes(self) -> int:
        return len(self._adj)

    def edges(self) -> Iterator[Edge]:
        """Yield ``(u, v, weight)``. Undirected edges are yielded once."""
        if self.directed:
            for u, nbrs in self._adj.items():
                for v, w in nbrs.items():
                    yield (u, v, w)
            return
        seen: set = set()
        for u, nbrs in self._adj.items():
            for v, w in nbrs.items():
                key = (u, v) if u == v else frozenset((u, v))
                if key in seen:
                    continue
                seen.add(key)
                yield (u, v, w)

    @property
    def num_edges(self) -> int:
        return sum(1 for _ in self.edges())

    def neighbors(self, u: Node) -> List[Node]:
        """Successors (out-neighbours). Alias kept close to NetworkX naming."""
        return list(self._adj[u].keys())

    successors = neighbors

    def predecessors(self, u: Node) -> List[Node]:
        return list(self._pred[u].keys())

    def edge_weight(self, u: Node, v: Node) -> float:
        return self._adj[u][v]

    def adjacency(self, u: Node) -> Dict[Node, float]:
        """Read-only-ish view of ``{successor: weight}`` for ``u``."""
        return self._adj[u]

    # ------------------------------------------------------------------ #
    # degrees
    # ------------------------------------------------------------------ #
    def out_degree(self, u: Node) -> int:
        return len(self._adj[u])

    def in_degree(self, u: Node) -> int:
        return len(self._pred[u]) if self.directed else len(self._adj[u])

    def degree(self, u: Node) -> int:
        """Total degree. For directed graphs this is in + out."""
        if self.directed:
            return len(self._adj[u]) + len(self._pred[u])
        return len(self._adj[u])

    def weighted_degree(self, u: Node) -> float:
        out_w = sum(self._adj[u].values())
        if not self.directed:
            return out_w
        return out_w + sum(self._pred[u].values())

    def degree_sequence(self) -> List[int]:
        return [self.degree(n) for n in self._adj]

    # ------------------------------------------------------------------ #
    # transforms
    # ------------------------------------------------------------------ #
    def copy(self) -> "Graph":
        g = Graph(directed=self.directed, weighted=self.weighted)
        for n in self._adj:
            g.add_node(n)
        for u, v, w in self.edges():
            g.add_edge(u, v, w)
        return g

    def to_undirected(self, reduce: str = "sum") -> "Graph":
        """Project onto an undirected graph.

        ``reduce`` controls how reciprocal weights ``u->v`` and ``v->u``
        combine into the single undirected weight: ``"sum"`` (default),
        ``"max"``, or ``"first"`` (keep whichever direction is seen first).
        For a binary graph ``reduce`` is irrelevant (weight is always 1.0).
        """
        # Accumulate symmetric weights first, then build, so the combine rule
        # is applied exactly once per unordered pair.
        combined: Dict[frozenset, float] = {}
        for u, nbrs in self._adj.items():
            for v, w in nbrs.items():
                key = frozenset((u, v))
                if key not in combined:
                    combined[key] = w
                elif reduce == "max":
                    combined[key] = max(combined[key], w)
                elif reduce == "first":
                    pass
                else:  # sum
                    combined[key] += w

        g = Graph(directed=False, weighted=self.weighted)
        g.add_nodes_from(self._adj.keys())
        for key, w in combined.items():
            pair = tuple(key)
            if len(pair) == 1:  # self-loop
                g.add_edge(pair[0], pair[0], w)
            else:
                g.add_edge(pair[0], pair[1], w)
        return g

    def to_matrix(self) -> Tuple[List[List[float]], List[Node]]:
        """Dense adjacency matrix ``M[i][j] = weight(node_i -> node_j)``.

        Returns the matrix (list of lists) and the row/column node ordering.
        Kept numpy-free here; callers that want linear algebra wrap it in an
        ``np.asarray`` (see ``centrality.py``).
        """
        nodes = self.nodes()
        index = {n: i for i, n in enumerate(nodes)}
        n = len(nodes)
        M = [[0.0] * n for _ in range(n)]
        for u, nbrs in self._adj.items():
            iu = index[u]
            for v, w in nbrs.items():
                M[iu][index[v]] = w
        return M, nodes

    def __contains__(self, n: Node) -> bool:
        return n in self._adj

    def __len__(self) -> int:
        return len(self._adj)

    def __repr__(self) -> str:
        kind = "Directed" if self.directed else "Undirected"
        w = "weighted" if self.weighted else "binary"
        return f"<{kind} {w} Graph: {self.num_nodes} nodes, {self.num_edges} edges>"
