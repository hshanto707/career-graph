"""evaluate.py — AUC-ROC / Hits@10 / MRR for the trained GNN, PLUS the same
metrics for the algorithmic baseline (`RecommendationAgent`'s Jaccard /
LEADS_TO-reachability signal, via `baseline.py`) on the IDENTICAL held-out
test edges — the thesis Evaluation-chapter comparison table
(test-plan.md GNN #5, #6).

Usage:
    python ml/evaluate.py [--checkpoint ml/checkpoints/gnn_link_predictor.pt] [--seed 42]

Requires `ml/requirements.txt` (torch, torch_geometric, scikit-learn).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ML_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ML_ROOT))

from export_graph import export  # noqa: E402
from graph_build import DATA_DIR, build_synthetic_career_graph  # noqa: E402
from train_gnn import (  # noqa: E402
    DEFAULT_CHECKPOINT,
    TARGET_EDGE_TYPES,
    _pairs_to_index_tensor,
    build_message_passing_edge_types,
    prepare_splits,
)

RESULTS_PATH = ML_ROOT / "results" / "evaluation_report.json"


def ranking_metrics(pos_scores: list[float], neg_scores: list[float], k: int = 10):
    """For each positive score, rank it against ALL negative scores (a
    shared candidate pool, standard for small-graph link-prediction eval).
    hits@k = fraction of positives ranked in the top-k; MRR = mean
    reciprocal rank of the positive within [itself + all negatives].
    """
    if not pos_scores:
        return {"hits_at_k": float("nan"), "mrr": float("nan")}

    hits = 0
    reciprocal_ranks = []
    sorted_neg = sorted(neg_scores, reverse=True)
    for p in pos_scores:
        # rank = 1 + number of negatives strictly greater than p
        rank = 1
        for n in sorted_neg:
            if n > p:
                rank += 1
            else:
                break
        reciprocal_ranks.append(1.0 / rank)
        if rank <= k:
            hits += 1
    return {
        "hits_at_k": hits / len(pos_scores),
        "mrr": sum(reciprocal_ranks) / len(reciprocal_ranks),
    }


def auc_roc(pos_scores: list[float], neg_scores: list[float]) -> float:
    from sklearn.metrics import roc_auc_score

    if not pos_scores or not neg_scores:
        return float("nan")
    y_true = [1] * len(pos_scores) + [0] * len(neg_scores)
    y_score = list(pos_scores) + list(neg_scores)
    if len(set(y_true)) < 2:
        return float("nan")
    return roc_auc_score(y_true, y_score)


def evaluate_gnn(checkpoint_path: Path, seed: int, k: int = 10):
    import torch

    from graph_build import build_synthetic_career_graph
    from model import LinkPredictor

    checkpoint = torch.load(checkpoint_path, weights_only=False)
    config = checkpoint["config"]
    node_indices = checkpoint["node_indices"]

    model = LinkPredictor(**config)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    hetero_data, _ = export(output_path=ML_ROOT / "data" / "career_graph.pt")
    raw_graph = build_synthetic_career_graph(data_dir=DATA_DIR)
    splits = prepare_splits(raw_graph, seed=seed)

    from train_gnn import build_training_graph

    edge_index_dict, supervision = build_training_graph(hetero_data, node_indices, raw_graph, splits)

    results = {}
    with torch.no_grad():
        z_dict = model.encode(edge_index_dict)
        for edge_type in TARGET_EDGE_TYPES:
            src_type, relation, dst_type = edge_type
            edge_label_index, edge_label = supervision[edge_type]["test"]
            if edge_label_index.shape[1] == 0:
                continue
            logits = model.decode(z_dict, src_type, dst_type, edge_label_index)
            scores = torch.sigmoid(logits).tolist()
            labels = edge_label.tolist()
            pos = [s for s, l in zip(scores, labels) if l == 1.0]
            neg = [s for s, l in zip(scores, labels) if l == 0.0]
            metrics = ranking_metrics(pos, neg, k=k)
            metrics["auc_roc"] = auc_roc(pos, neg)
            metrics["num_test_pos"] = len(pos)
            metrics["num_test_neg"] = len(neg)
            results[f"{src_type}_{relation}_{dst_type}"] = metrics

    return results, splits


def evaluate_baseline(splits, k: int = 10):
    from baseline import build_leads_to_baseline, build_requires_baseline

    results = {}
    for edge_type in TARGET_EDGE_TYPES:
        src_type, relation, dst_type = edge_type
        edge_splits = splits[edge_type]
        train_edges = edge_splits["train"]
        test_pos = edge_splits["test"]
        test_neg = edge_splits["test_neg"]
        if not test_pos:
            continue

        if relation == "REQUIRES":
            score_fn = build_requires_baseline(train_edges)
        else:
            score_fn = build_leads_to_baseline(train_edges)

        pos_scores = [score_fn(a, b) for a, b in test_pos]
        neg_scores = [score_fn(a, b) for a, b in test_neg]
        metrics = ranking_metrics(pos_scores, neg_scores, k=k)
        metrics["auc_roc"] = auc_roc(pos_scores, neg_scores)
        metrics["num_test_pos"] = len(pos_scores)
        metrics["num_test_neg"] = len(neg_scores)
        results[f"{src_type}_{relation}_{dst_type}"] = metrics

    return results


def build_comparison_table(gnn_results: dict, baseline_results: dict) -> str:
    lines = [
        "| Edge Type | Model | AUC-ROC | Hits@10 | MRR | #test_pos | #test_neg |",
        "|---|---|---|---|---|---|---|",
    ]
    for key in gnn_results:
        g = gnn_results[key]
        b = baseline_results.get(key, {})
        lines.append(
            f"| {key} | GNN (GraphSAGE) | {g['auc_roc']:.3f} | {g['hits_at_k']:.3f} | "
            f"{g['mrr']:.3f} | {g['num_test_pos']} | {g['num_test_neg']} |"
        )
        if b:
            lines.append(
                f"| {key} | Algorithmic baseline | {b['auc_roc']:.3f} | {b['hits_at_k']:.3f} | "
                f"{b['mrr']:.3f} | {b['num_test_pos']} | {b['num_test_neg']} |"
            )
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", default=str(DEFAULT_CHECKPOINT))
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--k", type=int, default=10)
    args = parser.parse_args()

    checkpoint_path = Path(args.checkpoint)
    if not checkpoint_path.exists():
        print(f"No checkpoint found at {checkpoint_path}. Run train_gnn.py first.")
        sys.exit(1)

    gnn_results, splits = evaluate_gnn(checkpoint_path, seed=args.seed, k=args.k)
    baseline_results = evaluate_baseline(splits, k=args.k)

    table = build_comparison_table(gnn_results, baseline_results)
    print(table)

    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "gnn": gnn_results,
        "baseline": baseline_results,
        "comparison_table_markdown": table,
        "seed": args.seed,
        "k": args.k,
    }
    with open(RESULTS_PATH, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nSaved report to {RESULTS_PATH}")


if __name__ == "__main__":
    main()
