"""Tests for parking constraint checker."""
import pytest
from optimization.contracts import CandidateBuilding, CandidateLayout, CampusRequirements
from optimization.constraints.parking import check_parking, compute_parking_ratio


def _req(min_parking=10):
    return CampusRequirements(
        project_id=1, site_width=300, site_height=300,
        min_green_percent=25, min_parking_percent=min_parking,
        min_road_width=8, min_building_gap=10,
    )


def _b(bid, btype="academic", zone="academic", w=60.0, d=40.0, x=None, y=None):
    return CandidateBuilding(
        building_id=bid, x=x or (10 * bid), y=y or (10 * bid),
        width=w, depth=d, rotation=0.0, name=f"B{bid}", type=btype, zone=zone,
    )


def _layout(*buildings):
    return CandidateLayout(candidate_id="t", site_width=300, site_height=300,
                            buildings=list(buildings))


class TestParkingRatio:
    def test_explicit_parking_building(self):
        # One 90×50 parking building = 4500m² on 90000m²
        p = _b(1, btype="parking", zone="parking", w=90, d=50)
        ratio = compute_parking_ratio(_layout(p), _req())
        
        expected_unbuilt = 90000 - 4500 - (0.08 * 90000)
        expected_surface = expected_unbuilt * 0.5
        expected_ratio = (4500 + expected_surface) / 90000
        
        assert abs(ratio - expected_ratio) < 0.001

    def test_no_parking_building_falls_back(self):
        # Only academic buildings — falls back to unbuilt estimate
        a = _b(1, btype="academic", zone="academic")
        ratio = compute_parking_ratio(_layout(a), _req())
        assert ratio > 0


class TestCheckParking:
    def test_passes_with_explicit_parking(self):
        # 40×30 parking = 1200m² on 90000m² = 1.3% → below 10%
        # Need larger parking building to pass
        p = _b(1, btype="parking", zone="parking", w=120, d=90, x=0, y=0)
        # 10800m² / 90000m² = 12% ✓
        violations = check_parking(_layout(p), _req(min_parking=10))
        assert violations == []

    def test_fails_with_tiny_parking(self):
        # Fill the site with a giant building so unbuilt space is ~0
        huge_bld = _b(2, w=280, d=280)
        # Parking of 1×1 — effectively 0 coverage
        p = _b(1, btype="parking", zone="parking", w=1, d=1, x=0, y=0)
        violations = check_parking(_layout(huge_bld, p), _req(min_parking=10))
        assert len(violations) == 1
        assert violations[0].type == "PARKING_VIOLATION"
        assert violations[0].severity == "hard"

    def test_zero_min_parking_always_passes(self):
        violations = check_parking(_layout(_b(1)), _req(min_parking=0))
        assert violations == []
