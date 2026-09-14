"""
ml/dataset/tests/test_graph_builder.py
======================================
Comprehensive test suite for Person 1 (Campus Graph Builder).
Implements the 14 mandatory test cases defined in docs/PERSON_1_IMPLEMENTATION_PLAN.md.
"""
from __future__ import annotations

import copy
import math
import random
import pytest

from contracts.layout import CampusGraph
from ml.dataset.graph_builder import build_graph
from ml.models.features import NODE_FEATURE_DIM, EDGE_FEATURE_DIM, prepare_graph
from ml.inference.generate import generate_candidates


@pytest.fixture
def minimal_campus():
    return {
        "projectId": 1,
        "siteWidth": 300.0,
        "siteHeight": 300.0,
        "buildings": [
            {
                "id": 1,
                "name": "Academic Block A",
                "type": "academic",
                "zone": "academic",
                "width": 60.0,
                "depth": 40.0,
                "height": 18.0,
                "floorCount": 4,
                "requiredCount": 1,
            }
        ],
        "constraints": [],
    }


@pytest.fixture
def multi_building_campus():
    return {
        "projectId": 2,
        "siteWidth": 350.0,
        "siteHeight": 300.0,
        "buildings": [
            {
                "id": 10,
                "name": "Academic Block A",
                "type": "academic",
                "zone": "academic",
                "width": 60.0,
                "depth": 40.0,
                "height": 18.0,
                "floorCount": 4,
                "requiredCount": 1,
            },
            {
                "id": 20,
                "name": "Library",
                "type": "library",
                "zone": "academic",
                "width": 40.0,
                "depth": 30.0,
                "height": 14.0,
                "floorCount": 3,
                "requiredCount": 2,
            },
            {
                "id": 30,
                "name": "Hostel 1",
                "type": "hostel",
                "zone": "residential",
                "width": 50.0,
                "depth": 30.0,
                "height": 24.0,
                "floorCount": 6,
                "requiredCount": 1,
            },
        ],
        "constraints": [
            {
                "id": 101,
                "type": "MIN_DISTANCE",
                "sourceId": 10,
                "targetId": 20,
                "value": 30.0,
                "operator": ">=",
                "priority": "hard",
            },
            {
                "id": 102,
                "type": "MAX_DISTANCE",
                "sourceId": 20,
                "targetId": 30,
                "value": 150.0,
                "operator": "<=",
                "priority": "soft",
            },
        ],
    }


# ---------------------------------------------------------------------------
# Test 1: Basic valid campus -> CampusGraph
# ---------------------------------------------------------------------------
def test_basic_valid_campus_to_graph(minimal_campus):
    graph = build_graph(minimal_campus)
    assert isinstance(graph, CampusGraph)
    assert len(graph.node_features) == 1
    assert len(graph.edge_index) == 2
    assert len(graph.edge_index[0]) == 0
    assert len(graph.edge_features) == 0


# ---------------------------------------------------------------------------
# Test 2: Multiple buildings expansion with requiredCount
# ---------------------------------------------------------------------------
def test_multiple_buildings_expansion(multi_building_campus):
    # requiredCount: id 10 has 1, id 20 has 2, id 30 has 1 -> total 4 nodes
    graph = build_graph(multi_building_campus)
    assert len(graph.node_features) == 4
    # Check that building 20 appears twice with building_id == 20.0
    b20_nodes = [row for row in graph.node_features if int(round(row[0])) == 20]
    assert len(b20_nodes) == 2
    assert b20_nodes[0][1] == 40.0 and b20_nodes[1][1] == 40.0


# ---------------------------------------------------------------------------
# Test 3: Node feature dimensions and finite values
# ---------------------------------------------------------------------------
def test_node_feature_dimensions_and_finite(multi_building_campus):
    graph = build_graph(multi_building_campus)
    for row in graph.node_features:
        assert len(row) == NODE_FEATURE_DIM == 20
        assert all(math.isfinite(x) for x in row)


# ---------------------------------------------------------------------------
# Test 4: Edge feature dimensions and types
# ---------------------------------------------------------------------------
def test_edge_feature_dimensions_and_types(multi_building_campus):
    graph = build_graph(multi_building_campus)
    assert len(graph.edge_index) == 2
    e_count = len(graph.edge_index[0])
    assert len(graph.edge_index[1]) == e_count
    assert len(graph.edge_features) == e_count
    for row in graph.edge_features:
        assert len(row) == EDGE_FEATURE_DIM == 9
        assert all(math.isfinite(x) for x in row)


# ---------------------------------------------------------------------------
# Test 5: Building type and zone one-hot encoding
# ---------------------------------------------------------------------------
def test_building_type_and_zone_one_hot_encoding(minimal_campus):
    graph = build_graph(minimal_campus)
    row = graph.node_features[0]
    # Building 1: type="academic" (index 7), zone="academic" (index 14)
    assert row[7] == 1.0
    assert sum(row[7:14]) == 1.0  # Exactly one type active
    assert row[14] == 1.0
    assert sum(row[14:20]) == 1.0  # Exactly one zone active


# ---------------------------------------------------------------------------
# Test 6: Unknown type and zone map to "other"
# ---------------------------------------------------------------------------
def test_unknown_type_and_zone_maps_to_other():
    campus = {
        "siteWidth": 200.0,
        "siteHeight": 200.0,
        "buildings": [
            {
                "id": 99,
                "name": "Observatory",
                "type": "observatory",
                "zone": "science_park",
                "width": 30.0,
                "depth": 30.0,
            }
        ],
    }
    graph = build_graph(campus)
    row = graph.node_features[0]
    # "other" type is index 13, "other" zone is index 19
    assert row[13] == 1.0
    assert row[19] == 1.0


# ---------------------------------------------------------------------------
# Test 7: SAME_ZONE edges created between nodes in same zone
# ---------------------------------------------------------------------------
def test_same_zone_edges_created():
    campus = {
        "siteWidth": 300.0,
        "siteHeight": 300.0,
        "buildings": [
            {"id": 1, "type": "academic", "zone": "academic", "width": 40.0, "depth": 30.0},
            {"id": 2, "type": "academic", "zone": "academic", "width": 50.0, "depth": 30.0},
        ],
    }
    graph = build_graph(campus)
    # Both are academic zone -> exactly 1 edge: (0, 1) with relation SAME_ZONE
    assert len(graph.edge_features) >= 1
    # Check SAME_ZONE one-hot is index 2 in EDGE_RELATIONS (NEAR, FAR, SAME_ZONE...)
    same_zone_found = False
    for edge in graph.edge_features:
        if edge[2] == 1.0:  # SAME_ZONE
            same_zone_found = True
            assert edge[7] == 1.0  # weight 1.0
    assert same_zone_found


# ---------------------------------------------------------------------------
# Test 8: Functional type edges created
# ---------------------------------------------------------------------------
def test_functional_type_edges_created():
    campus = {
        "siteWidth": 300.0,
        "siteHeight": 300.0,
        "buildings": [
            {"id": 1, "type": "academic", "zone": "academic", "width": 40.0, "depth": 30.0},
            {"id": 2, "type": "library", "zone": "academic", "width": 30.0, "depth": 25.0},
        ],
    }
    graph = build_graph(campus)
    # academic <-> library has NEAR relation (index 0) with weight 0.9
    near_found = False
    for edge in graph.edge_features:
        if edge[0] == 1.0:  # NEAR
            near_found = True
            assert math.isclose(edge[7], 0.9)
    assert near_found


# ---------------------------------------------------------------------------
# Test 9: User distance constraints mapped to edges
# ---------------------------------------------------------------------------
def test_user_distance_constraints_mapped(multi_building_campus):
    graph = build_graph(multi_building_campus)
    # Constraint 101: MIN_DISTANCE value=30.0 between b10 and b20
    # b10 is node 0, b20 is nodes 1 and 2
    min_dist_found = 0
    for edge in graph.edge_features:
        if edge[5] == 1.0:  # MIN_DISTANCE is index 5
            min_dist_found += 1
            assert edge[8] == 30.0  # distance column
            assert edge[7] == 1.0   # hard weight
    # Linked to both expanded instances of building 20
    assert min_dist_found == 2


# ---------------------------------------------------------------------------
# Test 10: Hard vs soft constraint weights
# ---------------------------------------------------------------------------
def test_hard_vs_soft_constraint_weights(multi_building_campus):
    graph = build_graph(multi_building_campus)
    # Constraint 101 is hard -> weight 1.0 (MIN_DISTANCE index 5)
    # Constraint 102 is soft -> weight 0.5 (MAX_DISTANCE index 6)
    hard_found = False
    soft_found = False
    for edge in graph.edge_features:
        if edge[5] == 1.0 and math.isclose(edge[7], 1.0):
            hard_found = True
        if edge[6] == 1.0 and math.isclose(edge[7], 0.5):
            soft_found = True
    assert hard_found
    assert soft_found


# ---------------------------------------------------------------------------
# Test 11: Graph construction is strictly deterministic
# ---------------------------------------------------------------------------
def test_graph_construction_is_strictly_deterministic(multi_building_campus):
    graph1 = build_graph(multi_building_campus)

    # Shuffle the buildings in a copy of campus_data
    shuffled_campus = copy.deepcopy(multi_building_campus)
    random.seed(42)
    random.shuffle(shuffled_campus["buildings"])

    graph2 = build_graph(shuffled_campus)

    assert graph1.node_features == graph2.node_features
    assert graph1.edge_index == graph2.edge_index
    assert graph1.edge_features == graph2.edge_features


# ---------------------------------------------------------------------------
# Test 12: Validation rejects missing or non-positive site dimensions
# ---------------------------------------------------------------------------
def test_validation_rejects_missing_site_dimensions(minimal_campus):
    invalid_campus = copy.deepcopy(minimal_campus)
    invalid_campus["siteWidth"] = -10.0
    with pytest.raises(ValueError, match="site dimensions must be strictly positive"):
        build_graph(invalid_campus)

    del invalid_campus["siteWidth"]
    with pytest.raises(ValueError, match="missing required site dimensions"):
        build_graph(invalid_campus)


# ---------------------------------------------------------------------------
# Test 13: Validation rejects empty buildings list
# ---------------------------------------------------------------------------
def test_validation_rejects_empty_buildings(minimal_campus):
    invalid_campus = copy.deepcopy(minimal_campus)
    invalid_campus["buildings"] = []
    with pytest.raises(ValueError, match="non-empty 'buildings' list"):
        build_graph(invalid_campus)


# ---------------------------------------------------------------------------
# Test 14: P1 graph passes P2 prepare_graph and GNN forward generation
# ---------------------------------------------------------------------------
def test_graph_passes_p2_prepare_graph_and_gnn_forward(multi_building_campus):
    graph = build_graph(multi_building_campus)
    # Real Person 2 prepare_graph validation
    prepared = prepare_graph(graph)
    assert prepared.num_nodes == 4
    assert prepared.site_width == 350.0
    assert prepared.site_height == 300.0

    # Real Person 2 generate_candidates inference
    candidates = generate_candidates(graph, num_candidates=3, seed=42)
    assert len(candidates) == 3
    for cand in candidates:
        assert cand.site_width == 350.0
        assert cand.site_height == 300.0
        assert len(cand.buildings) == 4


# ---------------------------------------------------------------------------
# Test 15: Validation rejects non-dict campus input
# ---------------------------------------------------------------------------
def test_validation_rejects_non_dict_campus():
    with pytest.raises(ValueError, match="must be a non-empty dictionary"):
        build_graph(None)

    with pytest.raises(ValueError, match="must be a non-empty dictionary"):
        build_graph("invalid string")

    with pytest.raises(ValueError, match="must be a non-empty dictionary"):
        build_graph({})


# ---------------------------------------------------------------------------
# Test 16: Validation rejects building missing id, width, or depth
# ---------------------------------------------------------------------------
def test_validation_rejects_building_missing_required_fields(minimal_campus):
    # Missing id
    campus_no_id = copy.deepcopy(minimal_campus)
    del campus_no_id["buildings"][0]["id"]
    with pytest.raises(ValueError, match="missing required field: id"):
        build_graph(campus_no_id)

    # Missing width
    campus_no_w = copy.deepcopy(minimal_campus)
    del campus_no_w["buildings"][0]["width"]
    with pytest.raises(ValueError, match="missing required field: width"):
        build_graph(campus_no_w)

    # Missing depth
    campus_no_d = copy.deepcopy(minimal_campus)
    del campus_no_d["buildings"][0]["depth"]
    with pytest.raises(ValueError, match="missing required field: depth"):
        build_graph(campus_no_d)


# ---------------------------------------------------------------------------
# Test 17: Validation rejects non-positive building dimensions
# ---------------------------------------------------------------------------
def test_validation_rejects_non_positive_building_dimensions(minimal_campus):
    campus_zero_w = copy.deepcopy(minimal_campus)
    campus_zero_w["buildings"][0]["width"] = 0.0
    with pytest.raises(ValueError, match="dimensions must be positive"):
        build_graph(campus_zero_w)

    campus_neg_d = copy.deepcopy(minimal_campus)
    campus_neg_d["buildings"][0]["depth"] = -15.0
    with pytest.raises(ValueError, match="dimensions must be positive"):
        build_graph(campus_neg_d)


# ---------------------------------------------------------------------------
# Test 18: Validation rejects requiredCount < 1
# ---------------------------------------------------------------------------
def test_validation_rejects_required_count_less_than_one(minimal_campus):
    campus_zero_rc = copy.deepcopy(minimal_campus)
    campus_zero_rc["buildings"][0]["requiredCount"] = 0
    with pytest.raises(ValueError, match="requiredCount must be >= 1"):
        build_graph(campus_zero_rc)

    campus_neg_rc = copy.deepcopy(minimal_campus)
    campus_neg_rc["buildings"][0]["requiredCount"] = -2
    with pytest.raises(ValueError, match="requiredCount must be >= 1"):
        build_graph(campus_neg_rc)


# ---------------------------------------------------------------------------
# Test 19: Validation rejects duplicate building IDs
# ---------------------------------------------------------------------------
def test_validation_rejects_duplicate_building_ids(minimal_campus):
    campus_dup = copy.deepcopy(minimal_campus)
    campus_dup["buildings"].append(
        {"id": 1, "name": "Duplicate Building", "type": "library", "width": 30.0, "depth": 20.0}
    )
    with pytest.raises(ValueError, match="Duplicate building ID in catalogue: 1"):
        build_graph(campus_dup)


# ---------------------------------------------------------------------------
# Test 20: Validation rejects constraint referencing non-existent building ID
# ---------------------------------------------------------------------------
def test_validation_rejects_nonexistent_constraint_building_id(minimal_campus):
    campus_bad_src = copy.deepcopy(minimal_campus)
    campus_bad_src["constraints"] = [
        {"id": 99, "type": "MIN_DISTANCE", "sourceId": 999, "targetId": 1, "value": 20.0}
    ]
    with pytest.raises(ValueError, match="references non-existent building ID: 999"):
        build_graph(campus_bad_src)

    campus_bad_tgt = copy.deepcopy(minimal_campus)
    campus_bad_tgt["constraints"] = [
        {"id": 99, "type": "MIN_DISTANCE", "sourceId": 1, "targetId": 888, "value": 20.0}
    ]
    with pytest.raises(ValueError, match="references non-existent building ID: 888"):
        build_graph(campus_bad_tgt)


# ---------------------------------------------------------------------------
# Test 21: Every P1-emitted directed edge satisfies source < target
# ---------------------------------------------------------------------------
def test_all_emitted_directed_edges_satisfy_source_less_than_target(multi_building_campus):
    graph = build_graph(multi_building_campus)
    sources = graph.edge_index[0]
    targets = graph.edge_index[1]
    assert len(sources) > 0, "Graph should contain edges for multi_building_campus"
    assert len(sources) == len(targets) == len(graph.edge_features)
    for src, tgt in zip(sources, targets):
        assert src < tgt, f"Expected source < target, but got source={src}, target={tgt}"

