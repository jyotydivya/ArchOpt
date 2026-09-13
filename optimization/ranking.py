"""
optimization/ranking.py
========================
Post-NSGA-II logic: build RankedLayout objects with full LayoutMetrics.

Takes the sorted (index, front, crowding_dist) list from nsga2.py,
filters to feasible-only layouts, and assembles the final output list.
"""
from __future__ import annotations

from typing import Dict, List, Tuple

from optimization.contracts import (
    CandidateLayout,
    CampusRequirements,
    LayoutMetrics,
    RankedLayout,
    ValidationResult,
)
from optimization.objectives import compute_objectives


def build_ranked_layouts(
    candidates: List[CandidateLayout],
    requirements: CampusRequirements,
    validations: Dict[str, ValidationResult],
    ranked_indices: List[Tuple[int, int, float]],
    top_k: int = 5,
) -> List[RankedLayout]:
    """
    Assemble the final top-k RankedLayout list.

    Parameters
    ----------
    candidates      : all candidate layouts (from P2 / mock).
    requirements    : campus requirements.
    validations     : dict mapping candidate_id → ValidationResult.
    ranked_indices  : output of nsga2.rank_population — sorted (idx, front, cd).
    top_k           : number of plans to return.

    Returns
    -------
    List of RankedLayout, length ≤ top_k, rank starting at 1.
    Feasible layouts are preferred; if fewer than top_k feasible plans exist,
    the best infeasible plans fill the remaining slots.
    """
    # Partition feasible vs infeasible
    feasible_ranked = []
    infeasible_ranked = []

    for global_idx, front_num, crowding_dist in ranked_indices:
        candidate = candidates[global_idx]
        val_result = validations.get(candidate.candidate_id)
        is_feasible = val_result.feasible if val_result else False

        if is_feasible:
            feasible_ranked.append((global_idx, front_num, crowding_dist))
        else:
            infeasible_ranked.append((global_idx, front_num, crowding_dist))

    # Build final selection: feasible first, then infeasible if needed
    selected = feasible_ranked[:top_k]
    if len(selected) < top_k:
        selected += infeasible_ranked[: top_k - len(selected)]

    # Assemble RankedLayout objects
    ranked_layouts: List[RankedLayout] = []
    for rank, (global_idx, front_num, _) in enumerate(selected, start=1):
        candidate = candidates[global_idx]
        val_result = validations.get(candidate.candidate_id)
        obj = compute_objectives(candidate, requirements)
        constraint_score = val_result.constraint_score if val_result else 0.0

        metrics = LayoutMetrics(
            land_utilization=round(obj["land_utilization"], 4),
            green_ratio=round(obj["green_ratio"], 4),
            parking_ratio=round(obj["parking_ratio"], 4),
            accessibility_score=round(obj["accessibility_score"], 4),
            road_efficiency=round(obj["road_efficiency"], 4),
            constraint_score=round(constraint_score, 4),
        )

        ranked_layouts.append(
            RankedLayout(
                candidate_id=candidate.candidate_id,
                rank=rank,
                feasible=val_result.feasible if val_result else False,
                buildings=candidate.buildings,
                metrics=metrics,
                site_width=candidate.site_width,
                site_height=candidate.site_height,
                validation=val_result,
            )
        )

    return ranked_layouts
