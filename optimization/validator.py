"""
optimization/validator.py
==========================
Aggregates all constraint checkers into a single ValidationResult.

Public API (P3 contract):
    validate_layout(layout, requirements, constraints) -> ValidationResult
"""
from __future__ import annotations

from typing import List

from optimization.contracts import (
    CandidateLayout,
    CampusRequirements,
    Constraint,
    ValidationResult,
    Violation,
)
from optimization.constraints.boundary import check_boundary
from optimization.constraints.overlap import check_overlap
from optimization.constraints.distance import check_distance
from optimization.constraints.zoning import check_zoning
from optimization.constraints.roads import check_roads
from optimization.constraints.green import check_green
from optimization.constraints.parking import check_parking


def validate_layout(
    layout: CandidateLayout,
    requirements: CampusRequirements,
    constraints: List[Constraint] | None = None,
) -> ValidationResult:
    """
    Run all constraint checkers and return a ValidationResult.

    Parameters
    ----------
    layout       : CandidateLayout from P2 (or mock).
    requirements : CampusRequirements from P4/P1.
    constraints  : Optional list of named Constraint objects from P4/P1.

    Returns
    -------
    ValidationResult
        feasible       — True iff no hard constraints are violated.
        violations     — All violations found (hard + soft).
        constraint_score — Proportion of hard constraints that passed [0, 1].
    """
    if constraints is None:
        constraints = []

    all_violations: List[Violation] = []

    # ── Hard constraint checkers ──────────────────────────────────────────────
    all_violations.extend(check_boundary(layout, requirements))
    all_violations.extend(check_overlap(layout, requirements))
    all_violations.extend(check_distance(layout, requirements, constraints))
    all_violations.extend(check_green(layout, requirements))
    all_violations.extend(check_parking(layout, requirements))
    all_violations.extend(check_roads(layout, requirements))

    # ── Soft constraint checkers ──────────────────────────────────────────────
    all_violations.extend(check_zoning(layout, requirements))

    # ── Feasibility & score ───────────────────────────────────────────────────
    hard_violations = [v for v in all_violations if v.severity == "hard"]
    feasible = len(hard_violations) == 0

    # Total hard checks = one per checker that can produce hard violations.
    # We count the number of unique hard-check categories attempted.
    hard_check_types = {
        "BOUNDARY_VIOLATION",
        "OVERLAP_VIOLATION",
        "GAP_VIOLATION",
        "NAMED_MIN_DISTANCE_VIOLATION",
        "NAMED_MAX_DISTANCE_VIOLATION",
        "GREEN_SPACE_VIOLATION",
        "PARKING_VIOLATION",
        "ROAD_ACCESS_VIOLATION",
    }
    hard_violation_types = {v.type for v in hard_violations}
    failed_checks = len(hard_violation_types & hard_check_types)
    total_checks = len(hard_check_types)
    constraint_score = 1.0 - (failed_checks / total_checks)

    return ValidationResult(
        feasible=feasible,
        violations=all_violations,
        constraint_score=round(constraint_score, 4),
    )
