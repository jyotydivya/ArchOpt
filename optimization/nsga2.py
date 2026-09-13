"""
optimization/nsga2.py
======================
Pure-Python NSGA-II implementation over pre-evaluated objective vectors.

The optimizer works on a *population* where each individual is already
evaluated — it receives a list of objective vectors (one per candidate)
and returns a Pareto-ranked ordering with crowding distances.

This design keeps NSGA-II decoupled from layout representation: it only
sees floating-point objective vectors and returns indices.

Optionally uses pymoo as an accelerated backend when available.

References
----------
Deb et al., 2002. "A Fast and Elitist Multiobjective Genetic Algorithm: NSGA-II."
IEEE Transactions on Evolutionary Computation, 6(2), 182–197.
"""
from __future__ import annotations

import math
import random
from typing import List, Tuple


# ─────────────────────────────────────────────────────────────────────────────
# Non-dominated sorting
# ─────────────────────────────────────────────────────────────────────────────

def _dominates(a: List[float], b: List[float]) -> bool:
    """Return True if objective vector *a* dominates *b* (minimisation)."""
    return all(ai <= bi for ai, bi in zip(a, b)) and any(ai < bi for ai, bi in zip(a, b))


def non_dominated_sort(objectives: List[List[float]]) -> List[List[int]]:
    """
    Sort population indices into Pareto fronts F1, F2, …

    Parameters
    ----------
    objectives : list of objective vectors, one per individual.
                 Each vector contains values to MINIMISE.

    Returns
    -------
    List of fronts, where each front is a list of individual indices.
    Front 0 (F1) is the best (Pareto-optimal) set.
    """
    n = len(objectives)
    domination_count = [0] * n          # how many individuals dominate i
    dominated_by: List[List[int]] = [[] for _ in range(n)]  # whom i dominates

    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            if _dominates(objectives[i], objectives[j]):
                dominated_by[i].append(j)
            elif _dominates(objectives[j], objectives[i]):
                domination_count[i] += 1

    fronts: List[List[int]] = []
    current_front = [i for i in range(n) if domination_count[i] == 0]
    fronts.append(current_front)

    while True:
        next_front: List[int] = []
        for i in current_front:
            for j in dominated_by[i]:
                domination_count[j] -= 1
                if domination_count[j] == 0:
                    next_front.append(j)
        if not next_front:
            break
        fronts.append(next_front)
        current_front = next_front

    return fronts


# ─────────────────────────────────────────────────────────────────────────────
# Crowding distance
# ─────────────────────────────────────────────────────────────────────────────

def crowding_distance(front: List[int], objectives: List[List[float]]) -> List[float]:
    """
    Compute crowding distance for each individual in a Pareto front.

    Returns a list of distances (index-aligned with *front*).
    Boundary individuals receive infinity.
    """
    n = len(front)
    if n == 0:
        return []
    distances = [0.0] * n
    num_objectives = len(objectives[0])

    for m in range(num_objectives):
        sorted_idx = sorted(range(n), key=lambda k: objectives[front[k]][m])
        distances[sorted_idx[0]] = math.inf
        distances[sorted_idx[-1]] = math.inf

        obj_min = objectives[front[sorted_idx[0]]][m]
        obj_max = objectives[front[sorted_idx[-1]]][m]
        obj_range = obj_max - obj_min

        if obj_range == 0:
            continue

        for pos in range(1, n - 1):
            prev_val = objectives[front[sorted_idx[pos - 1]]][m]
            next_val = objectives[front[sorted_idx[pos + 1]]][m]
            distances[sorted_idx[pos]] += (next_val - prev_val) / obj_range

    return distances


# ─────────────────────────────────────────────────────────────────────────────
# Main NSGA-II ranking function
# ─────────────────────────────────────────────────────────────────────────────

def nsga2_rank(
    objectives: List[List[float]],
) -> List[Tuple[int, int, float]]:
    """
    Rank a pre-evaluated population using NSGA-II.

    Parameters
    ----------
    objectives : list of objective vectors (to minimise). One per individual.

    Returns
    -------
    List of (individual_index, front_number, crowding_distance) tuples,
    sorted by (front_number ASC, crowding_distance DESC).
    Front numbers are 1-indexed (Front 1 = Pareto-optimal).
    """
    if not objectives:
        return []

    fronts = non_dominated_sort(objectives)

    result: List[Tuple[int, int, float]] = []
    for front_num, front in enumerate(fronts, start=1):
        distances = crowding_distance(front, objectives)
        for local_idx, global_idx in enumerate(front):
            result.append((global_idx, front_num, distances[local_idx]))

    # Sort: better front first, then higher crowding distance within front
    result.sort(key=lambda t: (t[1], -t[2]))
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Optional pymoo backend
# ─────────────────────────────────────────────────────────────────────────────

def _try_pymoo_rank(objectives: List[List[float]]) -> List[Tuple[int, int, float]] | None:
    """
    Attempt to use pymoo's non-dominated sorting as a faster alternative.
    Returns None if pymoo is not installed.
    """
    try:
        import numpy as np
        from pymoo.util.nds.non_dominated_sorting import NonDominatedSorting

        F = np.array(objectives)
        nds = NonDominatedSorting()
        fronts_raw = nds.do(F, return_rank=False)

        result: List[Tuple[int, int, float]] = []
        for front_num, front in enumerate(fronts_raw, start=1):
            distances = crowding_distance(list(front), objectives)
            for local_idx, global_idx in enumerate(front):
                result.append((int(global_idx), front_num, distances[local_idx]))

        result.sort(key=lambda t: (t[1], -t[2]))
        return result
    except ImportError:
        return None


def rank_population(
    objectives: List[List[float]],
    use_pymoo: bool = True,
) -> List[Tuple[int, int, float]]:
    """
    Rank a population — tries pymoo first, falls back to pure-Python.

    Parameters
    ----------
    objectives : objective vectors (to minimise).
    use_pymoo  : if True, attempt pymoo acceleration.

    Returns
    -------
    Sorted list of (index, front, crowding_distance) tuples.
    """
    if use_pymoo:
        result = _try_pymoo_rank(objectives)
        if result is not None:
            return result
    return nsga2_rank(objectives)
