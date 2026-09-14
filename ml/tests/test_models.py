"""
ml/tests/test_models.py
=======================
Unit tests for the feature layout, model plumbing, losses and training loop.
"""
from __future__ import annotations

import math

import numpy as np
import pytest

from contracts.layout import CampusGraph
from ml.models.campus_model import (
    DEFAULT_WEIGHTS_PATH,
    init_params,
    load_params,
    param_shapes,
    save_params,
)
from ml.models.features import (
    EDGE_FEATURE_DIM,
    NODE_FEATURE_DIM,
    NODE_INPUT_DIM,
    encode_edge,
    encode_node,
    prepare_graph,
)
from ml.models.layout_decoder import bounded_positions
from ml.training.mock_graph import build_mock_campus_graph


def _node(**overrides):
    fields = dict(
        building_id=7, width=50.0, depth=30.0, height=15.0, floor_count=5,
        building_type="hostel", zone="residential", site_width=250.0, site_height=200.0,
    )
    fields.update(overrides)
    return encode_node(**fields)


# ── Features ──────────────────────────────────────────────────────────────────

def test_node_encoding_round_trips():
    graph = prepare_graph(CampusGraph(node_features=[_node()], edge_index=[[], []], edge_features=[]))
    node = graph.nodes[0]
    assert len(_node()) == NODE_FEATURE_DIM
    assert (node.building_id, node.width, node.depth, node.height, node.floor_count) == (7, 50.0, 30.0, 15.0, 5)
    assert (node.type, node.zone) == ("hostel", "residential")
    assert (graph.site_width, graph.site_height) == (250.0, 200.0)
    assert graph.node_inputs.shape == (1, NODE_INPUT_DIM)


def test_unknown_type_and_zone_map_to_other():
    graph = prepare_graph(CampusGraph(
        node_features=[_node(building_type="cafeteria", zone="commercial")],
        edge_index=[[], []], edge_features=[],
    ))
    assert (graph.nodes[0].type, graph.nodes[0].zone) == ("other", "other")


def test_edge_encoding_and_symmetrisation():
    row = encode_edge("near", weight=0.8)
    assert len(row) == EDGE_FEATURE_DIM
    graph = prepare_graph(CampusGraph(node_features=[_node(), _node(building_id=8)], edge_index=[[0], [1]], edge_features=[row]))
    assert graph.edge_index.tolist() == [[0, 1], [1, 0]]
    assert graph.edge_inputs.shape == (2, EDGE_FEATURE_DIM)


def test_short_edge_rows_are_padded():
    graph = prepare_graph(CampusGraph(node_features=[_node(), _node(building_id=8)], edge_index=[[0], [1]], edge_features=[[1.0, 0.0]]))
    assert graph.raw_edge_features.shape == (1, EDGE_FEATURE_DIM)


def test_unknown_relation_is_rejected():
    with pytest.raises(ValueError):
        encode_edge("ADJACENT_TO")


# ── Geometry ──────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("u", [0.0, 0.5, 1.0])
@pytest.mark.parametrize("vertical", [0.0, 1.0])
def test_bounded_positions_keep_footprint_on_site(u, vertical):
    width, depth, site_w, site_h = 80.0, 30.0, 200.0, 150.0
    x, y, cx, cy, extent_x, extent_y = bounded_positions(u, u, vertical, width, depth, site_w, site_h)
    assert x >= 0 and y >= 0
    assert cx - extent_x / 2 >= 0 and cx + extent_x / 2 <= site_w
    assert cy - extent_y / 2 >= 0 and cy + extent_y / 2 <= site_h


# ── Checkpoints ───────────────────────────────────────────────────────────────

def test_save_and_load_round_trip(tmp_path):
    params = init_params(seed=5)
    path = tmp_path / "model.npz"
    save_params(params, path)
    loaded = load_params(path)
    for name, value in params.items():
        np.testing.assert_allclose(loaded[name], value, rtol=1e-6)


def test_load_rejects_mismatched_checkpoint(tmp_path):
    params = init_params()
    params.pop("decoder.out.bias")
    path = tmp_path / "bad.npz"
    save_params(params, path)
    with pytest.raises(ValueError):
        load_params(path)


def test_shipped_checkpoint_loads():
    assert DEFAULT_WEIGHTS_PATH.exists(), "run `python -m ml.training.train` to create the checkpoint"
    load_params(DEFAULT_WEIGHTS_PATH)


def test_param_shapes_match_torch_module():
    pytest.importorskip("torch")
    from ml.models.campus_model import CampusModel

    state = CampusModel().state_dict()
    assert {k: tuple(v.shape) for k, v in state.items()} == param_shapes()


# ── Losses & training ─────────────────────────────────────────────────────────

def test_overlap_loss_is_zero_when_apart_and_positive_when_overlapping():
    torch = pytest.importorskip("torch")
    from ml.training.loss import GraphTensors, overlap_loss

    t = GraphTensors(
        widths=torch.tensor([20.0, 20.0]), depths=torch.tensor([20.0, 20.0]),
        zone_ids=torch.tensor([0, 1]), edge_src=torch.tensor([], dtype=torch.long),
        edge_dst=torch.tensor([], dtype=torch.long), edge_features=torch.zeros(0, EDGE_FEATURE_DIM),
        site_width=200.0, site_height=200.0, min_gap=10.0,
    )
    extent = torch.full((1, 2), 20.0)
    apart = overlap_loss(torch.tensor([[20.0, 150.0]]), torch.tensor([[20.0, 150.0]]), extent, extent, t)
    stacked = overlap_loss(torch.tensor([[50.0, 55.0]]), torch.tensor([[50.0, 55.0]]), extent, extent, t)
    assert float(apart) == 0.0
    assert float(stacked) > 0.0


def test_training_runs_and_writes_loadable_weights(tmp_path):
    pytest.importorskip("torch")
    from ml.training.train import train

    path = tmp_path / "tiny.npz"
    losses = train(steps=3, graphs_per_step=1, samples_per_graph=2, out_path=path, log_every=0)
    assert all(math.isfinite(v) for v in losses.values())
    load_params(path)


def test_evaluate_reports_population_stats():
    from ml.inference.generate import generate_candidates
    from ml.training.evaluate import evaluate_candidates

    stats = evaluate_candidates(generate_candidates(build_mock_campus_graph(), 10, seed=0))
    assert stats["num_candidates"] == 10
    assert stats["in_bounds_rate"] == 1.0
