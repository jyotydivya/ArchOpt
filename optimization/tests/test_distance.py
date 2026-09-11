"""Tests for named distance constraint checker."""
import pytest
from optimization.contracts import (
    CandidateBuilding, CandidateLayout, CampusRequirements, Constraint,
)
from optimization.constraints.distance import check_distance


def _req():
    return CampusRequirements(
        project_id=1, site_width=300, site_height=300,
        min_green_percent=25, min_parking_percent=10,
        min_road_width=8, min_building_gap=10,
    )


def _b(bid, x, y, w=40.0, d=30.0):
    return CandidateBuilding(building_id=bid, x=x, y=y, width=w, depth=d,
                              rotation=0.0, name=f"B{bid}", type="academic", zone="academic")


def _layout(*buildings):
    return CandidateLayout(candidate_id="t", site_width=300, site_height=300,
                            buildings=list(buildings))


def _min_dist(src, tgt, val, priority="hard", cid=1):
    return Constraint(id=cid, type="MIN_DISTANCE", source_id=src,
                      target_id=tgt, value=val, operator=">=", priority=priority)


def _max_dist(src, tgt, val, priority="soft", cid=2):
    return Constraint(id=cid, type="MAX_DISTANCE", source_id=src,
                      target_id=tgt, value=val, operator="<=", priority=priority)


class TestMinDistance:
    def test_satisfied(self):
        # Centres at (20,15) and (120,15) → dist = 100m
        b1, b2 = _b(1, 0, 0), _b(2, 100, 0)
        c = _min_dist(1, 2, 90)
        assert check_distance(_layout(b1, b2), _req(), [c]) == []

    def test_violated_hard(self):
        b1, b2 = _b(1, 0, 0), _b(2, 50, 0)  # centres 50m apart
        c = _min_dist(1, 2, 100)
        violations = check_distance(_layout(b1, b2), _req(), [c])
        assert len(violations) == 1
        assert violations[0].severity == "hard"
        assert violations[0].type == "NAMED_MIN_DISTANCE_VIOLATION"

    def test_violated_soft(self):
        b1, b2 = _b(1, 0, 0), _b(2, 50, 0)
        c = _min_dist(1, 2, 100, priority="soft")
        violations = check_distance(_layout(b1, b2), _req(), [c])
        assert violations[0].severity == "soft"


class TestMaxDistance:
    def test_satisfied(self):
        b1, b2 = _b(1, 0, 0), _b(2, 40, 0)  # 40m apart
        c = _max_dist(1, 2, 100)
        assert check_distance(_layout(b1, b2), _req(), [c]) == []

    def test_violated(self):
        b1, b2 = _b(1, 0, 0), _b(2, 200, 0)  # 200m apart
        c = _max_dist(1, 2, 100)
        violations = check_distance(_layout(b1, b2), _req(), [c])
        assert len(violations) == 1
        assert violations[0].type == "NAMED_MAX_DISTANCE_VIOLATION"


class TestEdgeCases:
    def test_missing_building_skipped(self):
        b1 = _b(1, 0, 0)
        c = _min_dist(1, 99, 100)  # building 99 not in layout
        assert check_distance(_layout(b1), _req(), [c]) == []

    def test_empty_constraints(self):
        b1, b2 = _b(1, 0, 0), _b(2, 10, 0)
        assert check_distance(_layout(b1, b2), _req(), []) == []

    def test_non_distance_constraint_ignored(self):
        b1, b2 = _b(1, 0, 0), _b(2, 10, 0)
        c = Constraint(id=1, type="SAME_ZONE", source_id=1, target_id=2,
                       value=0, operator="==", priority="soft")
        assert check_distance(_layout(b1, b2), _req(), [c]) == []
