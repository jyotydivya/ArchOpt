"""
ml/training/evaluate.py
=======================
Diagnostics for a generated candidate population. Reports numbers only —
it never filters or ranks candidates (that is Person 3's job).

Usage (from repo root):
    python -m ml.training.evaluate
    python -m ml.training.evaluate --num 100 --seed 7 --with-optimizer
"""
from __future__ import annotations

import argparse
import math
from typing import Dict, List, Sequence

import numpy as np

from contracts.layout import CampusRequirements, CandidateBuilding, CandidateLayout, Constraint


def _aabb(b: CandidateBuilding):
    """Axis-aligned box of the rotated footprint (exact for 0°/90°)."""
    angle = math.radians(b.rotation)
    extent_x = abs(b.width * math.cos(angle)) + abs(b.depth * math.sin(angle))
    extent_y = abs(b.width * math.sin(angle)) + abs(b.depth * math.cos(angle))
    cx, cy = b.x + b.width / 2.0, b.y + b.depth / 2.0
    return cx - extent_x / 2.0, cy - extent_y / 2.0, cx + extent_x / 2.0, cy + extent_y / 2.0


def _min_pair_separation(layout: CandidateLayout) -> float:
    boxes = [_aabb(b) for b in layout.buildings]
    best = math.inf
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            a, b = boxes[i], boxes[j]
            best = min(best, max(b[0] - a[2], a[0] - b[2], b[1] - a[3], a[1] - b[3]))
    return best


def evaluate_candidates(candidates: Sequence[CandidateLayout], min_gap: float = 10.0) -> Dict[str, float]:
    """Overlap, gap, boundary and diversity statistics for a population."""
    if not candidates:
        return {"num_candidates": 0}

    separations = [_min_pair_separation(c) for c in candidates]
    in_bounds = [
        all(
            box[0] >= -1e-6 and box[1] >= -1e-6 and box[2] <= c.site_width + 1e-6 and box[3] <= c.site_height + 1e-6
            for box in map(_aabb, c.buildings)
        )
        for c in candidates
    ]
    centres = np.array([
        [(b.x + b.width / 2.0, b.y + b.depth / 2.0) for b in c.buildings]
        for c in candidates
    ])  # [K, N, 2]
    signatures = {tuple(np.round(row.ravel(), 1)) for row in centres}

    return {
        "num_candidates": len(candidates),
        "buildings_per_layout": len(candidates[0].buildings),
        "overlap_free_rate": float(np.mean([s > 0 for s in separations])),
        "gap_ok_rate": float(np.mean([s >= min_gap for s in separations])),
        "in_bounds_rate": float(np.mean(in_bounds)),
        "unique_layouts": len(signatures),
        "mean_centre_std_m": float(centres.std(axis=0).mean()),
    }


def evaluate_with_optimizer(
    candidates: Sequence[CandidateLayout],
    requirements: CampusRequirements,
    constraints: List[Constraint] | None = None,
) -> Dict[str, float]:
    """Run Person 3's validator over the population and summarise (read-only)."""
    from optimization.validator import validate_layout

    results = [validate_layout(c, requirements, constraints or []) for c in candidates]
    violation_counts: Dict[str, int] = {}
    for result in results:
        for kind in {v.type for v in result.violations}:
            violation_counts[kind] = violation_counts.get(kind, 0) + 1
    summary: Dict[str, float] = {
        "p3_feasible_rate": float(np.mean([r.feasible for r in results])),
        "p3_mean_constraint_score": float(np.mean([r.constraint_score for r in results])),
    }
    summary.update({f"p3_layouts_with_{k}": v for k, v in sorted(violation_counts.items())})
    return summary


def main() -> None:
    from ml.inference.generate import generate_candidates
    from ml.training.mock_graph import build_mock_campus_graph, mock_constraints, mock_requirements

    parser = argparse.ArgumentParser(description="Evaluate generated candidates on the mock campus.")
    parser.add_argument("--num", type=int, default=100)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--with-optimizer", action="store_true", help="also run Person 3's validator")
    args = parser.parse_args()

    candidates = generate_candidates(build_mock_campus_graph(), args.num, seed=args.seed)
    metrics = evaluate_candidates(candidates)
    if args.with_optimizer:
        metrics.update(evaluate_with_optimizer(candidates, mock_requirements(), mock_constraints()))
    for name, value in metrics.items():
        print(f"{name:40s} {value:.3f}" if isinstance(value, float) else f"{name:40s} {value}")


if __name__ == "__main__":
    main()
