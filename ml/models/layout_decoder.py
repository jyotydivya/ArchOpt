"""
ml/models/layout_decoder.py
===========================
Turns node embeddings + latent noise into building placements.

Per node the MLP sees [h_i ‖ mean(h) ‖ z_i ‖ z_graph] and outputs three logits:

    u, v        sigmoid → relative position of the footprint centre in the
                feasible range of the site
    vertical    sigmoid → probability that the building is rotated 90°

z_i (per building) and z_graph (per candidate) are Gaussian samples; drawing
fresh samples is what makes each candidate layout different.

bounded_positions() maps (u, v, vertical) to metres so that
  * x, y (bottom-left of the unrotated footprint) are ≥ 0, and
  * the rotated footprint stays inside [0, site_width] × [0, site_height]
whenever the building fits on the site at all.
It uses only arithmetic + abs(), so it works on NumPy arrays and torch tensors.
"""
from __future__ import annotations

import numpy as np

from ml.models.gnn_encoder import TORCH_AVAILABLE, Params, linear_numpy, relu_numpy

if TORCH_AVAILABLE:
    import torch
    from torch import nn

LATENT_DIM = 8
DECODER_OUTPUTS = 3


def _max(a, b):
    return (a + b + abs(a - b)) / 2.0


def _relu(a):
    return (a + abs(a)) / 2.0


def bounded_positions(u, v, vertical, width, depth, site_width, site_height, margin=0.0):
    """
    Map normalised outputs to footprint coordinates in metres.

    `vertical` may be soft (probability, training) or hard 0/1 (inference);
    the axis-aligned extent is interpolated between the 0° and 90° footprints.

    Returns (x, y, cx, cy, extent_x, extent_y).
    """
    extent_x = (1.0 - vertical) * width + vertical * depth
    extent_y = (1.0 - vertical) * depth + vertical * width
    half_x = _max(width, extent_x) / 2.0 + margin
    half_y = _max(depth, extent_y) / 2.0 + margin
    cx = half_x + u * _relu(site_width - 2.0 * half_x)
    cy = half_y + v * _relu(site_height - 2.0 * half_y)
    return cx - width / 2.0, cy - depth / 2.0, cx, cy, extent_x, extent_y


def sigmoid_numpy(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(x, -50.0, 50.0)))


def _decoder_inputs(h, z_node, z_graph, xp_cat, expand):
    """Build [K, N, 2H + 2L] decoder inputs from h [N, H], z_node [K, N, L], z_graph [K, L]."""
    k, n = z_node.shape[0], z_node.shape[1]
    graph_mean = h.mean(0)
    return xp_cat([
        expand(h[None, :, :], (k, n, h.shape[1])),
        expand(graph_mean[None, None, :], (k, n, h.shape[1])),
        z_node,
        expand(z_graph[:, None, :], (k, n, z_graph.shape[1])),
    ])


# ── NumPy implementation ──────────────────────────────────────────────────────

def decode_numpy(
    params: Params,
    h: np.ndarray,
    z_node: np.ndarray,
    z_graph: np.ndarray,
    prefix: str = "decoder",
) -> np.ndarray:
    """Return raw logits [K, N, 3]."""
    x = _decoder_inputs(
        h, z_node, z_graph,
        lambda parts: np.concatenate(parts, axis=-1),
        np.broadcast_to,
    )
    x = relu_numpy(linear_numpy(params, f"{prefix}.hidden1", x))
    x = relu_numpy(linear_numpy(params, f"{prefix}.hidden2", x))
    return linear_numpy(params, f"{prefix}.out", x)


# ── PyTorch implementation ────────────────────────────────────────────────────

if TORCH_AVAILABLE:

    class LayoutDecoder(nn.Module):
        def __init__(self, hidden_dim: int, latent_dim: int = LATENT_DIM):
            super().__init__()
            self.hidden1 = nn.Linear(2 * hidden_dim + 2 * latent_dim, hidden_dim)
            self.hidden2 = nn.Linear(hidden_dim, hidden_dim)
            self.out = nn.Linear(hidden_dim, DECODER_OUTPUTS)

        def forward(
            self,
            h: "torch.Tensor",
            z_node: "torch.Tensor",
            z_graph: "torch.Tensor",
        ) -> "torch.Tensor":
            x = _decoder_inputs(
                h, z_node, z_graph,
                lambda parts: torch.cat(parts, dim=-1),
                lambda t, shape: t.expand(*shape),
            )
            x = torch.relu(self.hidden1(x))
            x = torch.relu(self.hidden2(x))
            return self.out(x)
