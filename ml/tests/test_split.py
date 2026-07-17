"""test_split.py — pure-Python tests for ml/split.py (edge split +
negative sampling). No torch dependency at all.

Run with: `pytest ml/tests/test_split.py` (only needs pytest, no other deps).

Covers test-plan.md "Custom AI Model (GNN)" #2 (disjoint, non-empty splits)
and #4 (negative sampling never contaminates with real edges).
"""
from __future__ import annotations

import sys
from pathlib import Path

ML_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ML_ROOT))

from split import sample_negative_edges, split_edges  # noqa: E402


def _make_edges(n: int) -> list[tuple[str, str]]:
    return [(f"src-{i}", f"dst-{i}") for i in range(n)]


def test_split_is_disjoint():
    edges = _make_edges(100)
    split = split_edges(edges, val_frac=0.1, test_frac=0.1, seed=42)
    assert split.is_disjoint()


def test_split_covers_all_edges_exactly_once():
    edges = _make_edges(50)
    split = split_edges(edges, val_frac=0.2, test_frac=0.2, seed=1)
    assert split.all_edges() == set(edges)
    assert len(split.train) + len(split.val) + len(split.test) == len(set(edges))


def test_each_split_non_empty_above_minimum_size():
    edges = _make_edges(20)
    split = split_edges(edges, val_frac=0.1, test_frac=0.1, seed=7)
    assert len(split.train) > 0
    assert len(split.val) > 0
    assert len(split.test) > 0


def test_tiny_dataset_still_produces_disjoint_nonempty_splits():
    # Minimum viable size (3 distinct edges): each split still gets >= 1.
    edges = _make_edges(3)
    split = split_edges(edges, seed=3)
    assert split.is_disjoint()
    assert len(split.train) >= 1
    assert len(split.val) >= 1
    assert len(split.test) >= 1


def test_split_deterministic_for_same_seed():
    edges = _make_edges(30)
    a = split_edges(edges, seed=99)
    b = split_edges(edges, seed=99)
    assert a.train == b.train
    assert a.val == b.val
    assert a.test == b.test


def test_split_differs_for_different_seed():
    edges = _make_edges(30)
    a = split_edges(edges, seed=1)
    b = split_edges(edges, seed=2)
    assert (a.train, a.val, a.test) != (b.train, b.val, b.test)


def test_duplicate_edges_deduplicated_before_split():
    edges = _make_edges(10) + _make_edges(10)  # exact duplicates
    split = split_edges(edges, seed=5)
    assert len(split.all_edges()) == 10


def test_negative_edges_never_real_positives():
    src_ids = [f"s{i}" for i in range(20)]
    dst_ids = [f"d{i}" for i in range(20)]
    positives = {(f"s{i}", f"d{i}") for i in range(20)}
    negatives = sample_negative_edges(src_ids, dst_ids, positives, num_samples=50, seed=42)
    assert negatives, "expected at least some negatives in a sparse graph"
    assert not (set(negatives) & positives)


def test_negative_sampling_checks_against_full_positive_set_not_just_train():
    """A negative must not secretly be a held-out val/test positive --
    verified by passing the FULL positive set (train+val+test) as the
    exclusion set, mirroring how train_gnn.py calls this function."""
    src_ids = ["a", "b", "c"]
    dst_ids = ["x", "y", "z"]
    all_positives = {("a", "x"), ("b", "y"), ("c", "z")}
    negatives = sample_negative_edges(src_ids, dst_ids, all_positives, num_samples=5, seed=1)
    for neg in negatives:
        assert neg not in all_positives


def test_negative_sampling_degrades_gracefully_when_graph_too_dense():
    # Every possible (src, dst) pair is already a positive -- no negative
    # exists; must return an empty list rather than hang/crash.
    src_ids = ["a", "b"]
    dst_ids = ["x", "y"]
    all_positives = {("a", "x"), ("a", "y"), ("b", "x"), ("b", "y")}
    negatives = sample_negative_edges(src_ids, dst_ids, all_positives, num_samples=5, seed=1)
    assert negatives == []


def test_split_edges_rejects_invalid_fractions():
    import pytest

    with pytest.raises(ValueError):
        split_edges(_make_edges(10), val_frac=0.6, test_frac=0.6)
