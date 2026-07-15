# connectome-graph-analysis

From-scratch graph algorithms applied to the C. elegans connectome, built as a
data-structures-and-algorithms project. Every graph algorithm is implemented by
hand and validated against NetworkX. **The connectome is the substrate; the
algorithms are the product.**

## Repo structure

```
connectome-graph-analysis/
├── CLAUDE.md
├── README.md
├── LICENSE                          # MIT
├── pyproject.toml                   # uv-managed, py3.11; numpy runtime, networkx dev-only
├── .gitignore                       # data/raw/, processed CSVs, heavy results
├── data/
│   ├── raw/                         # downloaded sources (gitignored, provenance below)
│   │   ├── celegans/
│   │   └── flywire/                 # Phase 2
│   └── processed/                   # harmonized edge list + node table (gitignored)
├── src/
│   └── connectome_graph/
│       ├── __init__.py
│       ├── io/
│       │   ├── celegans.py          # Cook 2019 reader -> edge records + graph variants
│       │   └── flywire.py           # Phase 2 stub: Codex static CSV loader
│       ├── graph/                   # ← FROM SCRATCH. No third-party graph lib imported here.
│       │   ├── graph.py             # Graph: adjacency-list core (+ dense matrix on demand)
│       │   ├── traversal.py         # BFS, weak connected components, Dijkstra
│       │   ├── distributions.py     # degree dist, clustering (triangle counting), transitivity
│       │   ├── centrality.py        # Brandes betweenness, eigenvector (power iter), PageRank
│       │   ├── smallworld.py        # char. path length, avg clustering, sigma vs ER null
│       │   ├── nulls.py             # ER G(n,m) + degree-preserving double-edge-swap
│       │   └── community.py         # OPTIONAL stretch stub: spectral / Louvain (from scratch)
│       ├── validation/
│       │   └── networkx_parity.py   # THE ONLY networkx import: cross-check every metric
│       └── analysis/
│           ├── ground_truth.py      # load command-interneuron set from reference/
│           └── hub_recovery.py      # PUNCHLINE: recovery + degree-preserving null test
├── scripts/                         # thin, ordered, reproducible entry points
│   ├── 00_fetch_celegans.py
│   ├── 01_build_graph.py
│   ├── 02_run_metrics.py
│   ├── 03_validate_vs_networkx.py
│   └── 04_hub_recovery.py
├── notebooks/                       # exploration only; never the source of truth
├── results/                         # figures + tables (gitignored heavy artifacts)
├── reference/
│   ├── functional_labels.md         # command-interneuron ground truth + citations + provenance
│   └── command_interneurons.csv     # machine-readable target set (one source of truth)
└── tests/
    ├── test_traversal.py            # path/cycle/star/components/dijkstra closed forms
    ├── test_centrality.py           # Brandes/eigenvector/pagerank closed forms
    ├── test_nulls.py                # degree sequence preserved; ER edge count exact
    └── test_parity.py               # networkx agreement, exact where exact, tol where iterative
```

## TL;DR
> **[PENDING — fill after Stage 4 on real Cook-2019 data.]** The analysis
> machinery is built, tested, and validated against NetworkX, but no headline
> result is claimed until it has been run on the real connectome, not the
> synthetic fixture used for smoke-testing. The one-line result will read like
> *"Betweenness recovers the command interneurons beyond a degree-preserving
> null; PageRank and eigenvector do not"* **or** *"raw degree explains
> command-interneuron salience; higher-order centrality adds nothing"* —
> whichever the data says. A negative result is reported plainly.

## Question
Which centrality measure best recovers the independently-known *C. elegans*
command interneurons (AVA, AVB, AVD, AVE, PVC, ...), and does any higher-order
centrality recover them **beyond what raw degree already explains**?

The "beyond degree" clause is load-bearing and non-circular. Command
interneurons are already known to be high-degree, so "hubs recover them" is
expected and weak on its own. The real test: does the *specific wiring*
concentrate betweenness / eigenvector / PageRank on the command set more than a
**degree-preserving null** (configuration model with the same degree sequence)
would? That isolates structure-beyond-degree. If the answer is "no, degree
explains it all," that is a real, honest, reportable finding.

This is **validation-by-triangulation**: graph-theoretic salience checked
against functional importance from an *independent* source (electrophysiology /
ablation literature), not against anything derived from the graph itself.

## What's from scratch (and what isn't)
- **From scratch** (`src/connectome_graph/graph/`): the `Graph` data structure,
  BFS, connected components, Dijkstra, degree distributions, clustering /
  transitivity via triangle counting, Brandes betweenness, eigenvector
  centrality (power iteration), PageRank, Erdős–Rényi and degree-preserving
  configuration-model nulls, and small-world sigma.
- **Not from scratch, by design**: NetworkX (validation/cross-check only, and
  imported in exactly one file), numpy (dense linear algebra only — not a graph
  library), CSV parsing / data I/O, and plotting.

> **The one rule.** No third-party graph library (NetworkX, igraph, graph-tool,
> `scipy.sparse.csgraph`) may be imported anywhere under `src/` except
> `validation/networkx_parity.py`. If a task tempts you to "just use
> `nx.betweenness_centrality`" inside `src/`, that is the failure mode this repo
> exists to avoid. Stop and implement it.

## Data
- **Source**: Cook et al. 2019 (*Nature* 571:63–71); download via the OpenWorm
  ConnectomeToolbox mirror into `data/raw/celegans/` (gitignored). `scripts/00`
  harmonizes it to two tidy CSVs under `data/processed/`:
  `celegans_edges.csv` (`source,target,type,synapses`) and `celegans_nodes.csv`
  (`neuron,cell_class,neurotransmitter`).
- **Provenance (read before trusting labels)**: neuron identities follow **Cook
  2019 / WormAtlas**, not older White-1986-derived edge lists. Cook 2019
  corrected identity errors including the **PVCL/PVCR switch** and the
  **DVB/PVT crossing**; PVC is a command-interneuron target, so the convention
  is load-bearing. Relabel any White-1986 edge list before analysis.
- **Command-interneuron ground truth**: `reference/functional_labels.md`
  (prose + citations) and `reference/command_interneurons.csv` (the single
  machine-readable source consumed by the analysis).

## Methods
- **Graph representation**: adjacency-list core (`dict[node, dict[node,
  weight]]`) with a predecessor map so `in_degree` and the backward passes of
  Brandes/PageRank are O(neighbours), plus a dense adjacency matrix
  materialized on demand for the power-iteration metrics.
- **Graph construction is a modeling decision**: `io.build_variants` never
  collapses to one graph. It builds the family — combined / chemical-only /
  gap-only × directed/undirected × binary/synapse-weighted — and the recovery
  result is checked for robustness across all of them. Chemical synapses are
  directed; gap junctions are symmetric (undirected, or both orientations in a
  directed graph).
- **Algorithms** (one line each): BFS — hop distances via a queue; Dijkstra —
  binary-heap shortest paths; clustering — triangle counting on the undirected
  projection; betweenness — Brandes (BFS or Dijkstra SSSP + dependency
  accumulation), O(VE) / O(VE + V²log V); eigenvector — power iteration,
  L2-renormalized; PageRank — damped power iteration with uniform dangling
  redistribution.
- **Null models**: Erdős–Rényi G(n, m) for small-world sigma; degree-preserving
  **double-edge-swap** configuration model for the beyond-degree test.
- **Recovery metric**: precision@k and mean rank of the command set, plus a
  right-tailed empirical p-value / z-score comparing the metric's concentration
  on the command set in the real graph vs. the degree-preserving null ensemble.

## Validation
Every metric is validated against NetworkX on the **identical** graph, in the
one sanctioned file `validation/networkx_parity.py`:

| Metric | Agreement | Notes |
|--------|-----------|-------|
| degree, BFS distances, connected components | **exact** | any mismatch is a bug |
| clustering, average clustering | **exact** (tol 1e-12) | undirected projection |
| betweenness (Brandes) | tolerance | matches nx `_rescale` exactly; observed ~0 diff |
| eigenvector (power iter) | tolerance 1e-6 | normalization/convergence differences |
| PageRank | tolerance 1e-6 | uniform dangling + personalization |

Parity with NetworkX is **triangulation, not a crutch**: unit tests also pin
every algorithm to closed-form answers on tiny graphs (path / cycle / star /
complete). `scripts/03` doubles as a CI gate and exits non-zero on any failure.

## Results
> **[PENDING real data.]** `results/metrics.csv` and `results/hub_recovery.csv`
> are produced by Stages 02 and 04. Populate this section from the real run:
> - Centrality-vs-function recovery, per graph variant (precision@k, mean rank).
> - Beyond-degree null test verdict per metric per variant (the `beyond_degree`
>   column) — reported whichever way it falls.
> - Robustness across chemical / gap / combined and directed / weighted choices.
> - Small-world metrics (C, L, sigma) vs. nulls.
> - [Optional] community / spectral structure.

## Limitations & honest framing
- The interpretability bridge is the weakest link: structural graph salience is
  a **structural analogy** for functional importance, not a demonstration of it.
- Command interneurons are a priori high-degree; the degree-preserving null test
  is what makes any positive claim non-circular, and **it may come back
  negative** — which is reported, not buried.
- Single organism, single reconstruction. *C. elegans* is small enough that some
  metrics are near-saturated (short paths, dense hub connectivity), so effect
  sizes should be read with the null distribution, not in isolation.

## Reproduce
```bash
uv venv --python 3.11
uv pip install -e ".[dev]"
uv run pytest                              # 26 tests: closed-form + networkx parity
uv run python scripts/00_fetch_celegans.py # fetch + harmonize Cook 2019
uv run python scripts/01_build_graph.py    # build graph variants, report structure
uv run python scripts/02_run_metrics.py    # centralities + small-world -> results/
uv run python scripts/03_validate_vs_networkx.py  # parity gate (exits non-zero on fail)
uv run python scripts/04_hub_recovery.py   # PUNCHLINE: recovery + beyond-degree null
```
Scripts 00 → 04 are ordered and reproducible; notebooks are exploration only.

## Phase 2 (not yet built)
FlyWire whole-brain (~140k neurons) via the Codex static CSV export. Out of
scope until v1's parity + recovery result are committed (CLAUDE.md). Scaling
notes: stream the Codex `connections.csv` rather than materialize it, and
replace the dense-matrix centrality paths with a sparse formulation.
