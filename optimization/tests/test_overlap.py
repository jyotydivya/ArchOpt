"""Tests for overlap / gap constraint checker."""
import pytest
from optimization.contracts import CandidateBuilding, CandidateLayout, CampusRequirements, Entrance
from optimization.constraints.overlap import check_overlap


def _requirements(min_gap=10.0):
    return CampusRequirements(
        project_id=1, site_width=300, site_height=300,
        min_green_percent=25, min_parking_percent=10,
        min_road_width=8, min_building_gap=min_gap,
    )


def _b(bid, x, y, w=60.0, d=40.0, rot=0.0):
    return CandidateBuilding(building_id=bid, x=x, y=y, width=w, depth=d,
                              rotation=rot, name=f"B{bid}", type="academic", zone="academic")


def _layout(buildings, site_w=300, site_h=300):
    return CandidateLayout(candidate_id="t", site_width=site_w, site_height=site_h, buildings=buildings)


class TestNoOverlap:
    def test_well_separated_pair(self):
        # 20m gap between buildings
        violations = check_overlap(_layout([_b(1, 0, 0), _b(2, 100, 0)]), _requirements())
        assert violations == []

    def test_single_building(self):
        violations = check_overlap(_layout([_b(1, 50, 50)]), _requirements())
        assert violations == []

    def test_zero_buildings(self):
        violations = check_overlap(_layout([]), _requirements())
        assert violations == []

    def test_exactly_at_min_gap(self):
        # Building 1: x=[0,60], Building 2: x=[70,130], gap = 10 exactly
        violations = check_overlap(_layout([_b(1, 0, 0), _b(2, 70, 0)]), _requirements(min_gap=10))
        assert violations == []


class TestOverlapViolations:
    def test_direct_overlap(self):
        # Both buildings placed at same position
        violations = check_overlap(_layout([_b(1, 50, 50), _b(2, 50, 50)]), _requirements())
        assert len(violations) == 1
        assert violations[0].type == "OVERLAP_VIOLATION"
        assert violations[0].severity == "hard"
        assert set(violations[0].building_ids) == {1, 2}

    def test_partial_overlap(self):
        # B1 at x=[0,60], B2 at x=[50,110] — overlap of 10m
        violations = check_overlap(_layout([_b(1, 0, 0), _b(2, 50, 0)]), _requirements())
        assert len(violations) == 1
        assert violations[0].type == "OVERLAP_VIOLATION"

    def test_gap_too_small(self):
        # B1: x=[0..60], B2 starts at x=67 → gap = 7m < min_gap=10
        violations = check_overlap(_layout([_b(1, 0, 0), _b(2, 67, 0)]), _requirements(min_gap=10))
        assert len(violations) == 1
        assert violations[0].type == "GAP_VIOLATION"

    def test_multiple_pairs_overlapping(self):
        buildings = [_b(i, i * 30, 0) for i in range(4)]
        # 30m spacing with 60m wide buildings → all adjacent pairs overlap
        violations = check_overlap(_layout(buildings), _requirements())
        assert len(violations) >= 3

    def test_rotated_buildings_no_overlap(self):
        # b1: x=[0..60], y=[0..40]. b2 starts at x=120 (well separated)
        b1 = _b(1, 0, 0, w=60, d=40, rot=0)
        b2 = _b(2, 120, 0, w=60, d=40, rot=90)  # rotated but still far away
        violations = check_overlap(_layout([b1, b2]), _requirements())
        assert violations == []

    def test_rotated_buildings_overlap(self):
        b1 = _b(1, 100, 100, w=60, d=40, rot=0)
        b2 = _b(2, 110, 110, w=60, d=40, rot=45)
        violations = check_overlap(_layout([b1, b2]), _requirements())
        assert len(violations) >= 1
