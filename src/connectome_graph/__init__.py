"""connectome_graph — from-scratch graph algorithms for biological connectomes.

The connectome is the substrate; the algorithms are the product. Every graph
algorithm under ``connectome_graph.graph`` is implemented by hand. NetworkX is
imported in exactly one place — ``connectome_graph.validation.networkx_parity``
— whose only job is to cross-check the hand-rolled code. See CLAUDE.md.
"""

from connectome_graph.graph.graph import Graph

__all__ = ["Graph"]
__version__ = "0.1.0"
