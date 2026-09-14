"""
ml/training/mock_graph.py
=========================
Mock and synthetic CampusGraphs so Person 2 can develop and train before
Person 1's ml/dataset/graph_builder.py exists.

graph_from_campus_data() takes the same `campus_data` dict the backend builds
in backend/services/orchestrator.py and emits a CampusGraph in the column
layout of ml/models/features.py. It is a stand-in, not Person 1's builder:
once build_graph() lands, callers switch to it and nothing in
ml/models or ml/inference changes.

Building catalogue matches optimization/mock_data.py (300 × 300 m MVP campus).
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Tuple

import numpy as np

from contracts.layout import CampusGraph, CampusRequirements, Constraint, Entrance
from ml.models.features import encode_edge, encode_node

MVP_SITE_WIDTH = 300.0
MVP_SITE_HEIGHT = 300.0

MVP_BUILDINGS: List[Dict[str, Any]] = [
    {"id": 1, "name": "Academic Block A", "type": "academic", "zone": "academic",    "width": 60.0, "depth": 40.0, "height": 18.0, "floorCount": 4, "requiredCount": 1},
    {"id": 2, "name": "Academic Block B", "type": "academic", "zone": "academic",    "width": 60.0, "depth": 40.0, "height": 18.0, "floorCount": 4, "requiredCount": 1},
    {"id": 3, "name": "Library",          "type": "library",  "zone": "academic",    "width": 30.0, "depth": 25.0, "height": 12.0, "floorCount": 3, "requiredCount": 1},
    {"id": 4, "name": "Administration",   "type": "admin",    "zone": "admin",       "width": 40.0, "depth": 30.0, "height": 12.0, "floorCount": 3, "requiredCount": 1},
    {"id": 5, "name": "Hostel A",         "type": "hostel",   "zone": "residential", "width": 50.0, "depth": 30.0, "height": 15.0, "floorCount": 5, "requiredCount": 1},
    {"id": 6, "name": "Hostel B",         "type": "hostel",   "zone": "residential", "width": 50.0, "depth": 30.0, "height": 15.0, "floorCount": 5, "requiredCount": 1},
    {"id": 7, "name": "Hostel C",         "type": "hostel",   "zone": "residential", "width": 50.0, "depth": 30.0, "height": 15.0, "floorCount": 5, "requiredCount": 1},
    {"id": 8, "name": "Sports Complex",   "type": "sports",   "zone": "sports",      "width": 80.0, "depth": 60.0, "height": 10.0, "floorCount": 1, "requiredCount": 1},
    {"id": 9, "name": "Parking Area",     "type": "parking",  "zone": "parking",     "width": 40.0, "depth": 30.0, "height": 3.0,  "floorCount": 1, "requiredCount": 1},
]

MVP_CONSTRAINTS: List[Dict[str, Any]] = [
    {"id": 1, "type": "MIN_DISTANCE", "sourceId": 8, "targetId": 3, "value": 60.0,  "operator": ">=", "priority": "soft"},
    {"id": 2, "type": "MAX_DISTANCE", "sourceId": 1, "targetId": 3, "value": 120.0, "operator": "<=", "priority": "soft"},
]

MVP_ENTRANCES: List[Dict[str, float]] = [
    {"x": 145.0, "y": 0.0, "width": 12.0},
    {"x": 0.0, "y": 145.0, "width": 10.0},
]

# Functional adjacencies implied by building types (not user constraints).
TYPE_RELATIONS: List[Tuple[str, str, str, float]] = [
    ("academic", "library", "NEAR", 0.9),
    ("hostel", "sports", "NEAR", 0.6),
    ("admin", "parking", "NEAR", 0.7),
    ("academic", "admin", "ACCESSIBLE_FROM", 0.5),
    ("library", "sports", "FAR", 0.5),
]

# type → (zone, width, depth, height, floors, sampling probability)
_CATALOGUE: Dict[str, Tuple[str, float, float, float, int, float]] = {
    "academic": ("academic",    60.0, 40.0, 18.0, 4, 0.30),
    "library":  ("academic",    30.0, 25.0, 12.0, 3, 0.10),
    "hostel":   ("residential", 50.0, 30.0, 15.0, 5, 0.25),
    "admin":    ("admin",       40.0, 30.0, 12.0, 3, 0.10),
    "sports":   ("sports",      80.0, 60.0, 10.0, 1, 0.10),
    "parking":  ("parking",     40.0, 30.0, 3.0,  1, 0.15),
}


def mock_campus_data(
    site_width: float = MVP_SITE_WIDTH,
    site_height: float = MVP_SITE_HEIGHT,
) -> Dict[str, Any]:
    """Backend-shaped campus_data dict for the MVP campus."""
    return {
        "projectId": 1,
        "siteWidth": site_width,
        "siteHeight": site_height,
        "minGreenPercent": 25.0,
        "minParkingPercent": 10.0,
        "minRoadWidth": 8.0,
        "minBuildingGap": 10.0,
        "entrances": [dict(e) for e in MVP_ENTRANCES],
        "buildings": [dict(b) for b in MVP_BUILDINGS],
        "constraints": [dict(c) for c in MVP_CONSTRAINTS],
    }


def graph_from_campus_data(campus_data: Dict[str, Any]) -> CampusGraph:
    """
    Convert a backend campus_data dict into a CampusGraph (mock graph builder).

    Nodes: one per building copy (requiredCount expands).
    Edges (one direction each; the model symmetrises):
      SAME_ZONE between buildings sharing a zone,
      TYPE_RELATIONS between matching type pairs,
      MIN_DISTANCE / MAX_DISTANCE from user constraints (weight 1.0 hard, 0.5 soft).
    """
    site_width = float(campus_data["siteWidth"])
    site_height = float(campus_data["siteHeight"])

    buildings: List[Dict[str, Any]] = []
    for b in campus_data["buildings"]:
        buildings.extend([b] * max(1, int(b.get("requiredCount", 1))))

    node_features = [
        encode_node(
            building_id=b["id"],
            width=b["width"],
            depth=b["depth"],
            height=b.get("height", 0.0),
            floor_count=b.get("floorCount", 1),
            building_type=b.get("type", ""),
            zone=b.get("zone", ""),
            site_width=site_width,
            site_height=site_height,
        )
        for b in buildings
    ]

    sources: List[int] = []
    targets: List[int] = []
    edge_features: List[List[float]] = []

    def add_edge(i: int, j: int, relation: str, weight: float, distance: float = 0.0) -> None:
        sources.append(i)
        targets.append(j)
        edge_features.append(encode_edge(relation, weight, distance))

    for i in range(len(buildings)):
        for j in range(i + 1, len(buildings)):
            a, b = buildings[i], buildings[j]
            if a.get("zone") and a.get("zone") == b.get("zone"):
                add_edge(i, j, "SAME_ZONE", 1.0)
            for type_a, type_b, relation, weight in TYPE_RELATIONS:
                if {a.get("type"), b.get("type")} == {type_a, type_b}:
                    add_edge(i, j, relation, weight)

    nodes_by_id: Dict[int, List[int]] = {}
    for idx, b in enumerate(buildings):
        nodes_by_id.setdefault(int(b["id"]), []).append(idx)

    for c in campus_data.get("constraints", []):
        if c.get("type") not in ("MIN_DISTANCE", "MAX_DISTANCE"):
            continue
        weight = 1.0 if c.get("priority", "hard") == "hard" else 0.5
        for i in nodes_by_id.get(int(c["sourceId"]), []):
            for j in nodes_by_id.get(int(c["targetId"]), []):
                add_edge(i, j, c["type"], weight, float(c["value"]))

    return CampusGraph(
        node_features=node_features,
        edge_index=[sources, targets],
        edge_features=edge_features,
    )


def build_mock_campus_graph(
    site_width: float = MVP_SITE_WIDTH,
    site_height: float = MVP_SITE_HEIGHT,
) -> CampusGraph:
    """9-building MVP campus as a CampusGraph."""
    return graph_from_campus_data(mock_campus_data(site_width, site_height))


def mock_requirements(campus_data: Dict[str, Any] | None = None) -> CampusRequirements:
    """CampusRequirements matching mock_campus_data() (for Person 3 integration)."""
    data = campus_data or mock_campus_data()
    return CampusRequirements(
        project_id=int(data["projectId"]),
        site_width=float(data["siteWidth"]),
        site_height=float(data["siteHeight"]),
        min_green_percent=float(data["minGreenPercent"]),
        min_parking_percent=float(data["minParkingPercent"]),
        min_road_width=float(data["minRoadWidth"]),
        min_building_gap=float(data["minBuildingGap"]),
        entrances=[Entrance(x=e["x"], y=e["y"], width=e["width"]) for e in data["entrances"]],
    )


def mock_constraints(campus_data: Dict[str, Any] | None = None) -> List[Constraint]:
    """Constraint dataclasses matching mock_campus_data()."""
    data = campus_data or mock_campus_data()
    return [
        Constraint(
            id=int(c["id"]),
            type=c["type"],
            source_id=int(c["sourceId"]),
            target_id=int(c["targetId"]),
            value=float(c["value"]),
            operator=c["operator"],
            priority=c["priority"],
        )
        for c in data["constraints"]
    ]


def random_campus_data(rng: np.random.Generator) -> Dict[str, Any]:
    """Synthetic campus_data for training: random site, 5–12 buildings, a few constraints."""
    site_width = float(round(rng.uniform(220.0, 420.0)))
    site_height = float(round(rng.uniform(220.0, 420.0)))
    types = list(_CATALOGUE)
    probs = np.array([_CATALOGUE[t][5] for t in types])

    buildings: List[Dict[str, Any]] = []
    built_area = 0.0
    for idx in range(int(rng.integers(5, 13))):
        building_type = types[int(rng.choice(len(types), p=probs / probs.sum()))]
        zone, width, depth, height, floors, _ = _CATALOGUE[building_type]
        width = float(round(width * rng.uniform(0.75, 1.25)))
        depth = float(round(depth * rng.uniform(0.75, 1.25)))
        if built_area + width * depth > 0.3 * site_width * site_height:
            break
        built_area += width * depth
        buildings.append({
            "id": idx + 1,
            "name": f"{building_type.capitalize()} {idx + 1}",
            "type": building_type,
            "zone": zone,
            "width": width,
            "depth": depth,
            "height": height,
            "floorCount": floors,
            "requiredCount": 1,
        })

    diagonal = math.hypot(site_width, site_height)
    constraints: List[Dict[str, Any]] = []
    for cid in range(int(rng.integers(0, 3))):
        source, target = rng.choice(len(buildings), size=2, replace=False)
        kind = "MIN_DISTANCE" if rng.random() < 0.5 else "MAX_DISTANCE"
        constraints.append({
            "id": cid + 1,
            "type": kind,
            "sourceId": int(source) + 1,
            "targetId": int(target) + 1,
            "value": float(round(diagonal * (rng.uniform(0.15, 0.3) if kind == "MIN_DISTANCE" else rng.uniform(0.3, 0.5)))),
            "operator": ">=" if kind == "MIN_DISTANCE" else "<=",
            "priority": "hard" if rng.random() < 0.5 else "soft",
        })

    return {
        "projectId": 0,
        "siteWidth": site_width,
        "siteHeight": site_height,
        "minGreenPercent": 25.0,
        "minParkingPercent": 10.0,
        "minRoadWidth": 8.0,
        "minBuildingGap": 10.0,
        "entrances": [],
        "buildings": buildings,
        "constraints": constraints,
    }


def random_campus_graph(rng: np.random.Generator) -> CampusGraph:
    return graph_from_campus_data(random_campus_data(rng))
