"""split.py — edge-level train/val/test splitting + negative sampling.

Pure Python (no torch dependency) so the split-disjointness and negative-
sampling-correctness logic can be unit-tested (test-plan.md "Custom AI Model
(GNN)" #2 and #4) in any environment, independent of whether torch/PyTorch
Geometric are installed.

Split is edge-level, not node-level: every positive edge is assigned to
exactly one of train/val/test, so no edge leaks across splits. Message
passing during training only uses the train-split positive edges (see
`train_gnn.py`), which additionally prevents val/test edges from leaking
into the encoder's input graph.
"""
from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass(frozen=True)
class EdgeSplit:
    train: list[tuple[str, str]]
    val: list[tuple[str, str]]
    test: list[tuple[str, str]]

    def is_disjoint(self) -> bool:
        t, v, te = set(self.train), set(self.val), set(self.test)
        return not (t & v) and not (t & te) and not (v & te)

    def all_edges(self) -> set[tuple[str, str]]:
        return set(self.train) | set(self.val) | set(self.test)


def split_edges(
    edges: list[tuple[str, str]],
    val_frac: float = 0.1,
    test_frac: float = 0.1,
    seed: int = 42,
) -> EdgeSplit:
    """Deterministically shuffle (seeded) then partition `edges` into
    train/val/test with no overlap. Duplicate edges are deduplicated first
    (an edge belongs to exactly one split).

    Guarantees, for any dataset with >= 3 distinct edges: every split is
    non-empty (at least one val and one test edge), matching test-plan.md's
    "each split is non-empty for a dataset above a minimum size".
    """
    if not (0 <= val_frac < 1 and 0 <= test_frac < 1 and val_frac + test_frac < 1):
        raise ValueError("val_frac + test_frac must be < 1, both in [0, 1)")

    unique_edges = sorted(set(edges))  # sorted first for determinism pre-shuffle
    rng = random.Random(seed)
    shuffled = unique_edges[:]
    rng.shuffle(shuffled)

    n = len(shuffled)
    n_val = max(1, int(round(n * val_frac))) if n >= 3 else 0
    n_test = max(1, int(round(n * test_frac))) if n >= 3 else 0
    # Never let val+test consume the entire set — always leave >= 1 for train
    # when there's more than one edge.
    while n > 1 and n_val + n_test >= n:
        if n_val >= n_test and n_val > 0:
            n_val -= 1
        elif n_test > 0:
            n_test -= 1
        else:
            break

    val = shuffled[:n_val]
    test = shuffled[n_val:n_val + n_test]
    train = shuffled[n_val + n_test:]
    return EdgeSplit(train=train, val=val, test=test)


def sample_negative_edges(
    src_ids: list[str],
    dst_ids: list[str],
    positive_edges: set[tuple[str, str]],
    num_samples: int,
    seed: int = 42,
    allow_self_loops: bool = True,
) -> list[tuple[str, str]]:
    """Sample `num_samples` (src, dst) pairs that are NOT in
    `positive_edges` (the full set of real edges of this type, i.e. the
    union of train+val+test — never just the train positives — so a
    "negative" truly never contaminates training with a false negative that
    is actually a held-out positive, per test-plan.md #4).

    Sampling is with rejection, seeded for reproducibility. If the graph is
    dense enough that negatives are hard to find, sampling degrades
    gracefully by returning fewer than `num_samples` after a bounded number
    of attempts rather than looping forever.
    """
    if not src_ids or not dst_ids or num_samples <= 0:
        return []

    rng = random.Random(seed)
    negatives: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    max_attempts = num_samples * 50 + 1000

    attempts = 0
    while len(negatives) < num_samples and attempts < max_attempts:
        attempts += 1
        src = rng.choice(src_ids)
        dst = rng.choice(dst_ids)
        if not allow_self_loops and src == dst:
            continue
        pair = (src, dst)
        if pair in positive_edges or pair in seen:
            continue
        seen.add(pair)
        negatives.append(pair)

    return negatives
