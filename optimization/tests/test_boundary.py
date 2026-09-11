"""Tests for boundary constraint checker."""
import pytest
from optimization.contracts import CandidateBuilding, CandidateLayout, CampusRequirements, Entrance
from optimization.constraints.boundary import check_boundary


def _requirements():
    return CampusRequirements(
        project_id=1, site_width=300, site_height=300,
        min_green_percent=25, min_parking_percent=10,
        min_road_width=8, min_building_gap=10,
        entrances=[Entrance(x=145, y=0, width=10)],
    )


def _building(bid=1, x=50.0, y=50.0, w=60.0, d=40.0, rot=0.0):
    return CandidateBuilding(building_id=bid, x=x, y=y, width=w, depth=d, rotation=rot,
                              name=f"B{bid}", type="academic", zone="academic")


def _layout(buildings):
    return CandidateLayout(candidate_id="t", site_width=300, site_height=300, buildings=buildings)


class TestBoundaryValid:
    def test_fully_inside_no_rotation(self):
        violations = check_boundary(_layout([_building(x=50, y=50, w=60, d=40)]), _requirements())
        assert violations == []

    def test_near_top_edge_still_valid(self):
        # top edge at y + depth = 290 + 10 = 300 — exactly on boundary
        violations = check_boundary(_layout([_building(x=50, y=260, w=60, d=40)]), _requirements())
        assert violations == []

    def test_near_right_edge_still_valid(self):
        violations = check_boundary(_layout([_building(x=240, y=50, w=60, d=40)]), _requirements())
        assert violations == []

    def test_rotated_45_inside(self):
        # A 20×20 box rotated 45° — its bounding box extends by ~14m each side
        violations = check_boundary(_layout([_building(x=140, y=140, w=20, d=20, rot=45)]), _requirements())
        assert violations == []


class TestBoundaryViolations:
    def test_off_left_edge(self):
        violations = check_boundary(_layout([_building(x=-5, y=50, w=60, d=40)]), _requirements())
        assert len(violations) == 1
        assert violations[0].type == "BOUNDARY_VIOLATION"
        assert violations[0].severity == "hard"

    def test_off_right_edge(self):
        violations = check_boundary(_layout([_building(x=260, y=50, w=60, d=40)]), _requirements())
        assert len(violations) == 1

    def test_off_top_edge(self):
        violations = check_boundary(_layout([_building(x=50, y=280, w=60, d=40)]), _requirements())
        assert len(violations) == 1

    def test_off_bottom_edge(self):
        violations = check_boundary(_layout([_building(x=50, y=-10, w=60, d=40)]), _requirements())
        assert len(violations) == 1

    def test_multiple_buildings_one_bad(self):
        good = _building(bid=1, x=50, y=50)
        bad  = _building(bid=2, x=280, y=50, w=60, d=40)
        violations = check_boundary(_layout([good, bad]), _requirements())
        assert len(violations) == 1
        assert violations[0].building_ids == [2]

    def test_rotated_building_clips_edge(self):
        # 40×40 box at (270, 150) rotated 45° — corners will exceed x=300
        violations = check_boundary(_layout([_building(x=270, y=150, w=40, d=40, rot=45)]), _requirements())
        assert len(violations) >= 1
