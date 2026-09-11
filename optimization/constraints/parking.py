"""
optimization/constraints/parking.py
=====================================
Hard constraint: the total parking area must be at least
*minParkingPercent* % of the total site area.

V1 approximation:
  Buildings of type "parking" contribute their full footprint (w × d).
  If no parking buildings are present, we check that the layout leaves
  enough unbuilt space for the required parking fraction.

  For a campus prototype, a "parking" zone building or explicit parking area
  polygon should be present for the constraint to pass with a real layout.
  Without an explicit parking building the check uses the same estimate
  approach as green.py (lenient, avoids false positives during early dev).
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

    if parking_area > 0:
        return parking_area / site_area

    # Fallback: estimate from unbuilt space
    built_area = sum(b.width * b.depth for b in layout.buildings)
    road_est = 0.08 * site_area
    unbuilt = max(0.0, site_area - built_area - road_est)
    # Assume half of unbuilt can be parking
    return (unbuilt * 0.5) / site_area


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
