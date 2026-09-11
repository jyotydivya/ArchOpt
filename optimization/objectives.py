"""
optimization/objectives.py
============================
Five scalar objective functions for the NSGA-II optimizer.

Convention: ALL objectives are expressed as values to **minimise**.
  - Where "higher is better" (e.g. land utilization), we return 1 − value.
  - Objectives are normalised to [0, 1].

Objectives
----------
1. land_utilization_obj    → minimise (1 − land_utilization)
2. green_ratio_obj         → minimise (1 − green_ratio)
3. parking_ratio_obj       → minimise (1 − parking_ratio)
4. accessibility_obj       → minimise mean normalised distance to entrances
5. road_efficiency_obj     → minimise estimated total road length / site diagonal

Public API
----------
compute_objectives(layout, requirements) -> dict[str, float]
    Returns raw metric values (higher = better for all metrics).
    The NSGA-II module inverts them internally.
"""
from __future__ import annotations

import math
from typing import Dict, List

from optimization.contracts import (
    CandidateBuilding,
    CandidateLayout,
    CampusRequirements,
)
from optimization.constraints.green import compute_green_ratio
from optimization.constraints.parking import compute_parking_ratio


# ── Helper ────────────────────────────────────────────────────────────────────

def _centre(b: CandidateBuilding):
    return b.x + b.width / 2.0, b.y + b.depth / 2.0


def _nearest_entrance_dist(bx: float, by: float, requirements: CampusRequirements) -> float:
    if not requirements.entrances:
        # No entrances defined: treat campus centre as reference
        cx, cy = requirements.site_width / 2, requirements.site_height / 2
        return math.hypot(bx - cx, by - cy)
    return min(
        math.hypot(bx - (e.x + e.width / 2), by - e.y)
        for e in requirements.entrances
    )


# ── Individual objectives ─────────────────────────────────────────────────────

def land_utilization(layout: CandidateLayout, requirements: CampusRequirements) -> float:
    """
    Fraction of site area covered by building footprints.
    Returns value in [0, 1]; higher is better.
    """
    site_area = requirements.site_width * requirements.site_height
    if site_area == 0:
        return 0.0
    built = sum(b.width * b.depth for b in layout.buildings)
    return min(1.0, built / site_area)


def green_ratio(layout: CandidateLayout, requirements: CampusRequirements) -> float:
    """Green-space ratio; higher is better."""
    return compute_green_ratio(layout, requirements)


def parking_ratio(layout: CandidateLayout, requirements: CampusRequirements) -> float:
    """Parking coverage ratio; higher is better."""
    return compute_parking_ratio(layout, requirements)


def accessibility_score(layout: CandidateLayout, requirements: CampusRequirements) -> float:
    """
    Normalised inverse of mean distance from each building to the nearest entrance.
    Returns value in [0, 1]; higher = more accessible.
    """
    if not layout.buildings:
        return 0.0

    site_diagonal = math.hypot(requirements.site_width, requirements.site_height)
    if site_diagonal == 0:
        return 1.0

    distances = []
    for b in layout.buildings:
        bx, by = _centre(b)
        d = _nearest_entrance_dist(bx, by, requirements)
        distances.append(d)

    mean_dist = sum(distances) / len(distances)
    # Normalise: 0 distance → score 1.0, full diagonal → score 0.0
    score = 1.0 - min(1.0, mean_dist / site_diagonal)
    return score


def road_efficiency(layout: CandidateLayout, requirements: CampusRequirements) -> float:
    """
    Estimate road efficiency as the inverse of total spanning tree length.

    Uses a greedy minimum spanning tree over building centres + entrances,
    normalised by site diagonal × number of nodes.

    Returns value in [0, 1]; higher = more efficient (shorter roads needed).
    """
    points: List[tuple] = []

    for b in layout.buildings:
        points.append(_centre(b))

    for e in requirements.entrances:
        points.append((e.x + e.width / 2, e.y))

    n = len(points)
    if n <= 1:
        return 1.0

    site_diagonal = math.hypot(requirements.site_width, requirements.site_height)

    # Prim's MST
    in_tree = [False] * n
    min_cost = [float("inf")] * n
    min_cost[0] = 0.0
    total_length = 0.0

    for _ in range(n):
        # Pick the node not in tree with smallest cost
        u = min(
            (i for i in range(n) if not in_tree[i]),
            key=lambda i: min_cost[i],
        )
        in_tree[u] = True
        total_length += min_cost[u]

        # Update neighbours
        for v in range(n):
            if not in_tree[v]:
                dist = math.hypot(points[u][0] - points[v][0], points[u][1] - points[v][1])
                if dist < min_cost[v]:
                    min_cost[v] = dist

    # Normalise: ideal = 0 length, worst ≈ n × site_diagonal
    max_possible = n * site_diagonal
    efficiency = 1.0 - min(1.0, total_length / max_possible) if max_possible > 0 else 1.0
    return efficiency


# ── Public API ────────────────────────────────────────────────────────────────

def compute_objectives(
    layout: CandidateLayout,
    requirements: CampusRequirements,
) -> Dict[str, float]:
    """
    Compute all five objective metric values.

    Returns a dict with keys matching LayoutMetrics fields.
    All values are in [0, 1]; higher = better.
    The constraint_score is NOT computed here — it comes from validate_layout().
    """
    return {
        "land_utilization": land_utilization(layout, requirements),
        "green_ratio": green_ratio(layout, requirements),
        "parking_ratio": parking_ratio(layout, requirements),
        "accessibility_score": accessibility_score(layout, requirements),
        "road_efficiency": road_efficiency(layout, requirements),
    }


def objectives_to_minimise(layout: CandidateLayout, requirements: CampusRequirements) -> List[float]:
    """
    Return objective values as a list in the order expected by NSGA-II.
    All values are negated/inverted so that NSGA-II minimises them.

    Order: [land_util, green, parking, accessibility, road_eff]
    """
    obj = compute_objectives(layout, requirements)
    return [
        1.0 - obj["land_utilization"],
        1.0 - obj["green_ratio"],
        1.0 - obj["parking_ratio"],
        1.0 - obj["accessibility_score"],
        1.0 - obj["road_efficiency"],
    ]
