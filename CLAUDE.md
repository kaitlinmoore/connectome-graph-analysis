# CLAUDE.md — connectome-graph-analysis

## What this repo is
A from-scratch graph-algorithms library applied to biological connectomes.
The connectome is the substrate; the algorithms are the product.

Sibling repo: sparse-coding-v1.

## The one rule that defines this repo
Algorithms in `src/connectome_graph/graph/` are implemented FROM SCRATCH.
NetworkX (or igraph, graph-tool, scipy.sparse.csgraph) MUST NOT be imported
anywhere under `src/`. NetworkX appears ONLY in
`src/connectome_graph/validation/networkx_parity.py`, whose sole job is to
cross-check the hand-rolled implementations. If a task tempts you to "just use
nx.betweenness_centrality" inside src/, that is the failure mode this repo exists
to avoid. Stop and implement it.

## Headline question
Which centrality measure best recovers the independently-known C. elegans command
interneurons (AVA, AVB, AVD, AVE, PVC, ...), and does any higher-order centrality
recover them BEYOND what raw degree already explains?

The "beyond degree" clause is load-bearing and non-circular:
- Command interneurons are already known to be high-degree. So "hubs recover them"
  is expected and weak on its own.
- The real test: does the SPECIFIC wiring concentrate betweenness / eigenvector /
  PageRank on the command set more than a degree-preserving null (configuration
  model with the same degree sequence) would? That isolates structure-beyond-degree.
- If the answer is "no, degree explains it all," that is a real, honest, reportable
  finding — report it plainly. Do not fish for a positive result.

This is validation-by-triangulation: graph-theoretic salience checked against
functional importance from an INDEPENDENT source (electrophysiology / ablation
literature), not against anything derived from the graph itself.

## Ground-truth provenance (read before trusting labels)
Command-interneuron identities and neuron-type labels come from Cook et al. 2019 /
WormAtlas — NOT from older White-1986-derived edge lists. Cook 2019 corrected
identity errors including a PVCL/PVCR switch and a DVB/PVT crossing; PVC is a target
neuron, so label provenance matters. Record every label's source in
reference/functional_labels.md with a citation.

## Graph construction is a modeling decision
Do not silently collapse to one graph. Build and be able to justify:
- combined vs. chemical-synapse-only vs. gap-junction-only
- directed (chemical) vs. undirected (gap junction)
- binary vs. synapse-count-weighted
The recovery result must be checked for robustness across these. Report where it
holds and where it breaks.

## Validation discipline
Every metric is validated against NetworkX on the identical graph:
- Exact agreement expected: BFS distances, degree, clustering coefficient,
  connected components.
- Tolerance-based agreement (document the tolerance and why): eigenvector,
  PageRank, betweenness — implementation/normalization differences are expected;
  large disagreement is a bug in the hand-rolled code until proven otherwise.
Unit tests also check algorithms against tiny graphs with closed-form answers
(path, cycle, star, complete) — parity with NetworkX is triangulation, not a crutch.

## Environment & standard
- WSL2 / Ubuntu, uv for deps, Python 3.11
- MIT license, kebab-case naming, copy-not-import between repos
- scripts/ are thin ordered entry points; notebooks/ are exploration only and never
  the source of truth
- Data in data/raw/ is gitignored; provenance and download steps live in the README

## Phase scope
v1 = C. elegans only. FlyWire (Codex static CSV, ~140k neurons) is Phase 2 and is
out of scope until v1's parity + recovery result is committed.