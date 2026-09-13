"""
optimization/constraints/green.py
===================================
Hard constraint: the total green-space coverage must be at least
*minGreenPercent* % of the total site area.

Green-space estimate (V1):
  green_area = site_area − built_area − estimated_road_area − parking_area

  built_area   = sum of building footprints (w × d, rotation-invariant)
  road_area    = estimated as 8% of site (conservative; road efficiency
                 objective handles optimisation)
  parking_area = estimated from minParkingPercent

  If green_ratio < minGreenPercent / 100, this is a hard violation.
"""
from __future__ import annotations

from typing import List

from optimization.contracts import (
    CandidateLayout,
    CampusRequirements,
    Violation,
)


def compute_green_ratio(
    layout: CandidateLayout,
    requirements: CampusRequirements,
) -> float:
    """
    Return the estimated green-space ratio ∈ [0, 1].

    This is exposed separately so the objective function can reuse it.
    """
    site_area = requirements.site_width * requirements.site_height
    built_area = sum(b.width * b.depth for b in layout.buildings)

    # Conservative road area estimate (8% of site)
    road_area_est = 0.08 * site_area

    # Parking area reserved from requirements
    parking_area_est = (requirements.min_parking_percent / 100.0) * site_area

    occupied = built_area + road_area_est + parking_area_est
    green_area = max(0.0, site_area - occupied)
    return green_area / site_area


def check_green(
    layout: CandidateLayout,
    requirements: CampusRequirements,
) -> List[Violation]:
    """
    Check that estimated green-space meets the minimum requirement.

    Returns a list with at most one hard Violation.
    """
    violations: List[Violation] = []
    green_ratio = compute_green_ratio(layout, requirements)
    required = requirements.min_green_percent / 100.0

    if green_ratio < required:
        violations.append(
            Violation(
                type="GREEN_SPACE_VIOLATION",
                building_ids=[],
                message=(
                    f"Estimated green-space ratio {green_ratio:.1%} is below "
                    f"the required {required:.1%} "
                    f"({requirements.min_green_percent}% of site)."
                ),
                severity="hard",
            )
        )
    return violations
