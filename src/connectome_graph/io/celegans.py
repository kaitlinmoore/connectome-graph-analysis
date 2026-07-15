"""Read the C. elegans connectome into :class:`Graph` variants.

Provenance (read CLAUDE.md before trusting labels): neuron identities and type
labels follow **Cook et al. 2019 / WormAtlas**, not older White-1986-derived
edge lists. Cook 2019 corrected identity errors including the PVCL/PVCR switch
and the DVB/PVT crossing. Because PVC is a command-interneuron target, the
label convention is load-bearing — keep every download and any relabelling
step recorded in the README and ``reference/functional_labels.md``.

Expected on-disk schema
-----------------------
``scripts/00_fetch_celegans.py`` harmonises the raw Cook 2019 supplement into
two tidy CSVs under ``data/processed/`` (gitignored):

``celegans_edges.csv``::

    source,target,type,synapses
    AVAL,AVBL,chemical,5
    AVAL,PVCL,electrical,2
    ...

* ``type`` is ``chemical`` (directed) or ``electrical`` (gap junction,
  symmetric/undirected).
* ``synapses`` is the integer contact count used as edge weight.

``celegans_nodes.csv`` (optional but recommended)::

    neuron,cell_class,neurotransmitter
    AVAL,interneuron,glutamate
    ...

Graph construction is a modelling decision (CLAUDE.md): this module never
silently collapses to one graph. ``build_variants`` returns the full family —
combined / chemical-only / gap-only × directed/undirected × binary/weighted —
so the recovery result can be checked for robustness across all of them.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from connectome_graph.graph.graph import Graph

CHEMICAL = "chemical"
ELECTRICAL = "electrical"
_ELECTRICAL_ALIASES = {"electrical", "gap", "gap_junction", "gapjunction", "ej"}
_CHEMICAL_ALIASES = {"chemical", "synapse", "chem", "cs"}


@dataclass(frozen=True)
class EdgeRecord:
    source: str
    target: str
    kind: str  # normalised to CHEMICAL or ELECTRICAL
    synapses: float


def _normalise_kind(raw: str) -> str:
    r = raw.strip().lower()
    if r in _ELECTRICAL_ALIASES:
        return ELECTRICAL
    if r in _CHEMICAL_ALIASES:
        return CHEMICAL
    raise ValueError(f"unrecognised edge type {raw!r}")


def read_edge_records(path: str | Path) -> List[EdgeRecord]:
    """Parse ``celegans_edges.csv`` into normalised :class:`EdgeRecord`s."""
    path = Path(path)
    records: List[EdgeRecord] = []
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        required = {"source", "target", "type", "synapses"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"{path} missing columns: {sorted(missing)}")
        for row in reader:
            records.append(
                EdgeRecord(
                    source=row["source"].strip(),
                    target=row["target"].strip(),
                    kind=_normalise_kind(row["type"]),
                    synapses=float(row["synapses"]),
                )
            )
    return records


def load_node_table(path: str | Path) -> Dict[str, Dict[str, str]]:
    """Parse ``celegans_nodes.csv`` into ``{neuron: {attr: value}}``."""
    path = Path(path)
    table: Dict[str, Dict[str, str]] = {}
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            name = (row.get("neuron") or "").strip()
            if not name:
                continue
            table[name] = {k: v for k, v in row.items() if k != "neuron"}
    return table


def build_graph_from_records(
    records: Iterable[EdgeRecord],
    include: str = "combined",
    directed: bool = True,
    weighted: bool = True,
    nodes: Optional[Iterable[str]] = None,
) -> Graph:
    """Assemble one :class:`Graph` from edge records.

    ``include`` ∈ {``"combined"``, ``"chemical"``, ``"electrical"``}.

    Electrical (gap-junction) synapses are physically symmetric. When the graph
    is directed we insert both orientations for electrical edges so their
    reciprocity is faithful; chemical edges keep their single orientation. When
    the graph is undirected everything collapses naturally.
    """
    g = Graph(directed=directed, weighted=weighted)
    if nodes is not None:
        g.add_nodes_from(nodes)

    for rec in records:
        if include == "chemical" and rec.kind != CHEMICAL:
            continue
        if include == "electrical" and rec.kind != ELECTRICAL:
            continue
        w = rec.synapses if weighted else 1.0
        g.add_edge(rec.source, rec.target, w)
        if directed and rec.kind == ELECTRICAL:
            g.add_edge(rec.target, rec.source, w)
    return g


@dataclass(frozen=True)
class GraphVariant:
    """A named connectome graph plus the modelling choices that produced it."""

    name: str
    graph: Graph
    include: str
    directed: bool
    weighted: bool


def build_variants(
    records: Iterable[EdgeRecord],
    nodes: Optional[Iterable[str]] = None,
) -> List[GraphVariant]:
    """Build the standard family of graph variants for robustness checks.

    Chemical synapses are directed; gap junctions are undirected; the combined
    graph is offered both directed (chemical direction kept, gaps symmetrised)
    and undirected. Each is built binary and synapse-weighted.
    """
    records = list(records)
    node_list = list(nodes) if nodes is not None else None
    specs: List[Tuple[str, str, bool, bool]] = [
        # (name, include, directed, weighted)
        ("combined_directed_weighted", "combined", True, True),
        ("combined_directed_binary", "combined", True, False),
        ("combined_undirected_weighted", "combined", False, True),
        ("chemical_directed_weighted", "chemical", True, True),
        ("chemical_directed_binary", "chemical", True, False),
        ("gap_undirected_weighted", "electrical", False, True),
        ("gap_undirected_binary", "electrical", False, False),
    ]
    variants: List[GraphVariant] = []
    for name, include, directed, weighted in specs:
        g = build_graph_from_records(
            records,
            include=include,
            directed=directed,
            weighted=weighted,
            nodes=node_list,
        )
        variants.append(GraphVariant(name, g, include, directed, weighted))
    return variants


def load_celegans(
    edges_path: str | Path,
    include: str = "combined",
    directed: bool = True,
    weighted: bool = True,
    node_table_path: Optional[str | Path] = None,
) -> Graph:
    """One-call loader: read the edge CSV and return a single graph variant.

    Pass ``node_table_path`` to seed isolated neurons (those present in the
    node table but with no edges of the selected type).
    """
    records = read_edge_records(edges_path)
    nodes = None
    if node_table_path is not None:
        nodes = list(load_node_table(node_table_path).keys())
    return build_graph_from_records(
        records, include=include, directed=directed, weighted=weighted, nodes=nodes
    )
