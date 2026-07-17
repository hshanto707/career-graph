"""export_graph.py — Neo4j-shaped graph -> PyTorch Geometric HeteroData.

Requires the packages in `ml/requirements.txt` (torch, torch_geometric).
See `docs/gnn-model.md` for exact install/run steps.

No live Neo4j instance is available in this sandbox, so this exports from
the synthetic seed data (`backend/data/kaggle_jobs.csv` +
`backend/data/onet_skills.csv` + `backend/data/synonyms.json`, run through
the real `IngestionAgent`/`NormalizationAgent` pipeline against
`FakeGraphService`) rather than a live Bolt connection. The Cypher-based
path is documented below for when a real Neo4j instance + full 10k-job
dataset are available.

Node features: since none of the node types carry rich numeric features in
the current schema, every node type gets a learned embedding table inside
the model (see `model.py`) rather than fixed input features here — this
export step only needs to produce correct node counts/indices and edge
index tensors.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ML_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ML_ROOT))

from graph_build import DATA_DIR, EDGE_TYPES, NODE_TYPES, RawGraph, build_synthetic_career_graph  # noqa: E402

DEFAULT_OUTPUT = ML_ROOT / "data" / "career_graph.pt"


def to_hetero_data(raw: RawGraph):
    """Convert a `RawGraph` (plain Python ids) into a PyG `HeteroData`.

    Node indices are assigned by position in `raw.node_ids[node_type]`
    (already sorted, so this is deterministic run-to-run). Edge tensors are
    `torch.long` of shape [2, num_edges] in PyG's expected layout.
    """
    import torch
    from torch_geometric.data import HeteroData

    data = HeteroData()
    indices: dict[str, dict[str, int]] = {}

    for node_type in NODE_TYPES:
        ids = raw.node_ids.get(node_type, [])
        indices[node_type] = {nid: i for i, nid in enumerate(ids)}
        data[node_type].num_nodes = len(ids)
        data[node_type].node_ids = list(ids)  # keep original string ids for inference/debugging

    for edge_type in EDGE_TYPES:
        src_type, relation, dst_type = edge_type
        pairs = raw.edges.get(edge_type, [])
        src_idx = indices[src_type]
        dst_idx = indices[dst_type]
        rows = [src_idx[s] for s, d in pairs if s in src_idx and d in dst_idx]
        cols = [dst_idx[d] for s, d in pairs if s in src_idx and d in dst_idx]
        edge_index = torch.tensor([rows, cols], dtype=torch.long) if rows else torch.empty((2, 0), dtype=torch.long)
        data[src_type, relation, dst_type].edge_index = edge_index

    return data, indices


def export(data_dir: Path | str = DATA_DIR, output_path: Path | str = DEFAULT_OUTPUT):
    import torch

    raw = build_synthetic_career_graph(data_dir=data_dir)
    hetero_data, indices = to_hetero_data(raw)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"hetero_data": hetero_data, "node_indices": indices}, output_path)
    return hetero_data, indices


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default=str(DATA_DIR))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()

    hetero_data, _ = export(args.data_dir, args.output)
    print(hetero_data)
    for node_type in NODE_TYPES:
        print(f"{node_type}: {hetero_data[node_type].num_nodes} nodes")
    for edge_type in EDGE_TYPES:
        et = hetero_data[edge_type]
        print(f"{edge_type}: {et.edge_index.shape[1]} edges")
    print(f"Saved to {args.output}")


if __name__ == "__main__":
    main()
