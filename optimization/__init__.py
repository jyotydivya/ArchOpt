"""
optimization/__init__.py
========================
Public API for the Constraint & Multi-Objective Optimization Engine (Person 3).

Usage:
    from optimization import validate_layout, optimize_layouts
    from optimization.contracts import (
        CampusRequirements, Constraint, CandidateLayout, RankedLayout
    )
"""
from optimization.validator import validate_layout
from optimization.optimizer import optimize_layouts

__all__ = ["validate_layout", "optimize_layouts"]
__version__ = "0.1.0"
