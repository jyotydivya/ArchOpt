"""
optimization/constraints/boundary.py
=====================================
Hard constraint: every building footprint must lie entirely within the
campus site boundary [0, siteWidth] × [0, siteHeight].

Supports rotated buildings via corner projection.
"""
from __future__ import annotations

import math
from typing import List

from optimization.contracts import (
    CandidateLayout,
    CampusRequirements,
    Violation,
)


def _rotated_corners(x: float, y: float, w: float, d: float, rot_deg: float):
    """
    Return the four corners of a rotated rectangle.

    The rectangle's local origin is its bottom-left corner (x, y).
    Rotation is counter-clockwise in degrees about the rectangle centre.

    Returns: list of (cx, cy) tuples.
    """
    cx = x + w / 2.0
    cy = y + d / 2.0
    angle = math.radians(rot_deg)
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)

    half_w, half_d = w / 2.0, d / 2.0
    local_corners = [
        (-half_w, -half_d),
        ( half_w, -half_d),
        ( half_w,  half_d),
        (-half_w,  half_d),
    ]

    corners = []
    for lx, ly in local_corners:
        rx = cx + lx * cos_a - ly * sin_a
        ry = cy + lx * sin_a + ly * cos_a
        corners.append((rx, ry))
    return corners


def check_boundary(
    layout: CandidateLayout,
    requirements: CampusRequirements,
) -> List[Violation]:
    """
    Check that every building in *layout* is fully inside the site boundary.

    Returns a (possibly empty) list of hard Violations.
    """
    violations: List[Violation] = []
    sw = requirements.site_width
    sh = requirements.site_height

    for b in layout.buildings:
        corners = _rotated_corners(b.x, b.y, b.width, b.depth, b.rotation)
        out_of_bounds = any(
            cx < 0 or cx > sw or cy < 0 or cy > sh
            for cx, cy in corners
        )
        if out_of_bounds:
            violations.append(
                Violation(
                    type="BOUNDARY_VIOLATION",
                    building_ids=[b.building_id],
                    message=(
                        f"Building {b.building_id} ({b.name!r}) extends "
                        f"outside the site boundary "
                        f"({sw}m × {sh}m)."
                    ),
                    severity="hard",
                )
            )
    return violations
