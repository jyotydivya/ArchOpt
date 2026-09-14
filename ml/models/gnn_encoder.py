"""
ml/models/gnn_encoder.py
========================
Edge-conditioned message-passing encoder: one embedding per building node.

Layer l (mean aggregation over incoming edges, residual update):

    m_ij   = ReLU(W_msg [h_j ‖ e_ij] + b_msg)          for every edge j → i
    agg_i  = mean_j m_ij                                (0 if i has no edges)
    h_i'   = h_i + ReLU(W_upd [h_i ‖ agg_i] + b_upd)

Edges are expected in both directions (prepare_graph() already does this).

Two implementations share one parameter naming scheme:
  * GNNEncoder         — torch.nn.Module, used for training (and inference when
                         PyTorch is installed). Plain PyTorch, no PyG needed.
  * encode_numpy()     — NumPy forward pass over the same weights, so inference
                         runs in environments without PyTorch.
"""
from __future__ import annotations

from typing import Dict

import numpy as np

try:
    import torch
    from torch import nn

    TORCH_AVAILABLE = True
except ImportError:  # pragma: no cover - exercised only without torch
    TORCH_AVAILABLE = False

HIDDEN_DIM = 64
NUM_LAYERS = 3

Params = Dict[str, np.ndarray]


# ── NumPy implementation ──────────────────────────────────────────────────────

def linear_numpy(params: Params, name: str, x: np.ndarray) -> np.ndarray:
    return x @ params[f"{name}.weight"].T + params[f"{name}.bias"]


def relu_numpy(x: np.ndarray) -> np.ndarray:
    return np.maximum(x, 0.0)


def encode_numpy(
    params: Params,
    node_inputs: np.ndarray,
    edge_index: np.ndarray,
    edge_inputs: np.ndarray,
    num_layers: int = NUM_LAYERS,
    prefix: str = "encoder",
) -> np.ndarray:
    """Return node embeddings [N, HIDDEN_DIM]."""
    h = relu_numpy(linear_numpy(params, f"{prefix}.input_proj", node_inputs))
    src, dst = edge_index[0], edge_index[1]
    degree = np.maximum(np.bincount(dst, minlength=h.shape[0]), 1)[:, None]

    for layer in range(num_layers):
        agg = np.zeros_like(h)
        if src.size:
            msg = relu_numpy(linear_numpy(
                params, f"{prefix}.layers.{layer}.message",
                np.concatenate([h[src], edge_inputs], axis=1),
            ))
            np.add.at(agg, dst, msg)
            agg /= degree
        h = h + relu_numpy(linear_numpy(
            params, f"{prefix}.layers.{layer}.update",
            np.concatenate([h, agg], axis=1),
        ))
    return h


# ── PyTorch implementation ────────────────────────────────────────────────────

if TORCH_AVAILABLE:

    class MessagePassingLayer(nn.Module):
        def __init__(self, hidden_dim: int, edge_dim: int):
            super().__init__()
            self.message = nn.Linear(hidden_dim + edge_dim, hidden_dim)
            self.update = nn.Linear(2 * hidden_dim, hidden_dim)

        def forward(
            self,
            h: "torch.Tensor",
            edge_index: "torch.Tensor",
            edge_inputs: "torch.Tensor",
        ) -> "torch.Tensor":
            src, dst = edge_index[0], edge_index[1]
            agg = torch.zeros_like(h)
            if src.numel():
                msg = torch.relu(self.message(torch.cat([h[src], edge_inputs], dim=-1)))
                agg = agg.index_add(0, dst, msg)
                degree = torch.bincount(dst, minlength=h.shape[0]).clamp(min=1)
                agg = agg / degree.unsqueeze(-1).to(h.dtype)
            return h + torch.relu(self.update(torch.cat([h, agg], dim=-1)))

    class GNNEncoder(nn.Module):
        def __init__(
            self,
            node_dim: int,
            edge_dim: int,
            hidden_dim: int = HIDDEN_DIM,
            num_layers: int = NUM_LAYERS,
        ):
            super().__init__()
            self.input_proj = nn.Linear(node_dim, hidden_dim)
            self.layers = nn.ModuleList(
                MessagePassingLayer(hidden_dim, edge_dim) for _ in range(num_layers)
            )

        def forward(
            self,
            node_inputs: "torch.Tensor",
            edge_index: "torch.Tensor",
            edge_inputs: "torch.Tensor",
        ) -> "torch.Tensor":
            h = torch.relu(self.input_proj(node_inputs))
            for layer in self.layers:
                h = layer(h, edge_index, edge_inputs)
            return h
