"""Tests for NSGA-II non-dominated sorting and crowding distance."""
import math
import pytest
from optimization.nsga2 import (
    _dominates,
    non_dominated_sort,
    crowding_distance,
    nsga2_rank,
    rank_population,
)


class TestDominates:
    def test_a_dominates_b_strictly(self):
        assert _dominates([0.1, 0.2], [0.3, 0.4]) is True

    def test_equal_not_dominating(self):
        assert _dominates([0.5, 0.5], [0.5, 0.5]) is False

    def test_partial_dominance(self):
        # [0.1, 0.5] vs [0.3, 0.3]: first is better, second is worse → not dominated
        assert _dominates([0.1, 0.5], [0.3, 0.3]) is False

    def test_b_dominates_a(self):
        assert _dominates([0.9, 0.9], [0.1, 0.1]) is False


class TestNonDominatedSort:
    def test_two_front_population(self):
        # Clear two-front case
        objectives = [
            [0.1, 0.9],  # Front 1 (Pareto)
            [0.9, 0.1],  # Front 1 (Pareto)
            [0.5, 0.5],  # Front 2 (dominated by neither above)
            [0.6, 0.8],  # Front 2 or 3
        ]
        fronts = non_dominated_sort(objectives)
        assert len(fronts) >= 2
        # Indices 0 and 1 should be in front 0 (Pareto optimal)
        assert 0 in fronts[0] and 1 in fronts[0]

    def test_all_dominated_chain(self):
        # Strict ordering: 0 < 1 < 2
        objectives = [[0.1, 0.1], [0.5, 0.5], [0.9, 0.9]]
        fronts = non_dominated_sort(objectives)
        assert fronts[0] == [0]
        assert fronts[1] == [1]
        assert fronts[2] == [2]

    def test_single_individual(self):
        fronts = non_dominated_sort([[0.3, 0.7]])
        assert fronts == [[0]]

    def test_all_equal(self):
        # All identical — all in the same front
        objectives = [[0.5, 0.5]] * 4
        fronts = non_dominated_sort(objectives)
        assert len(fronts[0]) == 4

    def test_all_indices_covered(self):
        objectives = [[i * 0.1, (9 - i) * 0.1] for i in range(10)]
        fronts = non_dominated_sort(objectives)
        all_indices = [i for front in fronts for i in front]
        assert sorted(all_indices) == list(range(10))


class TestCrowdingDistance:
    def test_boundary_gets_infinity(self):
        front = [0, 1, 2]
        objectives = [[0.0, 1.0], [0.5, 0.5], [1.0, 0.0]]
        distances = crowding_distance(front, objectives)
        assert distances[0] == math.inf
        assert distances[2] == math.inf
        assert math.isfinite(distances[1])

    def test_empty_front(self):
        assert crowding_distance([], [[0.5, 0.5]]) == []

    def test_two_individuals_get_infinity(self):
        front = [0, 1]
        objectives = [[0.0, 1.0], [1.0, 0.0]]
        distances = crowding_distance(front, objectives)
        assert all(d == math.inf for d in distances)


class TestNSGA2Rank:
    def test_output_length_matches_input(self):
        objectives = [[i * 0.1, (5 - i) * 0.1] for i in range(6)]
        result = nsga2_rank(objectives)
        assert len(result) == 6

    def test_pareto_optimal_ranked_first(self):
        objectives = [
            [0.1, 0.9],  # Pareto — neither dominates the other
            [0.9, 0.1],  # Pareto — neither dominates the other
            [0.8, 0.8],  # Dominated by [0.1,0.9] (0.1<0.8 AND 0.9>0.8 → not dominated actually)
        ]
        # Clear 2-front example:
        #   [0.2, 0.8] and [0.8, 0.2] don't dominate each other (trade-off).
        #   [0.5, 0.5] is dominated by [0.2,0.8]? No: 0.2<0.5 but 0.8>0.5.
        #   [0.5, 0.5] is dominated by [0.8,0.2]? No: 0.8>0.5.
        # So all three are on the same front! Use a strictly dominated point:
        #   [0.6, 0.6] is dominated by [0.2, 0.8]? No (0.8>0.6). By [0.4, 0.4]? Yes.
        # Clearest: [0.1,0.9], [0.9,0.1] (Pareto) and [0.5,0.5] (dominated by neither).
        # Actually [0.5,0.5]: Is it dominated by [0.1,0.9]? 0.1≤0.5 AND 0.9≥0.5 → NOT dominated.
        # Use strictly dominated: [0.6,0.8] dominated by [0.1,0.7] (0.1<0.6 AND 0.7<0.8).
        objectives2 = [
            [0.1, 0.7],  # Pareto — dominates index 2
            [0.8, 0.1],  # Pareto — not dominated by index 0 (0.8>0.1, not all ≤)
            [0.6, 0.8],  # Dominated by index 0 (0.1≤0.6 AND 0.7≤0.8, strictly on both)
        ]
        result = nsga2_rank(objectives2)
        front_map = {r[0]: r[1] for r in result}
        assert front_map[0] == 1
        assert front_map[1] == 1
        assert front_map[2] == 2

    def test_empty_population(self):
        assert nsga2_rank([]) == []

    def test_sorted_by_front_then_crowding(self):
        objectives = [[i * 0.1, (9 - i) * 0.1] for i in range(10)]
        result = nsga2_rank(objectives)
        front_nums = [r[1] for r in result]
        # Should be non-decreasing
        assert all(front_nums[i] <= front_nums[i + 1] for i in range(len(front_nums) - 1))

    def test_rank_population_pure_python(self):
        objectives = [[0.2, 0.8], [0.5, 0.5], [0.8, 0.2]]
        result = rank_population(objectives, use_pymoo=False)
        assert len(result) == 3

    def test_result_tuple_structure(self):
        objectives = [[0.3, 0.7], [0.7, 0.3]]
        result = nsga2_rank(objectives)
        for item in result:
            idx, front, crowding = item
            assert isinstance(idx, int)
            assert isinstance(front, int)
            assert isinstance(crowding, float)
