"""train_gnn.py — link-prediction training for REQUIRES and LEADS_TO edges.

Usage:
    python ml/train_gnn.py [--epochs 50] [--seed 42] [--checkpoint ml/checkpoints/gnn_link_predictor.pt]

Requires `ml/requirements.txt` (torch, torch_geometric). See
`docs/gnn-model.md` for exact install/run steps and reported results.

--------------------------------------------------------------------------
Leakage-safe edge split
--------------------------------------------------------------------------
`split.split_edges` (pure Python, unit-tested independently of torch) is
used to divide REQUIRES and LEADS_TO edges into disjoint train/val/test
sets. The message-passing graph fed to the encoder during training/val/test
only ever contains the TRAIN-split positive edges for these two relations
(plus their reverse, for bidirectional message passing) — val/test
positives are held out of the graph entirely, not just out of the loss, so
there is no leakage from the supervision signal back into node embeddings.
The other edge types (HAS_SKILL, TEACHES, IN_CATEGORY) are not a prediction
target, so all of their edges are always part of message passing.

--------------------------------------------------------------------------
Negative sampling
--------------------------------------------------------------------------
For each positive edge in a split, one negative (src, dst) pair is sampled
via `split.sample_negative_edges`, verified against the FULL edge set
(train+val+test positives), never just the train positives -- a "negative"
must not secretly be a held-out positive edge.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ML_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ML_ROOT))

from export_graph import DEFAULT_OUTPUT, export  # noqa: E402
from graph_build import EDGE_TYPES, NODE_TYPES  # noqa: E402
from split import sample_negative_edges, split_edges  # noqa: E402

DEFAULT_CHECKPOINT = ML_ROOT / "checkpoints" / "gnn_link_predictor.pt"
TARGET_EDGE_TYPES = [
    ("Job", "REQUIRES", "Skill"),
    ("Skill", "LEADS_TO", "Skill"),
]


def _reverse(edge_type: tuple[str, str, str]) -> tuple[str, str, str]:
    src, rel, dst = edge_type
    return (dst, f"rev_{rel}", src)


def build_message_passing_edge_types() -> list[tuple[str, str, str]]:
    types = list(EDGE_TYPES)
    types += [_reverse(et) for et in EDGE_TYPES]
    return types


def prepare_splits(raw_graph, seed: int = 42):
    """Returns {edge_type: {"train":[...], "val":[...], "test":[...],
    "val_neg":[...], "test_neg":[...], "train_neg":[...]}} for each target
    edge type, using node ids (strings) — converted to indices later."""
    splits = {}
    for edge_type in TARGET_EDGE_TYPES:
        src_type, _, dst_type = edge_type
        pairs = raw_graph.edges.get(edge_type, [])
        split = split_edges(pairs, val_frac=0.1, test_frac=0.1, seed=seed)
        assert split.is_disjoint(), f"split for {edge_type} is not disjoint"

        all_positives = split.all_edges()
        src_ids = raw_graph.node_ids[src_type]
        dst_ids = raw_graph.node_ids[dst_type]

        train_neg = sample_negative_edges(src_ids, dst_ids, all_positives, len(split.train), seed=seed)
        val_neg = sample_negative_edges(src_ids, dst_ids, all_positives, len(split.val), seed=seed + 1)
        test_neg = sample_negative_edges(src_ids, dst_ids, all_positives, len(split.test), seed=seed + 2)

        splits[edge_type] = {
            "train": split.train,
            "val": split.val,
            "test": split.test,
            "train_neg": train_neg,
            "val_neg": val_neg,
            "test_neg": test_neg,
        }
    return splits


def _pairs_to_index_tensor(pairs, src_index, dst_index):
    import torch

    rows = [src_index[s] for s, d in pairs]
    cols = [dst_index[d] for s, d in pairs]
    return torch.tensor([rows, cols], dtype=torch.long)


def build_training_graph(hetero_data, node_indices, raw_graph, splits):
    """Returns (edge_index_dict for message passing, per-target-edge-type
    dict of {split: (edge_label_index, edge_label)} tensors)."""
    import torch

    edge_index_dict = {}
    for edge_type in EDGE_TYPES:
        src_type, relation, dst_type = edge_type
        if edge_type in TARGET_EDGE_TYPES:
            # Only train-split positives go into message passing.
            train_pairs = splits[edge_type]["train"]
            ei = _pairs_to_index_tensor(train_pairs, node_indices[src_type], node_indices[dst_type])
        else:
            ei = hetero_data[edge_type].edge_index
        edge_index_dict[edge_type] = ei
        edge_index_dict[_reverse(edge_type)] = ei.flip(0)

    supervision = {}
    for edge_type in TARGET_EDGE_TYPES:
        src_type, _, dst_type = edge_type
        src_index = node_indices[src_type]
        dst_index = node_indices[dst_type]
        per_split = {}
        for split_name in ("train", "val", "test"):
            pos = splits[edge_type][split_name]
            neg = splits[edge_type][f"{split_name}_neg"]
            pos_idx = _pairs_to_index_tensor(pos, src_index, dst_index) if pos else torch.empty((2, 0), dtype=torch.long)
            neg_idx = _pairs_to_index_tensor(neg, src_index, dst_index) if neg else torch.empty((2, 0), dtype=torch.long)
            edge_label_index = torch.cat([pos_idx, neg_idx], dim=1)
            edge_label = torch.cat([torch.ones(pos_idx.shape[1]), torch.zeros(neg_idx.shape[1])])
            per_split[split_name] = (edge_label_index, edge_label)
        supervision[edge_type] = per_split

    return edge_index_dict, supervision


def train(
    epochs: int = 50,
    seed: int = 42,
    lr: float = 0.01,
    hidden_channels: int = 64,
    out_channels: int = 32,
    checkpoint_path: Path | str = DEFAULT_CHECKPOINT,
    data_dir=None,
):
    import torch
    import torch.nn.functional as F

    from model import LinkPredictor

    torch.manual_seed(seed)

    from graph_build import DATA_DIR, build_synthetic_career_graph

    export_kwargs = {"data_dir": data_dir} if data_dir else {}
    hetero_data, node_indices = export(output_path=ML_ROOT / "data" / "career_graph.pt", **export_kwargs)
    raw_graph = build_synthetic_career_graph(data_dir=data_dir or DATA_DIR)
    splits = prepare_splits(raw_graph, seed=seed)
    edge_index_dict, supervision = build_training_graph(hetero_data, node_indices, raw_graph, splits)

    num_nodes_per_type = {nt: hetero_data[nt].num_nodes for nt in NODE_TYPES}
    message_passing_edge_types = build_message_passing_edge_types()

    model = LinkPredictor(
        node_types=NODE_TYPES,
        message_passing_edge_types=message_passing_edge_types,
        num_nodes_per_type=num_nodes_per_type,
        hidden_channels=hidden_channels,
        out_channels=out_channels,
    )
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    history = []
    for epoch in range(1, epochs + 1):
        model.train()
        optimizer.zero_grad()
        z_dict = model.encode(edge_index_dict)

        loss = torch.tensor(0.0)
        for edge_type in TARGET_EDGE_TYPES:
            src_type, _, dst_type = edge_type
            edge_label_index, edge_label = supervision[edge_type]["train"]
            if edge_label_index.shape[1] == 0:
                continue
            logits = model.decode(z_dict, src_type, dst_type, edge_label_index)
            loss = loss + F.binary_cross_entropy_with_logits(logits, edge_label)

        loss.backward()
        optimizer.step()

        val_auc = _quick_val_auc(model, edge_index_dict, supervision)
        history.append({"epoch": epoch, "loss": float(loss.item()), "val_auc": val_auc})
        if epoch == 1 or epoch % 10 == 0 or epoch == epochs:
            print(f"epoch {epoch:3d}  loss={loss.item():.4f}  val_auc={val_auc:.4f}")

    checkpoint_path = Path(checkpoint_path)
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "model_state_dict": model.state_dict(),
            "config": model.config,
            "node_indices": node_indices,
            "target_edge_types": TARGET_EDGE_TYPES,
            "message_passing_edge_types": message_passing_edge_types,
            "history": history,
            "seed": seed,
        },
        checkpoint_path,
    )
    print(f"Checkpoint saved to {checkpoint_path}")
    return model, history, splits, node_indices, edge_index_dict, supervision


def _quick_val_auc(model, edge_index_dict, supervision) -> float:
    import torch

    try:
        from sklearn.metrics import roc_auc_score
    except ImportError:
        return float("nan")

    model.eval()
    with torch.no_grad():
        z_dict = model.encode(edge_index_dict)
        all_scores, all_labels = [], []
        for edge_type in TARGET_EDGE_TYPES:
            src_type, _, dst_type = edge_type
            edge_label_index, edge_label = supervision[edge_type]["val"]
            if edge_label_index.shape[1] == 0:
                continue
            logits = model.decode(z_dict, src_type, dst_type, edge_label_index)
            all_scores.extend(torch.sigmoid(logits).tolist())
            all_labels.extend(edge_label.tolist())
    if not all_labels or len(set(all_labels)) < 2:
        return float("nan")
    return roc_auc_score(all_labels, all_scores)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--lr", type=float, default=0.01)
    parser.add_argument("--checkpoint", default=str(DEFAULT_CHECKPOINT))
    args = parser.parse_args()
    train(epochs=args.epochs, seed=args.seed, lr=args.lr, checkpoint_path=args.checkpoint)


if __name__ == "__main__":
    main()
