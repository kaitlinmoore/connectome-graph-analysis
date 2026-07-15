"""Data I/O: read published connectome edge lists into our :class:`Graph`.

I/O is explicitly *not* from-scratch — parsing CSVs is not the product. What
matters here is provenance discipline (which reconstruction, which neuron-ID
convention) and building the several graph variants the analysis compares.
"""

from connectome_graph.io.celegans import (
    GraphVariant,
    build_variants,
    load_celegans,
    load_node_table,
)

__all__ = ["GraphVariant", "load_celegans", "load_node_table", "build_variants"]
