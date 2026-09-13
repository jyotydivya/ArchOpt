"""Tests for green-space constraint checker."""
import pytest
from optimization.contracts import CandidateBuilding, CandidateLayout, CampusRequirements
from optimization.constraints.green import check_green, compute_green_ratio


def _req(min_green=25):
    return CampusRequirements(
        project_id=1, site_width=300, site_height=300,
        min_green_percent=min_green, min_parking_percent=10,
        min_road_width=8, min_building_gap=10,
    )


def _b(bid, w=60.0, d=40.0):
    return CandidateBuilding(building_id=bid, x=10*bid, y=10*bid, width=w, depth=d,
                              rotation=0.0, name=f"B{bid}", type="academic", zone="academic")


def _layout(*buildings):
    return CandidateLayout(candidate_id="t", site_width=300, site_height=300,
                            buildings=list(buildings))


class TestGreenRatio:
    def test_few_small_buildings_high_green(self):
        # 2 buildings × 60×40 = 4800m² on 90000m² site → ~5% built
        ratio = compute_green_ratio(_layout(_b(1), _b(2)), _req())
        assert ratio > 0.25  # plenty of green

    def test_no_buildings_max_green(self):
        ratio = compute_green_ratio(_layout(), _req())
        # Subtract road_est (8%) + parking_est (10%) → ~82%
        assert ratio > 0.5

    def test_many_large_buildings_low_green(self):
        # 20 buildings × 100×80 = 160000m² > site area 90000m²
        buildings = [_b(i, w=100, d=80) for i in range(20)]
        ratio = compute_green_ratio(_layout(*buildings), _req())
        assert ratio <= 0.0  # clamped to 0


class TestCheckGreen:
    def test_passes_when_enough_green(self):
        violations = check_green(_layout(_b(1), _b(2)), _req(min_green=25))
        assert violations == []

    def test_fails_when_too_many_buildings(self):
        # Pack the site with large buildings
        buildings = [_b(i, w=100, d=80) for i in range(15)]
        violations = check_green(_layout(*buildings), _req(min_green=25))
        assert len(violations) == 1
        assert violations[0].type == "GREEN_SPACE_VIOLATION"
        assert violations[0].severity == "hard"

    def test_zero_min_green_always_passes(self):
        buildings = [_b(i, w=100, d=80) for i in range(10)]
        violations = check_green(_layout(*buildings), _req(min_green=0))
        assert violations == []
