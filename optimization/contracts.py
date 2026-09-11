"""
optimization/contracts.py
=========================
Re-exports all shared contracts from contracts/layout.py so that the
optimization package can be imported without needing the contracts/ directory
on the Python path.

Also defines any optimization-internal types not in the shared contracts.
"""
import sys
import os

# Allow importing from contracts/ at repo root even when running from optimization/
_repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

from contracts.layout import (   # noqa: F401  (re-exported)
    Entrance,
    CampusRequirements,
    Building,
    Constraint,
    SpatialRelationship,
    CampusGraph,
    CandidateBuilding,
    CandidateLayout,
    Violation,
    ValidationResult,
    LayoutMetrics,
    RankedLayout,
    BlueprintBuilding,
    Road,
    Area,
    Blueprint,
)

__all__ = [
    "Entrance",
    "CampusRequirements",
    "Building",
    "Constraint",
    "SpatialRelationship",
    "CampusGraph",
    "CandidateBuilding",
    "CandidateLayout",
    "Violation",
    "ValidationResult",
    "LayoutMetrics",
    "RankedLayout",
    "BlueprintBuilding",
    "Road",
    "Area",
    "Blueprint",
]
