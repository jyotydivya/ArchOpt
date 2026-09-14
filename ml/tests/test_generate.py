"""
ml/tests/test_generate.py
=========================
Contract tests for ml.inference.generate.generate_candidates().
"""
from __future__ import annotations

import math

import numpy as np
import pytest

from contracts.layout import CampusGraph, CandidateBuilding, CandidateLayout
from ml.inference.generate import generate_candidates
from ml.training.mock_graph import MVP_BUILDINGS, build_mock_campus_graph, random_campus_graph


@pytest.fixture(scope="module")
def mock_graph() -> CampusGraph:
    return build_mock_campus_graph()


@pytest.fixture(scope="module")
def candidates(mock_graph):
    return generate_candidates(mock_graph, 100, seed=0)


def _rotated_corners(b: CandidateBuilding):
    """Same corner maths as optimization/constraints/boundary.py."""
    cx, cy = b.x + b.width / 2.0, b.y + b.depth / 2.0
    angle = math.radians(b.rotation)
    cos_a, sin_a = math.cos(angle), math.sin(angle)
    return [
        (cx + lx * cos_a - ly * sin_a, cy + lx * sin_a + ly * cos_a)
        for lx, ly in [(-b.width / 2, -b.depth / 2), (b.width / 2, -b.depth / 2),
                       (b.width / 2, b.depth / 2), (-b.width / 2, b.depth / 2)]
    ]


# ── Contract ──────────────────────────────────────────────────────────────────

def test_returns_exactly_100_candidate_layouts(candidates):
    assert len(candidates) == 100
    assert all(isinstance(c, CandidateLayout) for c in candidates)


def test_default_num_candidates_is_100(mock_graph):
    assert len(generate_candidates(mock_graph, seed=1)) == 100


def test_candidate_ids_are_unique(candidates):
    ids = [c.candidate_id for c in candidates]
    assert len(set(ids)) == len(ids)
    assert all(isinstance(i, str) and i for i in ids)


def test_no_building_has_zero_width_or_depth(candidates):
    for c in candidates:
        for b in c.buildings:
            assert b.width > 0 and b.depth > 0


def test_buildings_carry_attributes_from_graph(candidates):
    catalogue = {b["id"]: b for b in MVP_BUILDINGS}
    for c in candidates:
        assert {b.building_id for b in c.buildings} == set(catalogue)
        for b in c.buildings:
            assert isinstance(b, CandidateBuilding)
            src = catalogue[b.building_id]
            assert (b.width, b.depth, b.height, b.floor_count) == (
                src["width"], src["depth"], src["height"], src["floorCount"]
            )
            assert b.zone == src["zone"]
            assert b.type == src["type"]
            assert b.name


def test_site_size_comes_from_graph(candidates):
    assert all((c.site_width, c.site_height) == (300.0, 300.0) for c in candidates)


def test_rotated_footprints_stay_on_site(candidates):
    for c in candidates:
        for b in c.buildings:
            assert 0.0 <= b.x <= c.site_width
            assert 0.0 <= b.y <= c.site_height
            assert b.rotation in (0.0, 90.0)
            for x, y in _rotated_corners(b):
                assert 0.0 <= x <= c.site_width
                assert 0.0 <= y <= c.site_height


# ── Diversity & determinism ───────────────────────────────────────────────────

def test_candidates_are_diverse(candidates):
    signatures = {
        tuple(round(v, 1) for b in c.buildings for v in (b.x, b.y, b.rotation))
        for c in candidates
    }
    assert len(signatures) == len(candidates)

    # Buildings move across the site between candidates, not just jitter.
    xs = np.array([[b.x for b in c.buildings] for c in candidates])
    ys = np.array([[b.y for b in c.buildings] for c in candidates])
    assert float(np.mean(xs.std(axis=0) + ys.std(axis=0))) > 20.0


def test_same_seed_reproduces_layouts(mock_graph):
    a = generate_candidates(mock_graph, 5, seed=42)
    b = generate_candidates(mock_graph, 5, seed=42)
    assert a == b


def test_different_seeds_give_different_layouts(mock_graph):
    a = generate_candidates(mock_graph, 5, seed=1)
    b = generate_candidates(mock_graph, 5, seed=2)
    assert [c.buildings for c in a] != [c.buildings for c in b]


def test_numpy_backend_matches_torch(mock_graph):
    pytest.importorskip("torch")
    a = generate_candidates(mock_graph, 20, seed=3, backend="numpy")
    b = generate_candidates(mock_graph, 20, seed=3, backend="torch")
    for ca, cb in zip(a, b):
        for ba, bb in zip(ca.buildings, cb.buildings):
            assert ba.x == pytest.approx(bb.x, abs=1e-3)
            assert ba.y == pytest.approx(bb.y, abs=1e-3)
            assert ba.rotation == bb.rotation


# ── Input handling ────────────────────────────────────────────────────────────

def test_accepts_dict_and_camel_case_graphs(mock_graph):
    snake = {
        "node_features": mock_graph.node_features,
        "edge_index": mock_graph.edge_index,
        "edge_features": mock_graph.edge_features,
    }
    camel = {
        "nodeFeatures": mock_graph.node_features,
        "edgeIndex": mock_graph.edge_index,
        "edgeFeatures": mock_graph.edge_features,
    }

    class CamelGraph:
        def __init__(self):
            self.nodeFeatures = mock_graph.node_features
            self.edgeIndex = mock_graph.edge_index
            self.edgeFeatures = mock_graph.edge_features

    expected = generate_candidates(mock_graph, 3, seed=0)
    for graph in (snake, camel, CamelGraph()):
        assert generate_candidates(graph, 3, seed=0) == expected


def test_graph_without_edges(mock_graph):
    graph = CampusGraph(node_features=mock_graph.node_features, edge_index=[[], []], edge_features=[])
    layouts = generate_candidates(graph, 4, seed=0)
    assert len(layouts) == 4
    assert len(layouts[0].buildings) == len(mock_graph.node_features)


def test_random_campuses_generate_valid_layouts():
    rng = np.random.default_rng(123)
    for _ in range(10):
        graph = random_campus_graph(rng)
        layouts = generate_candidates(graph, 5, seed=0)
        assert len(layouts) == 5
        for c in layouts:
            assert len(c.buildings) == len(graph.node_features)
            for b in c.buildings:
                assert b.width > 0 and b.depth > 0 and b.zone and b.type
                assert 0.0 <= b.x <= c.site_width and 0.0 <= b.y <= c.site_height


@pytest.mark.parametrize("num_candidates", [0, -1, 2.5, True])
def test_rejects_bad_num_candidates(mock_graph, num_candidates):
    with pytest.raises(ValueError):
        generate_candidates(mock_graph, num_candidates)


def _with(mock_graph: CampusGraph, **changes) -> CampusGraph:
    fields = {
        "node_features": mock_graph.node_features,
        "edge_index": mock_graph.edge_index,
        "edge_features": mock_graph.edge_features,
    }
    fields.update(changes)
    return CampusGraph(**fields)


def test_rejects_empty_graph(mock_graph):
    with pytest.raises(ValueError, match="non-empty"):
        generate_candidates(_with(mock_graph, node_features=[]), 1)


def test_rejects_rows_missing_columns(mock_graph):
    with pytest.raises(ValueError, match="columns"):
        generate_candidates(_with(mock_graph, node_features=[row[:5] for row in mock_graph.node_features]), 1)


def test_rejects_zero_footprint(mock_graph):
    rows = [list(row) for row in mock_graph.node_features]
    rows[0][1] = 0.0
    with pytest.raises(ValueError, match="width > 0"):
        generate_candidates(_with(mock_graph, node_features=rows), 1)


def test_rejects_edge_index_out_of_range(mock_graph):
    n = len(mock_graph.node_features)
    with pytest.raises(ValueError, match="outside"):
        generate_candidates(_with(mock_graph, edge_index=[[0], [n]], edge_features=[mock_graph.edge_features[0]]), 1)


def test_rejects_edge_feature_count_mismatch(mock_graph):
    with pytest.raises(ValueError, match="one row per edge"):
        generate_candidates(_with(mock_graph, edge_features=mock_graph.edge_features[:-1]), 1)


def test_missing_checkpoint_warns_and_still_generates(mock_graph, tmp_path):
    with pytest.warns(RuntimeWarning, match="checkpoint not found"):
        layouts = generate_candidates(mock_graph, 2, seed=0, weights_path=tmp_path / "missing.npz")
    assert len(layouts) == 2
