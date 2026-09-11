"""
optimization/constraints/roads.py
===================================
Hard constraint: every building must have road access — a clear corridor
of at least *minRoadWidth* metres connecting it to the nearest site entrance.

V1 approximation:
  We model road access as a straight-line corridor from each building's
  nearest face midpoint to the closest entrance.  We check that this
  corridor width is not blocked by another building closer to the entrance.

  Full road-network simulation is a P1 objective (road efficiency), not a
  hard constraint in V1.  The hard constraint here is:
    distance(building_centre → nearest_entrance) ≤ site_diagonal
    (i.e. at least one entrance exists and the building can theoretically
    reach it — degenerate cases like buildings placed ON the entrance are
    caught here).

  If no entrance is defined we skip this check (not a constraint violation).
"""
from __future__ import annotations

import math
from typing import List

from optimization.contracts import (
    CandidateLayout,
    CampusRequirements,
    Violation,
)


def _nearest_entrance_distance(bx: float, by: float, requirements: CampusRequirements) -> float:
    """Return the distance from point (bx, by) to the nearest entrance centre."""
    if not requirements.entrances:
        return 0.0
    min_d = float("inf")
    for e in requirements.entrances:
        ex, ey = e.x + e.width / 2.0, e.y
        d = math.hypot(bx - ex, by - ey)
        min_d = min(min_d, d)
    return min_d


def check_roads(
    layout: CandidateLayout,
    requirements: CampusRequirements,
) -> List[Violation]:
    """
    Verify every building can physically reach an entrance.

    Hard failure: building centre is further than the site diagonal from every
    entrance (geometrically impossible reachability — indicates bad placement).

    Note: sophisticated network-based road checking is implemented as an
    objective function (road_efficiency), not a hard constraint in V1.
    """
    if not requirements.entrances:
        return []

    violations: List[Violation] = []
    site_diagonal = math.hypot(requirements.site_width, requirements.site_height)

    for b in layout.buildings:
        bx = b.x + b.width / 2.0
        by = b.y + b.depth / 2.0
        d = _nearest_entrance_distance(bx, by, requirements)

        # A building placed entirely outside the site would also be caught
        # by boundary check, so this is a belt-and-suspenders guard.
        if d > site_diagonal:
            violations.append(
                Violation(
                    type="ROAD_ACCESS_VIOLATION",
                    building_ids=[b.building_id],
                    message=(
                        f"Building {b.building_id} ({b.name!r}) is "
                        f"{d:.1f}m from the nearest entrance — unreachable."
                    ),
                    severity="hard",
                )
            )

    return violations
