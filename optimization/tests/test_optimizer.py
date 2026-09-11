"""
Full pipeline integration test for the optimizer.

Tests the complete:
  generate_mock_candidates → optimize_layouts → list[RankedLayout]
pipeline.
"""
import pytest
from optimization.optimizer import optimize_layouts
from optimization.mock_data import generate_mock_candidates, get_demo_requirements
from optimization.contracts import RankedLayout, LayoutMetrics


@pytest.fixture
def requirements():
    return get_demo_requirements()


@pytest.fixture
def candidates(requirements):
    return generate_mock_candidates(50, requirements, seed=0)


class TestOptimizerOutput:
    def test_returns_top_5_by_default(self, candidates, requirements):
        result = optimize_layouts(candidates, requirements)
        assert len(result) == 5

    def test_returns_fewer_when_requested(self, candidates, requirements):
        result = optimize_layouts(candidates, requirements, top_k=3)
        assert len(result) == 3

    def test_ranks_are_sequential(self, candidates, requirements):
        result = optimize_layouts(candidates, requirements)
        ranks = [rl.rank for rl in result]
        assert ranks == list(range(1, len(result) + 1))

    def test_feasible_layouts_ranked_first(self, candidates, requirements):
        result = optimize_layouts(candidates, requirements)
        # Find first infeasible
        first_infeasible = next((i for i, rl in enumerate(result) if not rl.feasible), None)
        if first_infeasible is not None:
            # All layouts before it must be feasible
            assert all(result[i].feasible for i in range(first_infeasible))

    def test_return_type(self, candidates, requirements):
        result = optimize_layouts(candidates, requirements)
        assert all(isinstance(rl, RankedLayout) for rl in result)

    def test_metrics_in_range(self, candidates, requirements):
        result = optimize_layouts(candidates, requirements)
        for rl in result:
            m = rl.metrics
            assert 0.0 <= m.land_utilization  <= 1.0
            assert 0.0 <= m.green_ratio       <= 1.0
            assert 0.0 <= m.parking_ratio     <= 1.0
            assert 0.0 <= m.accessibility_score <= 1.0
            assert 0.0 <= m.road_efficiency   <= 1.0
            assert 0.0 <= m.constraint_score  <= 1.0

    def test_no_duplicate_candidate_ids(self, candidates, requirements):
        result = optimize_layouts(candidates, requirements)
        ids = [rl.candidate_id for rl in result]
        assert len(ids) == len(set(ids))

    def test_empty_candidates_returns_empty(self, requirements):
        result = optimize_layouts([], requirements)
        assert result == []

    def test_single_candidate(self, requirements):
        single = generate_mock_candidates(1, requirements, seed=7)
        result = optimize_layouts(single, requirements, top_k=5)
        assert len(result) == 1
        assert result[0].rank == 1

    def test_buildings_carried_through(self, candidates, requirements):
        result = optimize_layouts(candidates, requirements, top_k=1)
        assert len(result[0].buildings) == len(candidates[0].buildings)

    def test_site_dimensions_preserved(self, candidates, requirements):
        result = optimize_layouts(candidates, requirements, top_k=1)
        assert result[0].site_width == requirements.site_width
        assert result[0].site_height == requirements.site_height

    def test_reproducible_with_same_seed(self, requirements):
        c1 = generate_mock_candidates(30, requirements, seed=42)
        c2 = generate_mock_candidates(30, requirements, seed=42)
        r1 = optimize_layouts(c1, requirements, top_k=3)
        r2 = optimize_layouts(c2, requirements, top_k=3)
        assert [rl.candidate_id for rl in r1] == [rl.candidate_id for rl in r2]

    def test_no_hard_violation_in_feasible_plans(self, candidates, requirements):
        result = optimize_layouts(candidates, requirements)
        for rl in result:
            if rl.feasible and rl.validation:
                hard = [v for v in rl.validation.violations if v.severity == "hard"]
                assert hard == [], f"Feasible plan {rl.candidate_id} has hard violations: {hard}"
