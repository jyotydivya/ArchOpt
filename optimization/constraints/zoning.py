"""
optimization/constraints/zoning.py
=====================================
Soft constraint: buildings belonging to the same zone should be spatially
clustered together, not scattered across the campus.

Algorithm:
  For each zone group (≥ 2 buildings), compute the pairwise centroid distances.
  If the maximum intra-zone distance exceeds the threshold (default 150 m for
  a 300 × 300 site), flag the most distant pair.

The threshold scales with site size: threshold = 0.5 × min(siteWidth, siteHeight).
"""
from __future__ import annotations

import math
from collections import defaultdict
from typing import Dict, List

from optimization.contracts import (
    CandidateBuilding,
    CandidateLayout,
    CampusRequirements,
    Violation,
)


def _centre(b: CandidateBuilding):
    return b.x + b.width / 2.0, b.y + b.depth / 2.0


def _distance(b_a: CandidateBuilding, b_b: CandidateBuilding) -> float:
    ax, ay = _centre(b_a)
    bx, by = _centre(b_b)
    return math.hypot(ax - bx, ay - by)


def check_zoning(
    layout: CandidateLayout,
    requirements: CampusRequirements,
) -> List[Violation]:
    """
    Check that buildings of the same zone are reasonably clustered.

    Returns soft Violations for widely separated same-zone buildings.
    """
    violations: List[Violation] = []

    threshold = 0.5 * min(requirements.site_width, requirements.site_height)

    zone_groups: Dict[str, List[CandidateBuilding]] = defaultdict(list)
    for b in layout.buildings:
        if b.zone:
            zone_groups[b.zone].append(b)

    for zone, buildings in zone_groups.items():
        if len(buildings) < 2:
            continue
        for i in range(len(buildings)):
            for j in range(i + 1, len(buildings)):
                dist = _distance(buildings[i], buildings[j])
                if dist > threshold:
                    violations.append(
                        Violation(
                            type="ZONING_VIOLATION",
                            building_ids=[
                                buildings[i].building_id,
                                buildings[j].building_id,
                            ],
                            message=(
                                f"Zone '{zone}': buildings "
                                f"{buildings[i].building_id} and "
                                f"{buildings[j].building_id} are "
                                f"{dist:.1f}m apart — same-zone buildings "
                                f"should be within {threshold:.0f}m of each other."
                            ),
                            severity="soft",
                        )
                    )
    return violations
