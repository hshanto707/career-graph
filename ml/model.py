"""model.py — 2-layer heterogeneous GraphSAGE encoder + dot-product decoder
for link prediction on REQUIRES (Job-Skill) and LEADS_TO (Skill-Skill).

Architecture (documented, not a from-scratch novel design — see
project-roadmap.md Part B item 3):
  - Each node type gets a learned embedding table as its input feature
    (the schema has no rich numeric node features yet).
  - Two `HeteroConv` layers of `SAGEConv`, one per (message-passing) edge
    type present in the training graph, in both directions (reverse edges
    are added purely for message passing — see `train_gnn.py`).
  - Decoder: dot product between the two endpoint embeddings, passed
    through a sigmoid at inference/eval time (logits during training, for
    `BCEWithLogitsLoss` numerical stability).
"""
from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import HeteroConv, SAGEConv


class HeteroSAGEEncoder(nn.Module):
    def __init__(
        self,
        node_types: list[str],
        message_passing_edge_types: list[tuple[str, str, str]],
        num_nodes_per_type: dict[str, int],
        hidden_channels: int = 64,
        out_channels: int = 32,
    ):
        super().__init__()
        self.node_types = node_types
        self.embeddings = nn.ModuleDict(
            {nt: nn.Embedding(max(num_nodes_per_type.get(nt, 1), 1), hidden_channels) for nt in node_types}
        )

        def build_conv(out_dim: int) -> HeteroConv:
            convs = {
                edge_type: SAGEConv((-1, -1), out_dim)
                for edge_type in message_passing_edge_types
            }
            return HeteroConv(convs, aggr="mean")

        self.conv1 = build_conv(hidden_channels)
        self.conv2 = build_conv(out_channels)

    def forward(self, x_dict_placeholder, edge_index_dict):
        x_dict = {
            nt: self.embeddings[nt](torch.arange(self.embeddings[nt].num_embeddings, device=self._device()))
            for nt in self.node_types
        }
        x_dict = self.conv1(x_dict, edge_index_dict)
        x_dict = {k: F.relu(v) for k, v in x_dict.items()}
        x_dict = self.conv2(x_dict, edge_index_dict)
        return x_dict

    def _device(self):
        return next(self.parameters()).device


class DotProductDecoder(nn.Module):
    """Dot-product edge scorer: score(u, v) = z_u . z_v (a logit)."""

    def forward(self, z_src: torch.Tensor, z_dst: torch.Tensor) -> torch.Tensor:
        return (z_src * z_dst).sum(dim=-1)


class LinkPredictor(nn.Module):
    """Full model: encoder + dot-product decoder for named target edge types."""

    def __init__(
        self,
        node_types: list[str],
        message_passing_edge_types: list[tuple[str, str, str]],
        num_nodes_per_type: dict[str, int],
        hidden_channels: int = 64,
        out_channels: int = 32,
    ):
        super().__init__()
        self.encoder = HeteroSAGEEncoder(
            node_types, message_passing_edge_types, num_nodes_per_type, hidden_channels, out_channels
        )
        self.decoder = DotProductDecoder()
        self.config = {
            "node_types": node_types,
            "message_passing_edge_types": message_passing_edge_types,
            "num_nodes_per_type": num_nodes_per_type,
            "hidden_channels": hidden_channels,
            "out_channels": out_channels,
        }

    def encode(self, edge_index_dict):
        return self.encoder(None, edge_index_dict)

    def decode(self, z_dict, src_type: str, dst_type: str, edge_label_index: torch.Tensor) -> torch.Tensor:
        src = z_dict[src_type][edge_label_index[0]]
        dst = z_dict[dst_type][edge_label_index[1]]
        return self.decoder(src, dst)
