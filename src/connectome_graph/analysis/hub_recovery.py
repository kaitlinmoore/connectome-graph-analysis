"""The punchline: does centrality recover the command interneurons, and does
any higher-order centrality do so BEYOND what raw degree already explains?

Two layers, and the second is the one that matters:

1. **Recovery** — rank neurons by a centrality score and ask how well the top
   of the ranking coincides with the independently-known command-interneuron
   set (AVA, AVB, AVD, AVE, PVC, ...). Reported as precision@k and mean rank.
   This is expected to look good even for degree, because command interneurons
   are a priori high-degree. On its own it is weak and near-circular.

2. **Beyond-degree null test** — the load-bearing, non-circular part. Compare
   how much a metric concentrates on the command set in the REAL graph versus
   in an ensemble of degree-preserving nulls (configuration model, same degree
   sequence). If the observed concentration sits inside the null distribution,
   degree explains it all — report that plainly. If it sits in the tail, the
   specific wiring concentrates the metric on the command set beyond degree.

``null_enrichment_test`` deliberately reports an empirical p-value and a z-score
and does not "fish": a negative result (no enrichment beyond degree) is a real,
honest finding and the API is symmetric about it.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Callable, Dict, Hashable, List, Optional, Sequence, Set

from connectome_graph.graph.graph import Graph
from connectome_graph.graph.nulls import configuration_model

Node = Hashable
ScoreFn = Callable[[Graph], Dict[Node, float]]


# --------------------------------------------------------------------------- #
# Layer 1: recovery of a known target set from a ranking
# --------------------------------------------------------------------------- #
def _ranked_nodes(scores: Dict[Node, float]) -> List[Node]:
    """Nodes sorted by score, highest first. Ties broken by node for stability."""
    return [n for n, _ in sorted(scores.items(), key=lambda kv: (-kv[1], str(kv[0])))]


def precision_at_k(scores: Dict[Node, float], targets: Set[Node], k: int) -> float:
    """Fraction of the top-``k`` scoring nodes that are in ``targets``."""
    if k <= 0:
        return 0.0
    top = _ranked_nodes(scores)[:k]
    hits = sum(1 for n in top if n in targets)
    return hits / k


def recall_at_k(scores: Dict[Node, float], targets: Set[Node], k: int) -> float:
    """Fraction of ``targets`` that appear in the top-``k`` scoring nodes."""
    present = targets & set(scores)
    if not present:
        return 0.0
    top = set(_ranked_nodes(scores)[:k])
    return len(top & present) / len(present)


def rank_of_targets(scores: Dict[Node, float], targets: Set[Node]) -> Dict[Node, int]:
    """1-indexed rank (1 = highest score) of each present target."""
    order = _ranked_nodes(scores)
    pos = {n: i + 1 for i, n in enumerate(order)}
    return {t: pos[t] for t in targets if t in pos}


def mean_rank(scores: Dict[Node, float], targets: Set[Node]) -> float:
    """Mean 1-indexed rank of present targets (lower = better recovery)."""
    ranks = rank_of_targets(scores, targets)
    if not ranks:
        return float("nan")
    return sum(ranks.values()) / len(ranks)


@dataclass
class RecoveryResult:
    metric: str
    n_targets_present: int
    precision_at_k: Dict[int, float]
    mean_rank: float
    mean_normalized_rank: float  # mean_rank / n_nodes, in (0, 1]; lower is better


def recovery_report(
    scores: Dict[Node, float],
    targets: Set[Node],
    metric_name: str,
    ks: Sequence[int] = (5, 10, 20),
) -> RecoveryResult:
    """Summarise how well ``scores`` recovers ``targets``."""
    present = targets & set(scores)
    n = len(scores)
    mr = mean_rank(scores, targets)
    return RecoveryResult(
        metric=metric_name,
        n_targets_present=len(present),
        precision_at_k={k: precision_at_k(scores, targets, k) for k in ks},
        mean_rank=mr,
        mean_normalized_rank=(mr / n) if n and mr == mr else float("nan"),
    )


# --------------------------------------------------------------------------- #
# Layer 2: the beyond-degree, degree-preserving null test
# --------------------------------------------------------------------------- #
def target_concentration(scores: Dict[Node, float], targets: Set[Node]) -> float:
    """Concentration statistic: mean score on targets / mean score overall.

    Ratio > 1 means the metric loads more on the target set than on an average
    node. It is scale-free, so it is comparable between the real graph and a
    null whose absolute score magnitudes may differ.
    """
    present = [scores[t] for t in targets if t in scores]
    if not present:
        return float("nan")
    all_vals = list(scores.values())
    overall = sum(all_vals) / len(all_vals)
    if overall == 0:
        return float("nan")
    return (sum(present) / len(present)) / overall


@dataclass
class NullTestResult:
    metric: str
    observed: float
    null_mean: float
    null_std: float
    z_score: float
    p_value_right: float  # empirical P(null >= observed): small => enriched beyond degree
    num_nulls: int
    beyond_degree: bool  # convenience verdict at the chosen alpha

    def __str__(self) -> str:
        verdict = "BEYOND degree" if self.beyond_degree else "explained by degree"
        return (
            f"{self.metric:<14} obs={self.observed:.3f} "
            f"null={self.null_mean:.3f}+/-{self.null_std:.3f} "
            f"z={self.z_score:+.2f} p={self.p_value_right:.3f} -> {verdict}"
        )


def null_enrichment_test(
    graph: Graph,
    score_fn: ScoreFn,
    targets: Set[Node],
    metric_name: str,
    num_nulls: int = 100,
    seed: Optional[int] = 0,
    alpha: float = 0.05,
    statistic: Callable[[Dict[Node, float], Set[Node]], float] = target_concentration,
) -> NullTestResult:
    """Is the metric's concentration on ``targets`` beyond a degree null?

    Recomputes ``score_fn`` on ``num_nulls`` degree-preserving randomisations
    (configuration model — same degree sequence, wiring destroyed) and compares
    the observed concentration statistic to that null ensemble. A right-tailed
    empirical p-value below ``alpha`` means the real wiring concentrates the
    metric on the command set more than degree alone would — the non-circular
    positive result. Otherwise: degree explains it, reported plainly.
    """
    observed = statistic(score_fn(graph), targets)

    null_vals: List[float] = []
    for i in range(num_nulls):
        null_seed = None if seed is None else seed + i
        null_graph = configuration_model(graph, seed=null_seed)
        val = statistic(score_fn(null_graph), targets)
        if val == val:  # skip NaNs
            null_vals.append(val)

    if not null_vals:
        return NullTestResult(metric_name, observed, float("nan"), float("nan"),
                              float("nan"), float("nan"), 0, False)

    mean = sum(null_vals) / len(null_vals)
    var = sum((v - mean) ** 2 for v in null_vals) / len(null_vals)
    std = sqrt(var)
    z = (observed - mean) / std if std > 0 else float("nan")
    # right-tailed empirical p-value with the standard +1 correction
    ge = sum(1 for v in null_vals if v >= observed)
    p_right = (ge + 1) / (len(null_vals) + 1)

    return NullTestResult(
        metric=metric_name,
        observed=observed,
        null_mean=mean,
        null_std=std,
        z_score=z,
        p_value_right=p_right,
        num_nulls=len(null_vals),
        beyond_degree=(p_right < alpha),
    )
