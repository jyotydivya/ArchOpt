"""
optimization/constraints/distance.py
======================================
Evaluates named MIN_DISTANCE / MAX_DISTANCE constraints between specific
building pairs as specified in the project's Constraint list.

Distance is measured centre-to-centre.
"""
from __future__ import annotations

import math
from typing import Dict, List

from optimization.contracts import (
    CandidateBuilding,
    CandidateLayout,
    CampusRequirements,
    Constraint,
    Violation,
)


def _centre(b: CandidateBuilding):
    return b.x + b.width / 2.0, b.y + b.depth / 2.0


def _distance(b_a: CandidateBuilding, b_b: CandidateBuilding) -> float:
    ax, ay = _centre(b_a)
    bx, by = _centre(b_b)
    return math.hypot(ax - bx, ay - by)


def check_distance(
    layout: CandidateLayout,
    requirements: CampusRequirements,
    constraints: List[Constraint],
) -> List[Violation]:
    """
    Evaluate every named MIN_DISTANCE / MAX_DISTANCE constraint.

    Returns a list of Violations (severity = constraint.priority).
    """
    violations: List[Violation] = []

    # Index buildings by ID for O(1) look-up
    bld_map: Dict[int, CandidateBuilding] = {
        b.building_id: b for b in layout.buildings
    }

    for c in constraints:
        if c.type not in ("MIN_DISTANCE", "MAX_DISTANCE"):
            continue

        b_a = bld_map.get(c.source_id)
        b_b = bld_map.get(c.target_id)

        if b_a is None or b_b is None:
            # Buildings not present in this layout — skip silently.
            continue

        dist = _distance(b_a, b_b)
        required = c.value
        violated = False

        if c.type == "MIN_DISTANCE" and dist < required:
            violated = True
            msg = (
                f"MIN_DISTANCE violated: buildings {c.source_id} and "
                f"{c.target_id} are {dist:.1f}m apart, "
                f"minimum required is {required}m."
            )
        elif c.type == "MAX_DISTANCE" and dist > required:
            violated = True
            msg = (
                f"MAX_DISTANCE violated: buildings {c.source_id} and "
                f"{c.target_id} are {dist:.1f}m apart, "
                f"maximum allowed is {required}m."
            )

        if violated:
            violations.append(
                Violation(
                    type=f"NAMED_{c.type}_VIOLATION",
                    building_ids=[c.source_id, c.target_id],
                    message=msg,
                    severity=c.priority,  # "hard" or "soft"
                )
            )

    return violations
