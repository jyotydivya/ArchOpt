"""
ml/tests/test_integration_optimizer.py
======================================
Person 2 → Person 3 integration against the real code in the repo:

  * generate_candidates() → optimization.optimizer.optimize_layouts()
  * the backend's REAL-mode bridge (backend/services/ml_bridge.py), with a
    stand-in for Person 1's build_graph() until ml/dataset lands
"""
from __future__ import annotations

import sys
import types

import pytest

from contracts.layout import RankedLayout
from ml.inference.generate import generate_candidates
from ml.training.mock_graph import (
    build_mock_campus_graph,
    graph_from_campus_data,
    mock_campus_data,
    mock_constraints,
    mock_requirements,
)
from optimization.optimizer import optimize_layouts


@pytest.fixture(scope="module")
def candidates():
    return generate_candidates(build_mock_campus_graph(), 100, seed=0)


def test_optimize_layouts_returns_five_ranked_layouts(candidates):
    ranked = optimize_layouts(candidates, mock_requirements(), mock_constraints(), top_k=5)

    assert len(ranked) == 5
    assert all(isinstance(r, RankedLayout) for r in ranked)
    assert [r.rank for r in ranked] == [1, 2, 3, 4, 5]
    candidate_ids = {c.candidate_id for c in candidates}
    assert all(r.candidate_id in candidate_ids for r in ranked)
    for r in ranked:
        assert 0.0 <= r.metrics.constraint_score <= 1.0
        assert all(b.width > 0 and b.depth > 0 and b.zone and b.type for b in r.buildings)


def test_backend_real_pipeline_runs_with_p2_and_p3(monkeypatch):
    pytest.importorskip("fastapi")
    from backend.services import ml_bridge

    # Stand-in for Person 1's module so run_real_pipeline() can import it.
    dataset_pkg = types.ModuleType("ml.dataset")
    graph_builder = types.ModuleType("ml.dataset.graph_builder")
    graph_builder.build_graph = graph_from_campus_data
    monkeypatch.setitem(sys.modules, "ml.dataset", dataset_pkg)
    monkeypatch.setitem(sys.modules, "ml.dataset.graph_builder", graph_builder)

    campus_data = mock_campus_data()
    requirements = {
        key: campus_data[key]
        for key in ("projectId", "siteWidth", "siteHeight", "minGreenPercent",
                    "minParkingPercent", "minRoadWidth", "minBuildingGap", "entrances")
    }

    layouts = ml_bridge.run_real_pipeline(
        campus_data=campus_data,
        requirements_dict=requirements,
        constraints_list=campus_data["constraints"],
        candidate_count=100,
        top_k=5,
    )

    assert len(layouts) == 5
    expected_ids = {b["id"] for b in campus_data["buildings"]}
    for layout in layouts:
        assert {b["buildingId"] for b in layout["buildings"]} == expected_ids
