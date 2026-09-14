"""
ml/dataset/validation.py
========================
Input validation functions for Person 1 Campus Graph Builder.
Enforces strict contract pre-conditions on incoming campus_data.
"""
from __future__ import annotations

from typing import Any, Dict, Set


def validate_campus_data(campus_data: Any) -> None:
    """
    Validates that campus_data conforms to the backend-to-P1 input contract.
    Raises ValueError with descriptive messages on any schema or numerical violation.
    """
    if not isinstance(campus_data, dict) or not campus_data:
        raise ValueError("campus_data must be a non-empty dictionary")

    # Site dimensions
    if "siteWidth" not in campus_data or "siteHeight" not in campus_data:
        raise ValueError("campus_data missing required site dimensions ('siteWidth', 'siteHeight')")

    try:
        site_width = float(campus_data["siteWidth"])
        site_height = float(campus_data["siteHeight"])
    except (TypeError, ValueError) as exc:
        raise ValueError(f"site dimensions must be valid numbers: {exc}") from exc

    if site_width <= 0.0 or site_height <= 0.0:
        raise ValueError("site dimensions must be strictly positive")

    # Buildings catalogue
    buildings = campus_data.get("buildings")
    if not isinstance(buildings, list) or len(buildings) == 0:
        raise ValueError("campus_data must contain a non-empty 'buildings' list")

    seen_building_ids: Set[int] = set()
    for idx, b in enumerate(buildings):
        if not isinstance(b, dict):
            raise ValueError(f"Building at index {idx} must be a dictionary")

        for req_field in ("id", "width", "depth"):
            if req_field not in b:
                raise ValueError(f"Building {idx} missing required field: {req_field}")

        try:
            b_id = int(b["id"])
            w = float(b["width"])
            d = float(b["depth"])
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Building {idx} fields (id, width, depth) must be valid numbers: {exc}") from exc

        if b_id in seen_building_ids:
            raise ValueError(f"Duplicate building ID in catalogue: {b_id}")
        seen_building_ids.add(b_id)

        if w <= 0.0 or d <= 0.0:
            raise ValueError(f"Building {b_id} dimensions must be positive, got width={w}, depth={d}")

        if "requiredCount" in b and b["requiredCount"] is not None:
            try:
                rc = int(b["requiredCount"])
                if rc < 1:
                    raise ValueError(f"Building {b_id} requiredCount must be >= 1")
            except (TypeError, ValueError) as exc:
                if isinstance(exc, ValueError) and "requiredCount must be >= 1" in str(exc):
                    raise
                raise ValueError(f"Building {b_id} requiredCount must be an integer >= 1") from exc

    # Constraints validation
    constraints = campus_data.get("constraints", [])
    if constraints and isinstance(constraints, list):
        for c in constraints:
            if not isinstance(c, dict):
                continue
            c_id = c.get("id", 0)
            src_id = c.get("sourceId")
            tgt_id = c.get("targetId")

            if src_id is not None and int(src_id) not in seen_building_ids:
                raise ValueError(f"Constraint {c_id} references non-existent building ID: {src_id}")
            if tgt_id is not None and int(tgt_id) not in seen_building_ids:
                raise ValueError(f"Constraint {c_id} references non-existent building ID: {tgt_id}")
