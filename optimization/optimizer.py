"""
optimization/optimizer.py
==========================
Top-level orchestrator — the single function P4 calls.

Public API (P3 contract):
    optimize_layouts(candidates, requirements, constraints, top_k=5) -> list[RankedLayout]

Pipeline:
    CandidateLayout[]
        ↓
    validate_layout()  (per candidate)
        ↓
    compute_objectives()
        ↓
    rank_population()  (NSGA-II)
        ↓
    build_ranked_layouts()
        ↓
    list[RankedLayout]  (top_k)

Running as __main__ executes a full demo with mock data and writes SVG output.
"""
from __future__ import annotations

import json
import os
import time
from typing import List

from optimization.contracts import (
    CandidateLayout,
    CampusRequirements,
    Constraint,
    RankedLayout,
    ValidationResult,
)
from optimization.validator import validate_layout
from optimization.objectives import objectives_to_minimise
from optimization.nsga2 import rank_population
from optimization.ranking import build_ranked_layouts


def optimize_layouts(
    candidates: List[CandidateLayout],
    requirements: CampusRequirements,
    constraints: List[Constraint] | None = None,
    top_k: int = 5,
) -> List[RankedLayout]:
    """
    Validate, rank, and return the top *top_k* campus layouts.

    Parameters
    ----------
    candidates   : list of CandidateLayout (from P2 or mock).
    requirements : CampusRequirements (from P4 / P1 data layer).
    constraints  : optional named Constraint list (from P4 / P1 data layer).
    top_k        : number of ranked plans to return (default 5).

    Returns
    -------
    list[RankedLayout] — length ≤ top_k, sorted by rank (1 = best).
    """
    if constraints is None:
        constraints = []

    if not candidates:
        return []

    # ── Step 1: Validate all candidates ──────────────────────────────────────
    validations: dict[str, ValidationResult] = {}
    for candidate in candidates:
        validations[candidate.candidate_id] = validate_layout(
            candidate, requirements, constraints
        )

    # ── Step 2: Compute objective vectors (to minimise) ───────────────────────
    objective_vectors = [
        objectives_to_minimise(c, requirements) for c in candidates
    ]

    # ── Step 3: NSGA-II ranking ───────────────────────────────────────────────
    ranked_indices = rank_population(objective_vectors, use_pymoo=True)

    # ── Step 4: Assemble RankedLayout objects ─────────────────────────────────
    ranked_layouts = build_ranked_layouts(
        candidates, requirements, validations, ranked_indices, top_k=top_k
    )

    return ranked_layouts


# ─────────────────────────────────────────────────────────────────────────────
# Demo / __main__
# ─────────────────────────────────────────────────────────────────────────────

def _ranked_layout_to_dict(rl: RankedLayout) -> dict:
    """Convert RankedLayout to a JSON-serialisable dict."""
    return {
        "candidateId": rl.candidate_id,
        "rank": rl.rank,
        "feasible": rl.feasible,
        "siteWidth": rl.site_width,
        "siteHeight": rl.site_height,
        "buildings": [
            {
                "buildingId": b.building_id,
                "name": b.name,
                "type": b.type,
                "zone": b.zone,
                "x": b.x,
                "y": b.y,
                "width": b.width,
                "depth": b.depth,
                "height": b.height,
                "rotation": b.rotation,
                "floorCount": b.floor_count,
            }
            for b in rl.buildings
        ],
        "metrics": {
            "landUtilization": rl.metrics.land_utilization,
            "greenRatio": rl.metrics.green_ratio,
            "parkingRatio": rl.metrics.parking_ratio,
            "accessibilityScore": rl.metrics.accessibility_score,
            "roadEfficiency": rl.metrics.road_efficiency,
            "constraintScore": rl.metrics.constraint_score,
        },
        "violations": (
            [
                {
                    "type": v.type,
                    "buildingIds": v.building_ids,
                    "message": v.message,
                    "severity": v.severity,
                }
                for v in rl.validation.violations
            ]
            if rl.validation
            else []
        ),
    }


if __name__ == "__main__":
    import sys

    # Add repo root to path
    _here = os.path.dirname(os.path.abspath(__file__))
    _root = os.path.dirname(_here)
    if _root not in sys.path:
        sys.path.insert(0, _root)

    from optimization.mock_data import generate_mock_candidates, get_demo_requirements
    from optimization.visualize import render_comparison_html, render_layout_svg

    print("=" * 60)
    print("  AI Campus Planner — Optimization Engine Demo")
    print("  Person 3: Constraint & NSGA-II Module")
    print("=" * 60)

    requirements = get_demo_requirements()
    print(f"\n[Site] {requirements.site_width}m x {requirements.site_height}m")
    print(f"   Min green:   {requirements.min_green_percent}%")
    print(f"   Min parking: {requirements.min_parking_percent}%")
    print(f"   Min gap:     {requirements.min_building_gap}m")
    print(f"   Entrances:   {len(requirements.entrances)}")

    print("\n[1/3] Generating 100 mock candidate layouts...")
    t0 = time.time()
    candidates = generate_mock_candidates(100, requirements, seed=42)
    print(f"   Done in {time.time() - t0:.2f}s")

    print("\n[2/3] Running optimization pipeline (validate -> objectives -> NSGA-II)...")
    t1 = time.time()
    top_layouts = optimize_layouts(candidates, requirements, top_k=5)
    print(f"   Done in {time.time() - t1:.2f}s")

    print(f"\n[3/3] Top {len(top_layouts)} Ranked Layouts:")
    print(f"   {'Rank':<5} {'ID':<20} {'Feasible':<10} {'LandUtil':<10} {'Green':<8} {'Parking':<10} {'Access':<8} {'Score':<8}")
    print("   " + "-" * 79)
    for rl in top_layouts:
        m = rl.metrics
        feas = "[OK]" if rl.feasible else "[X]"
        print(
            f"   {rl.rank:<5} {rl.candidate_id:<20} {feas:<10} "
            f"{m.land_utilization:<10.3f} {m.green_ratio:<8.3f} "
            f"{m.parking_ratio:<10.3f} {m.accessibility_score:<8.3f} "
            f"{m.constraint_score:<8.3f}"
        )

    # ── Write output files ────────────────────────────────────────────────────
    out_dir = os.path.join(_root, "output")
    os.makedirs(out_dir, exist_ok=True)

    # JSON
    json_path = os.path.join(out_dir, "ranked_layouts.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump([_ranked_layout_to_dict(rl) for rl in top_layouts], f, indent=2)
    print(f"\n[SAVED] JSON -> {json_path}")

    # Individual SVGs
    for rl in top_layouts:
        svg_path = os.path.join(out_dir, f"layout_{rl.rank}.svg")
        with open(svg_path, "w", encoding="utf-8") as f:
            f.write(render_layout_svg(rl, requirements))
        print(f"   SVG rank {rl.rank} -> {svg_path}")

    # Comparison HTML
    html_path = os.path.join(out_dir, "comparison.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(render_comparison_html(top_layouts, requirements))
    print(f"\n[HTML] Interactive comparison -> {html_path}")
    print("   Open this file in a browser to view all 5 layouts side-by-side.")
    print("\nDone!")
