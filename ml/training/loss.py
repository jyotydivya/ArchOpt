"""
ml/training/loss.py
===================
Self-supervised layout losses (PyTorch).

No ground-truth campus layouts exist, so the model learns from geometry and
the graph's relationships. For K latent samples of one graph:

  overlap    footprints (inflated by min_gap / 2) should not intersect
  relation   NEAR / SAME_ZONE / ACCESSIBLE_FROM / ROAD_ACCESS pull together,
             FAR pushes apart, MIN/MAX_DISTANCE edges respect their metres
  zone       same-zone buildings within 0.5 × min(site side) (P3's zoning rule)
  diversity  different latent samples should give different layouts

Boundary needs no loss: bounded_positions() keeps footprints on site.
These are training signals only — candidates are never filtered on them.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, Tuple

import torch

from ml.models.features import DISTANCE_COLUMN, EDGE_RELATIONS, WEIGHT_COLUMN, PreparedGraph
from ml.models.layout_decoder import bounded_positions

# Preferred maximum centre distance, as a fraction of the site diagonal.
ATTRACT_TARGETS: Dict[str, float] = {
    "NEAR": 0.20,
    "SAME_ZONE": 0.25,
    "ACCESSIBLE_FROM": 0.30,
    "ROAD_ACCESS": 0.30,
}
FAR_TARGET = 0.45
DIVERSITY_SIGMA = 0.2


@dataclass
class LossWeights:
    overlap: float = 4.0
    relation: float = 1.0
    zone: float = 1.0
    diversity: float = 0.5


@dataclass
class GraphTensors:
    widths: torch.Tensor          # [N]
    depths: torch.Tensor          # [N]
    zone_ids: torch.Tensor        # [N]
    edge_src: torch.Tensor        # [E]
    edge_dst: torch.Tensor        # [E]
    edge_features: torch.Tensor   # [E, EDGE_FEATURE_DIM]
    site_width: float
    site_height: float
    min_gap: float

    @property
    def diagonal(self) -> float:
        return math.hypot(self.site_width, self.site_height)


def graph_tensors(graph: PreparedGraph, min_gap: float = 10.0) -> GraphTensors:
    return GraphTensors(
        widths=torch.as_tensor(graph.widths, dtype=torch.float32),
        depths=torch.as_tensor(graph.depths, dtype=torch.float32),
        zone_ids=torch.as_tensor(graph.zone_ids),
        edge_src=torch.as_tensor(graph.raw_edge_index[0]),
        edge_dst=torch.as_tensor(graph.raw_edge_index[1]),
        edge_features=torch.as_tensor(graph.raw_edge_features, dtype=torch.float32),
        site_width=graph.site_width,
        site_height=graph.site_height,
        min_gap=min_gap,
    )


def soft_layout(raw: torch.Tensor, t: GraphTensors) -> Tuple[torch.Tensor, ...]:
    """Raw logits [K, N, 3] → soft centres and axis-aligned extents, each [K, N]."""
    u, v, vertical = torch.sigmoid(raw).unbind(-1)
    _, _, cx, cy, extent_x, extent_y = bounded_positions(
        u, v, vertical, t.widths, t.depths, t.site_width, t.site_height
    )
    return cx, cy, extent_x, extent_y


def _upper_pairs(n: int) -> torch.Tensor:
    return torch.triu(torch.ones(n, n, dtype=torch.bool), diagonal=1)


def overlap_loss(cx, cy, extent_x, extent_y, t: GraphTensors) -> torch.Tensor:
    """Summed pairwise intersection of gap-inflated footprints / mean footprint area."""
    half_x = extent_x / 2.0 + t.min_gap / 2.0
    half_y = extent_y / 2.0 + t.min_gap / 2.0
    over_x = torch.relu(half_x.unsqueeze(-1) + half_x.unsqueeze(-2) - (cx.unsqueeze(-1) - cx.unsqueeze(-2)).abs())
    over_y = torch.relu(half_y.unsqueeze(-1) + half_y.unsqueeze(-2) - (cy.unsqueeze(-1) - cy.unsqueeze(-2)).abs())
    intersection = (over_x * over_y)[..., _upper_pairs(cx.shape[-1])]
    return intersection.sum(-1).mean() / (t.widths * t.depths).mean()


def relation_loss(cx, cy, t: GraphTensors) -> torch.Tensor:
    if t.edge_src.numel() == 0:
        return cx.new_zeros(())
    diagonal = t.diagonal
    dist = torch.sqrt(
        (cx[..., t.edge_src] - cx[..., t.edge_dst]) ** 2
        + (cy[..., t.edge_src] - cy[..., t.edge_dst]) ** 2
        + 1e-6
    ) / diagonal
    feats = t.edge_features

    def rel(name: str) -> torch.Tensor:
        return feats[:, EDGE_RELATIONS.index(name)]

    target = feats[:, DISTANCE_COLUMN] / diagonal
    terms = rel("FAR") * torch.relu(FAR_TARGET - dist)
    terms = terms + rel("MIN_DISTANCE") * torch.relu(target - dist)
    terms = terms + rel("MAX_DISTANCE") * torch.relu(dist - target)
    for name, limit in ATTRACT_TARGETS.items():
        terms = terms + rel(name) * torch.relu(dist - limit)
    return (feats[:, WEIGHT_COLUMN] * terms).sum(-1).mean() / cx.shape[-1]


def zone_loss(cx, cy, t: GraphTensors) -> torch.Tensor:
    same_zone = (t.zone_ids.unsqueeze(0) == t.zone_ids.unsqueeze(1)) & _upper_pairs(cx.shape[-1])
    if not bool(same_zone.any()):
        return cx.new_zeros(())
    dist = torch.sqrt(
        (cx.unsqueeze(-1) - cx.unsqueeze(-2)) ** 2 + (cy.unsqueeze(-1) - cy.unsqueeze(-2)) ** 2 + 1e-6
    )[..., same_zone]
    threshold = 0.45 * min(t.site_width, t.site_height)
    return torch.relu(dist - threshold).sum(-1).mean() / (t.diagonal * cx.shape[-1])


def diversity_loss(cx, cy, t: GraphTensors) -> torch.Tensor:
    """Mean RBF similarity between latent samples; lower = more diverse."""
    k = cx.shape[0]
    if k < 2:
        return cx.new_zeros(())
    pos = torch.stack([cx / t.site_width, cy / t.site_height], dim=-1)          # [K, N, 2]
    msd = ((pos.unsqueeze(0) - pos.unsqueeze(1)) ** 2).sum(-1).mean(-1)          # [K, K]
    return torch.exp(-msd[_upper_pairs(k)] / DIVERSITY_SIGMA ** 2).mean()


def total_loss(
    raw: torch.Tensor,
    t: GraphTensors,
    weights: LossWeights = LossWeights(),
) -> Tuple[torch.Tensor, Dict[str, float]]:
    cx, cy, extent_x, extent_y = soft_layout(raw, t)
    parts = {
        "overlap": overlap_loss(cx, cy, extent_x, extent_y, t),
        "relation": relation_loss(cx, cy, t),
        "zone": zone_loss(cx, cy, t),
        "diversity": diversity_loss(cx, cy, t),
    }
    loss = sum(getattr(weights, name) * value for name, value in parts.items())
    return loss, {name: float(value.detach()) for name, value in parts.items()}
