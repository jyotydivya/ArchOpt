"""
optimization/constraints/parking.py
=====================================
Hard constraint: the total parking area must be at least
*minParkingPercent* % of the total site area.

V1 approximation:
  Buildings of type "parking" contribute their full footprint (w × d).
  We also estimate surface parking from unbuilt space. This surface
  parking estimate is added to any explicit parking structures.
"""
from __future__ import annotations

from typing import List

from optimization.contracts import (
    CandidateLayout,
    CampusRequirements,
    Violation,
)


def compute_parking_ratio(
    layout: CandidateLayout,
    requirements: CampusRequirements,
) -> float:
    """
    Return the estimated parking ratio ∈ [0, 1].

    Exposed so the objective function can reuse it.
    """
    site_area = requirements.site_width * requirements.site_height

    # Explicit parking buildings
    parking_area = sum(
        b.width * b.depth
        for b in layout.buildings
        if b.type in ("parking", "car_park") or b.zone == "parking"
    )

    # Estimate surface parking from unbuilt space
    built_area = sum(b.width * b.depth for b in layout.buildings)
    road_est = 0.08 * site_area
    unbuilt = max(0.0, site_area - built_area - road_est)
    surface_parking = unbuilt * 0.5
    
    return (parking_area + surface_parking) / site_area


def check_parking(
    layout: CandidateLayout,
    requirements: CampusRequirements,
) -> List[Violation]:
    """
    Check that parking area meets the minimum requirement.

    Returns a list with at most one hard Violation.
    """
    violations: List[Violation] = []
    parking_ratio = compute_parking_ratio(layout, requirements)
    required = requirements.min_parking_percent / 100.0

    if parking_ratio < required:
        violations.append(
            Violation(
                type="PARKING_VIOLATION",
                building_ids=[],
                message=(
                    f"Estimated parking ratio {parking_ratio:.1%} is below "
                    f"the required {required:.1%} "
                    f"({requirements.min_parking_percent}% of site)."
                ),
                severity="hard",
            )
        )
    return violations
