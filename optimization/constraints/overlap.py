"""
optimization/constraints/overlap.py
=====================================
Hard constraint: buildings must not overlap, and must maintain a minimum
gap of *minBuildingGap* metres between any two footprints.

Implementation uses the Separating Axis Theorem (SAT) for rotated rectangles.
This is exact for any combination of rotations, including 0°.

Coordinate convention
---------------------
  CandidateBuilding.x, .y = bottom-left corner of the AXIS-ALIGNED bounding
  box (before rotation is applied).  Rotation is CCW about the footprint
  centre.

  Internal rectangle representation: centre (cx, cy) + half-extents + angle.
"""
from __future__ import annotations

import math
from typing import List, Tuple

from optimization.contracts import (
    CandidateBuilding,
    CandidateLayout,
    CampusRequirements,
    Violation,
)


# ── Rectangle corners ─────────────────────────────────────────────────────────

def _corners(b: CandidateBuilding) -> List[Tuple[float, float]]:
    """
    Return the four world-space corners of a (possibly rotated) building.

    Buildings are specified with (x, y) = bottom-left of bounding box,
    (width, depth) = extents, rotation = CCW degrees about the centre.
    """
    cx = b.x + b.width / 2.0
    cy = b.y + b.depth / 2.0
    hw, hd = b.width / 2.0, b.depth / 2.0
    ang = math.radians(b.rotation)
    cos_a, sin_a = math.cos(ang), math.sin(ang)

    # Four local corners (before rotation)
    local = [(-hw, -hd), (hw, -hd), (hw, hd), (-hw, hd)]

    return [
        (cx + lx * cos_a - ly * sin_a,
         cy + lx * sin_a + ly * cos_a)
        for lx, ly in local
    ]


# ── SAT helpers ───────────────────────────────────────────────────────────────

def _axes(corners: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    """Return the two unique edge-normal unit axes of a rectangle."""
    axes = []
    n = len(corners)
    seen = 0
    for i in range(n):
        if seen >= 2:
            break
        ex = corners[(i + 1) % n][0] - corners[i][0]
        ey = corners[(i + 1) % n][1] - corners[i][1]
        length = math.hypot(ex, ey)
        if length > 1e-9:
            axes.append((-ey / length, ex / length))
            seen += 1
    return axes


def _project(
    corners: List[Tuple[float, float]], axis: Tuple[float, float]
) -> Tuple[float, float]:
    dots = [c[0] * axis[0] + c[1] * axis[1] for c in corners]
    return min(dots), max(dots)


def _overlap_on_axis(
    corners_a: List[Tuple[float, float]],
    corners_b: List[Tuple[float, float]],
    axis: Tuple[float, float],
) -> float:
    """
    Return the signed overlap of two projections on *axis*.

    Positive  → they overlap by this amount.
    Negative  → they are separated by this amount (gap).
    """
    min_a, max_a = _project(corners_a, axis)
    min_b, max_b = _project(corners_b, axis)
    # Overlap = min(max_a, max_b) - max(min_a, min_b)
    return min(max_a, max_b) - max(min_a, min_b)


def _min_separation(
    corners_a: List[Tuple[float, float]],
    corners_b: List[Tuple[float, float]],
) -> float:
    """
    Return the signed separation distance between two convex polygons using SAT.

    SAT principle: two convex shapes are SEPARATED if there EXISTS an axis on
    which their projections do not overlap.

    Return value semantics:
      > 0  → separated by this distance (minimum gap = smallest separating gap found)
      = 0  → touching
      < 0  → overlapping (all axes show overlap; value = deepest overlap = max overlap across axes)

    For separated shapes: returns the gap on the MOST SEPARATING axis.
    For overlapping shapes: returns the negated minimum penetration depth.
    """
    all_axes = _axes(corners_a) + _axes(corners_b)
    gaps: List[float] = []

    for axis in all_axes:
        ov = _overlap_on_axis(corners_a, corners_b, axis)
        gap = -ov  # positive gap = separated on this axis
        gaps.append(gap)

    # If max gap > 0 → shapes are separated on at least one axis → no overlap.
    # The physical gap between them is the maximum gap (on the most separating axis).
    # If max gap < 0 → all axes show overlap → shapes intersect.
    return max(gaps)



# ── Public check ─────────────────────────────────────────────────────────────

def check_overlap(
    layout: CandidateLayout,
    requirements: CampusRequirements,
) -> List[Violation]:
    """
    Check for building overlaps and minimum-gap violations.

    Returns a list of hard Violations (one per offending pair).
    """
    violations: List[Violation] = []
    buildings = layout.buildings
    min_gap = requirements.min_building_gap

    for i in range(len(buildings)):
        for j in range(i + 1, len(buildings)):
            b_a = buildings[i]
            b_b = buildings[j]

            corners_a = _corners(b_a)
            corners_b = _corners(b_b)

            separation = _min_separation(corners_a, corners_b)

            if separation < min_gap:
                if separation <= 0:
                    msg = (
                        f"Buildings {b_a.building_id} ({b_a.name!r}) and "
                        f"{b_b.building_id} ({b_b.name!r}) overlap "
                        f"(penetration depth ≈ {-separation:.1f}m)."
                    )
                    vtype = "OVERLAP_VIOLATION"
                else:
                    msg = (
                        f"Buildings {b_a.building_id} ({b_a.name!r}) and "
                        f"{b_b.building_id} ({b_b.name!r}) are too close: "
                        f"{separation:.1f}m gap < required {min_gap}m."
                    )
                    vtype = "GAP_VIOLATION"

                violations.append(
                    Violation(
                        type=vtype,
                        building_ids=[b_a.building_id, b_b.building_id],
                        message=msg,
                        severity="hard",
                    )
                )
    return violations
