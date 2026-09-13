"""Tests for zoning constraint checker."""
import pytest
from optimization.contracts import CandidateBuilding, CandidateLayout, CampusRequirements
from optimization.constraints.zoning import check_zoning


def _req(sw=300, sh=300):
    return CampusRequirements(
        project_id=1, site_width=sw, site_height=sh,
        min_green_percent=25, min_parking_percent=10,
        min_road_width=8, min_building_gap=10,
    )


def _b(bid, x, y, zone="academic", w=40.0, d=30.0):
    return CandidateBuilding(building_id=bid, x=x, y=y, width=w, depth=d,
                              rotation=0.0, name=f"B{bid}", type=zone, zone=zone)


def _layout(*buildings):
    return CandidateLayout(candidate_id="t", site_width=300, site_height=300,
                            buildings=list(buildings))


class TestZoningValid:
    def test_same_zone_close_together(self):
        # Two academic buildings 20m apart — within threshold
        b1, b2 = _b(1, 0, 0), _b(2, 20, 0)
        assert check_zoning(_layout(b1, b2), _req()) == []

    def test_single_building_per_zone(self):
        b1 = _b(1, 0, 0, zone="academic")
        b2 = _b(2, 250, 250, zone="residential")
        # Only 1 per zone — no pair to check
        assert check_zoning(_layout(b1, b2), _req()) == []

    def test_different_zones_far_apart_ok(self):
        b1 = _b(1, 0, 0, zone="academic")
        b2 = _b(2, 250, 250, zone="sports")
        assert check_zoning(_layout(b1, b2), _req()) == []


class TestZoningViolations:
    def test_same_zone_too_far(self):
        # Two academic buildings on opposite corners of 300×300 site
        b1 = _b(1, 0,   0,   zone="academic")
        b2 = _b(2, 250, 250, zone="academic")
        violations = check_zoning(_layout(b1, b2), _req())
        assert len(violations) == 1
        assert violations[0].type == "ZONING_VIOLATION"
        assert violations[0].severity == "soft"  # zoning is always soft

    def test_three_buildings_two_violate(self):
        b1 = _b(1, 0, 0, zone="academic")
        b2 = _b(2, 10, 0, zone="academic")   # close to b1
        b3 = _b(3, 280, 280, zone="academic") # far from both
        violations = check_zoning(_layout(b1, b2, b3), _req())
        # b1-b3 and b2-b3 should both violate
        assert len(violations) >= 2

    def test_small_site_smaller_threshold(self):
        # On a 100×100 site, threshold = 50m
        b1 = _b(1, 0, 0, zone="academic")
        b2 = _b(2, 60, 0, zone="academic")  # centres 60m apart > 50m threshold
        violations = check_zoning(_layout(b1, b2), _req(sw=100, sh=100))
        assert len(violations) == 1
