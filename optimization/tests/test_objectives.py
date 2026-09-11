"""Tests for objective functions."""
import pytest
from optimization.contracts import CandidateBuilding, CandidateLayout, CampusRequirements, Entrance
from optimization.objectives import (
    compute_objectives,
    objectives_to_minimise,
    land_utilization,
    green_ratio,
    parking_ratio,
    accessibility_score,
    road_efficiency,
)


def _req():
    return CampusRequirements(
        project_id=1, site_width=300, site_height=300,
        min_green_percent=25, min_parking_percent=10,
        min_road_width=8, min_building_gap=10,
        entrances=[Entrance(x=145, y=0, width=10)],
    )


def _b(bid, x=50.0, y=50.0, w=60.0, d=40.0, zone="academic"):
    return CandidateBuilding(building_id=bid, x=x, y=y, width=w, depth=d,
                              rotation=0.0, name=f"B{bid}", type=zone, zone=zone)


def _layout(*buildings):
    return CandidateLayout(candidate_id="t", site_width=300, site_height=300,
                            buildings=list(buildings))


class TestLandUtilization:
    def test_zero_buildings(self):
        assert land_utilization(_layout(), _req()) == 0.0

    def test_single_building(self):
        # 60×40 = 2400m² / 90000m² ≈ 0.0267
        val = land_utilization(_layout(_b(1)), _req())
        assert abs(val - 2400 / 90000) < 0.001

    def test_capped_at_one(self):
        # Many large buildings
        buildings = [_b(i, x=i * 5, y=0, w=100, d=100) for i in range(20)]
        val = land_utilization(_layout(*buildings), _req())
        assert val <= 1.0


class TestGreenRatioObjective:
    def test_returns_float_in_range(self):
        val = green_ratio(_layout(_b(1)), _req())
        assert 0.0 <= val <= 1.0

    def test_more_buildings_lower_green(self):
        few = green_ratio(_layout(_b(1)), _req())
        many = green_ratio(_layout(*[_b(i, x=i*80, y=0, w=60, d=40) for i in range(4)]), _req())
        assert few >= many


class TestParkingRatioObjective:
    def test_returns_float_in_range(self):
        val = parking_ratio(_layout(_b(1)), _req())
        assert 0.0 <= val <= 1.0


class TestAccessibilityScore:
    def test_building_at_entrance_high_score(self):
        # Building centred at the entrance (145, 20)
        b = _b(1, x=115, y=0, w=60, d=40)
        score = accessibility_score(_layout(b), _req())
        assert score > 0.9

    def test_building_far_from_entrance_lower_score(self):
        near = _b(1, x=115, y=0, w=60, d=40)
        far  = _b(2, x=10, y=250, w=60, d=40)
        near_score = accessibility_score(_layout(near), _req())
        far_score  = accessibility_score(_layout(far),  _req())
        assert near_score > far_score

    def test_empty_layout(self):
        assert accessibility_score(_layout(), _req()) == 0.0

    def test_no_entrances_uses_centre(self):
        req = CampusRequirements(
            project_id=1, site_width=300, site_height=300,
            min_green_percent=25, min_parking_percent=10,
            min_road_width=8, min_building_gap=10, entrances=[],
        )
        val = accessibility_score(_layout(_b(1, x=120, y=120)), req)
        assert 0.0 <= val <= 1.0


class TestRoadEfficiency:
    def test_returns_float_in_range(self):
        val = road_efficiency(_layout(_b(1), _b(2, x=200)), _req())
        assert 0.0 <= val <= 1.0

    def test_single_building_perfect(self):
        # With an entrance, there's 1 building + 1 entrance = 2-node MST.
        # Road efficiency will be high but not exactly 1.0 (a road is needed).
        val = road_efficiency(_layout(_b(1, x=120, y=0)), _req())
        assert 0.0 < val <= 1.0


class TestComputeObjectives:
    def test_returns_all_keys(self):
        obj = compute_objectives(_layout(_b(1)), _req())
        expected_keys = {
            "land_utilization", "green_ratio", "parking_ratio",
            "accessibility_score", "road_efficiency"
        }
        assert set(obj.keys()) == expected_keys

    def test_all_values_in_range(self):
        obj = compute_objectives(_layout(_b(1)), _req())
        for key, val in obj.items():
            assert 0.0 <= val <= 1.0, f"{key}={val} out of [0,1]"


class TestObjectivesToMinimise:
    def test_inverts_values(self):
        obj = compute_objectives(_layout(_b(1)), _req())
        min_vals = objectives_to_minimise(_layout(_b(1)), _req())
        assert len(min_vals) == 5
        # Each minimise value = 1 - metric value
        assert abs(min_vals[0] - (1 - obj["land_utilization"])) < 1e-9

    def test_all_in_range(self):
        min_vals = objectives_to_minimise(_layout(_b(1)), _req())
        for v in min_vals:
            assert 0.0 <= v <= 1.0
