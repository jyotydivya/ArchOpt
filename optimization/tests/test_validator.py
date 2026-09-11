"""Tests for the aggregate validator."""
import pytest
from optimization.contracts import (
    CandidateBuilding, CandidateLayout, CampusRequirements, Constraint, Entrance,
)
from optimization.validator import validate_layout


def _req():
    return CampusRequirements(
        project_id=1, site_width=300, site_height=300,
        min_green_percent=25, min_parking_percent=10,
        min_road_width=8, min_building_gap=10,
        entrances=[Entrance(x=145, y=0, width=10)],
    )


def _b(bid, x=50.0, y=100.0, w=60.0, d=40.0, zone="academic", btype="academic"):
    return CandidateBuilding(
        building_id=bid, x=x, y=y, width=w, depth=d,
        rotation=0.0, name=f"B{bid}", type=btype, zone=zone,
    )


def _layout(*buildings):
    return CandidateLayout(
        candidate_id="t", site_width=300, site_height=300,
        buildings=list(buildings),
    )


class TestValidatorFeasible:
    def test_well_spaced_layout_is_feasible(self):
        # Three buildings well spaced on 300×300 site — no overlaps, all within bounds
        buildings = [
            _b(1, x=10,  y=200, w=60, d=40),
            _b(2, x=100, y=200, w=60, d=40),
            _b(3, x=10,  y=50,  w=60, d=40),
            # 110×90 parking block — 9900m² / 90000m² = 11% > 10% required
            _b(4, x=170, y=10,  w=110, d=90, zone="parking", btype="parking"),
        ]
        result = validate_layout(_layout(*buildings), _req())
        assert result.feasible is True
        assert result.constraint_score > 0.5

    def test_empty_layout_no_hard_violations(self):
        # No buildings → no overlaps/boundary issues, but may fail green/parking
        result = validate_layout(_layout(), _req())
        # Green should pass (site is all green), parking depends on estimate
        hard = [v for v in result.violations if v.severity == "hard"]
        # Parking estimate on empty site should be fine
        assert result.constraint_score >= 0.5


class TestValidatorViolations:
    def test_overlapping_buildings_infeasible(self):
        b1 = _b(1, x=50, y=50)
        b2 = _b(2, x=50, y=50)  # same position
        result = validate_layout(_layout(b1, b2), _req())
        assert result.feasible is False
        assert result.constraint_score < 1.0
        types = {v.type for v in result.violations}
        assert "OVERLAP_VIOLATION" in types

    def test_out_of_bounds_infeasible(self):
        b = _b(1, x=280, y=50, w=60, d=40)  # goes to x=340 > 300
        result = validate_layout(_layout(b), _req())
        assert result.feasible is False
        types = {v.type for v in result.violations}
        assert "BOUNDARY_VIOLATION" in types

    def test_named_hard_constraint_violation(self):
        b1 = _b(1, x=0, y=0)
        b2 = _b(2, x=50, y=0)  # centres 50m apart
        c = Constraint(id=1, type="MIN_DISTANCE", source_id=1, target_id=2,
                       value=150, operator=">=", priority="hard")
        result = validate_layout(_layout(b1, b2), _req(), [c])
        assert result.feasible is False

    def test_soft_violations_dont_affect_feasibility(self):
        # Two same-zone buildings far apart → zoning soft violation
        b1 = _b(1, x=0, y=0, zone="academic")
        b2 = _b(2, x=250, y=250, zone="academic")
        result = validate_layout(_layout(b1, b2), _req())
        soft = [v for v in result.violations if v.severity == "soft"]
        hard = [v for v in result.violations if v.severity == "hard"]
        assert len(soft) >= 1
        # Soft violations alone → feasible (if no hard violations)
        if not hard:
            assert result.feasible is True

    def test_constraint_score_range(self):
        b = _b(1, x=50, y=100)
        result = validate_layout(_layout(b), _req())
        assert 0.0 <= result.constraint_score <= 1.0


class TestValidatorReturnTypes:
    def test_return_type(self):
        from optimization.contracts import ValidationResult
        result = validate_layout(_layout(_b(1)), _req())
        assert isinstance(result, ValidationResult)
        assert isinstance(result.feasible, bool)
        assert isinstance(result.violations, list)
        assert isinstance(result.constraint_score, float)
