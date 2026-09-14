"""
ml/dataset/graph_builder.py
===========================
Person 1: Campus Graph Builder.

Transforms backend campus_data dictionary into Contract 5 CampusGraph:
    campus_data ──build_graph──▶ CampusGraph (node_features [N, 20], edge_index [2, E], edge_features [E, 9])

Adheres strictly to:
- docs/Technical_Architecture_6-Person_Execution_Contract_readable.pdf
- docs/ARCHOPT_TEAM_INTEGRATION_GUIDE.md (Part 4)
- docs/PERSON_1_IMPLEMENTATION_PLAN.md
- contracts/layout.py (Contract 5)
- ml/models/features.py (Feature encodings and vocabulary)
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

from contracts.layout import CampusGraph
from ml.dataset.validation import validate_campus_data
from ml.models.features import encode_edge, encode_node

# Functional adjacencies defined in architecture contract & mock_graph reference:
TYPE_RELATIONS: List[Tuple[str, str, str, float]] = [
    ("academic", "library", "NEAR", 0.9),
    ("hostel", "sports", "NEAR", 0.6),
    ("admin", "parking", "NEAR", 0.7),
    ("academic", "admin", "ACCESSIBLE_FROM", 0.5),
    ("library", "sports", "FAR", 0.5),
]


def build_graph(campus_data: Dict[str, Any]) -> CampusGraph:
    """
    Constructs a topological CampusGraph (Contract 5) from backend campus_data.

    Parameters
    ----------
    campus_data : dict containing siteWidth, siteHeight, buildings, constraints, entrances, etc.

    Returns
    -------
    CampusGraph : dataclass with node_features [N, 20], edge_index [2, E], edge_features [E, 9].
    """
    # 1. Strict input validation
    validate_campus_data(campus_data)

    site_width = float(campus_data["siteWidth"])
    site_height = float(campus_data["siteHeight"])

    # 2. Deterministic node expansion (sort by ID ascending)
    sorted_catalog_buildings = sorted(
        campus_data["buildings"],
        key=lambda b: int(b["id"]),
    )

    expanded_nodes: List[Dict[str, Any]] = []
    nodes_by_id: Dict[int, List[int]] = {}

    for b in sorted_catalog_buildings:
        b_id = int(b["id"])
        count = max(1, int(b.get("requiredCount", 1)))
        start_idx = len(expanded_nodes)
        for _ in range(count):
            node_idx = len(expanded_nodes)
            expanded_nodes.append(b)
            nodes_by_id.setdefault(b_id, []).append(node_idx)

    # 3. Node features encoding ([N, 20])
    node_features: List[List[float]] = []
    for b in expanded_nodes:
        height = float(b.get("height", 12.0)) if b.get("height") is not None else 12.0
        floor_count = int(b.get("floorCount", 1)) if b.get("floorCount") is not None else 1

        node_row = encode_node(
            building_id=int(b["id"]),
            width=float(b["width"]),
            depth=float(b["depth"]),
            height=height,
            floor_count=floor_count,
            building_type=str(b.get("type", "other")),
            zone=str(b.get("zone", "other")),
            site_width=site_width,
            site_height=site_height,
        )
        node_features.append(node_row)

    # 4. Edge construction: key = (u, v, relation_type) -> (weight, distance) with u < v
    edges_dict: Dict[Tuple[int, int, str], Tuple[float, float]] = {}

    def add_edge(i: int, j: int, relation: str, weight: float, distance: float = 0.0) -> None:
        if i == j:
            return
        u = min(i, j)
        v = max(i, j)
        rel_key = (u, v, relation.strip().upper())
        if rel_key in edges_dict:
            existing_weight, existing_dist = edges_dict[rel_key]
            # Keep higher weight; if equal weight, keep more restrictive distance
            if weight > existing_weight:
                edges_dict[rel_key] = (weight, distance)
            elif weight == existing_weight and distance > 0.0:
                edges_dict[rel_key] = (weight, distance)
        else:
            edges_dict[rel_key] = (weight, distance)

    n = len(expanded_nodes)

    # 4a. SAME_ZONE relationships between nodes sharing zone
    for i in range(n):
        for j in range(i + 1, n):
            z_i = str(expanded_nodes[i].get("zone", "")).strip().lower()
            z_j = str(expanded_nodes[j].get("zone", "")).strip().lower()
            if z_i and z_i == z_j:
                add_edge(i, j, "SAME_ZONE", 1.0, 0.0)

    # 4b. Functional type relationships
    for i in range(n):
        for j in range(i + 1, n):
            t_i = str(expanded_nodes[i].get("type", "")).strip().lower()
            t_j = str(expanded_nodes[j].get("type", "")).strip().lower()
            for type_a, type_b, relation, weight in TYPE_RELATIONS:
                if {t_i, t_j} == {type_a, type_b}:
                    add_edge(i, j, relation, weight, 0.0)

    # 4c. User constraints
    sorted_constraints = sorted(
        campus_data.get("constraints", []) or [],
        key=lambda c: int(c.get("id", 0)),
    )
    for c in sorted_constraints:
        c_type = str(c.get("type", "")).strip().upper()
        if c_type not in ("MIN_DISTANCE", "MAX_DISTANCE", "SAME_ZONE"):
            continue

        priority = str(c.get("priority", "hard")).strip().lower()
        weight = 1.0 if priority == "hard" else 0.5
        distance = float(c.get("value", 0.0)) if c_type in ("MIN_DISTANCE", "MAX_DISTANCE") else 0.0

        src_id = int(c["sourceId"])
        tgt_id = int(c["targetId"])

        for i in nodes_by_id.get(src_id, []):
            for j in nodes_by_id.get(tgt_id, []):
                if i != j:
                    add_edge(i, j, c_type, weight, distance)

    # 5. Deterministic edge sorting by (source_idx, target_idx, relation_type)
    sorted_edge_keys = sorted(
        edges_dict.keys(),
        key=lambda k: (k[0], k[1], k[2]),
    )

    if sorted_edge_keys:
        sources = [k[0] for k in sorted_edge_keys]
        targets = [k[1] for k in sorted_edge_keys]
        edge_features = [
            encode_edge(k[2], edges_dict[k][0], edges_dict[k][1])
            for k in sorted_edge_keys
        ]
        edge_index: List[List[int]] = [sources, targets]
    else:
        edge_index = [[], []]
        edge_features = []

    return CampusGraph(
        node_features=node_features,
        edge_index=edge_index,
        edge_features=edge_features,
    )
