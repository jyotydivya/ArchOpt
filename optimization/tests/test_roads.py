"""Tests for road-access constraint checker."""
import pytest
from optimization.contracts import CandidateBuilding, CandidateLayout, CampusRequirements, Entrance
from optimization.constraints.roads import check_roads


def _req(entrances=None):
    return CampusRequirements(
        project_id=1, site_width=300, site_height=300,
        min_green_percent=25, min_parking_percent=10,
        min_road_width=8, min_building_gap=10,
        entrances=entrances or [Entrance(x=145, y=0, width=10)],
    )


def _b(bid, x=50.0, y=50.0, w=60.0, d=40.0):
    return CandidateBuilding(building_id=bid, x=x, y=y, width=w, depth=d,
                              rotation=0.0, name=f"B{bid}", type="academic", zone="academic")


def _layout(*buildings):
    return CandidateLayout(candidate_id="t", site_width=300, site_height=300,
                            buildings=list(buildings))


class TestRoadsValid:
    def test_building_near_entrance(self):
        violations = check_roads(_layout(_b(1, 50, 50)), _req())
        assert violations == []

    def test_no_entrances_skips_check(self):
        # With no entrances defined, check is skipped (not applicable)
        violations = check_roads(_layout(_b(1, 50, 50)), _req(entrances=[]))
        assert violations == []

    def test_building_on_far_side_still_reachable(self):
        # 300×300 site diagonal ≈ 424m; any point on-site is within diagonal
        violations = check_roads(_layout(_b(1, 280, 280)), _req())
        assert violations == []


class TestRoadsViolation:
    def test_unreachable_beyond_diagonal(self):
        """
        Simulate an unreachable building by using a tiny site (1×1) where
        the diagonal is ~1.4m and the building is 500m away.
        """
        req = CampusRequirements(
            project_id=1, site_width=1, site_height=1,
            min_green_percent=0, min_parking_percent=0,
            min_road_width=8, min_building_gap=0,
            entrances=[Entrance(x=0, y=0, width=1)],
        )
        # Place building centre at (500, 500) — clearly beyond diagonal
        b = CandidateBuilding(building_id=1, x=499, y=499, width=1, depth=1,
                               rotation=0, name="B1", type="academic", zone="academic")
        layout = CandidateLayout(candidate_id="t", site_width=1, site_height=1, buildings=[b])
        violations = check_roads(layout, req)
        assert len(violations) == 1
        assert violations[0].type == "ROAD_ACCESS_VIOLATION"
