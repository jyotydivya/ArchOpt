"""
ml/models/features.py
=====================
Column layout of the CampusGraph (Contract 5) that the GNN reads.

Contract 5 fixes only the *shapes* of node_features [N, F], edge_index [2, E]
and edge_features [E, G]. The generator also needs each building's id,
footprint, type, zone and the site size to emit fully-populated
CandidateBuilding objects, so the column meaning is fixed here.
Person 1's build_graph() should build rows with encode_node() / encode_edge()
so both sides stay in sync.

Node feature row (NODE_FEATURE_DIM = 20)
    0       building_id     backend DB id (float-encoded int)
    1       width           metres, east-west footprint
    2       depth           metres, north-south footprint
    3       height          metres
    4       floor_count
    5       site_width      metres (same value on every row)
    6       site_height     metres (same value on every row)
    7..13   type one-hot    academic, library, hostel, admin, sports, parking, other
    14..19  zone one-hot    academic, residential, sports, admin, parking, other

Edge feature row (EDGE_FEATURE_DIM = 9)
    0..6    relation one-hot  NEAR, FAR, SAME_ZONE, ACCESSIBLE_FROM, ROAD_ACCESS,
                              MIN_DISTANCE, MAX_DISTANCE
    7       weight            relationship strength, 0–1
    8       distance          metres; target for MIN/MAX_DISTANCE, 0 otherwise

Extra trailing node columns are ignored. Edge rows shorter or longer than
EDGE_FEATURE_DIM are zero-padded / truncated.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, List, Sequence, Tuple

import numpy as np

BUILDING_TYPES: Tuple[str, ...] = (
    "academic", "library", "hostel", "admin", "sports", "parking", "other",
)
ZONES: Tuple[str, ...] = (
    "academic", "residential", "sports", "admin", "parking", "other",
)
EDGE_RELATIONS: Tuple[str, ...] = (
    "NEAR", "FAR", "SAME_ZONE", "ACCESSIBLE_FROM", "ROAD_ACCESS",
    "MIN_DISTANCE", "MAX_DISTANCE",
)

NODE_BASE_COLUMNS: Tuple[str, ...] = (
    "building_id", "width", "depth", "height", "floor_count",
    "site_width", "site_height",
)
NODE_FEATURE_COLUMNS: Tuple[str, ...] = (
    NODE_BASE_COLUMNS
    + tuple(f"type_{t}" for t in BUILDING_TYPES)
    + tuple(f"zone_{z}" for z in ZONES)
)
NODE_FEATURE_DIM = len(NODE_FEATURE_COLUMNS)

EDGE_FEATURE_COLUMNS: Tuple[str, ...] = (
    tuple(f"rel_{r.lower()}" for r in EDGE_RELATIONS) + ("weight", "distance")
)
EDGE_FEATURE_DIM = len(EDGE_FEATURE_COLUMNS)

TYPE_START = len(NODE_BASE_COLUMNS)
ZONE_START = TYPE_START + len(BUILDING_TYPES)
WEIGHT_COLUMN = len(EDGE_RELATIONS)
DISTANCE_COLUMN = WEIGHT_COLUMN + 1

# Normalised inputs the network actually sees.
_NODE_SCALARS = 6
NODE_INPUT_DIM = _NODE_SCALARS + len(BUILDING_TYPES) + len(ZONES)
EDGE_INPUT_DIM = EDGE_FEATURE_DIM

_HEIGHT_SCALE = 60.0
_FLOOR_SCALE = 10.0


# ── Encoding (used by graph builders) ─────────────────────────────────────────

def _one_hot(value: str, vocab: Sequence[str]) -> List[float]:
    key = (value or "").strip().lower()
    if key not in vocab:
        key = "other"
    return [1.0 if v == key else 0.0 for v in vocab]


def encode_node(
    *,
    building_id: int,
    width: float,
    depth: float,
    height: float,
    floor_count: int,
    building_type: str,
    zone: str,
    site_width: float,
    site_height: float,
) -> List[float]:
    """Return one node_features row in the NODE_FEATURE_COLUMNS layout."""
    return (
        [
            float(building_id), float(width), float(depth), float(height),
            float(floor_count), float(site_width), float(site_height),
        ]
        + _one_hot(building_type, BUILDING_TYPES)
        + _one_hot(zone, ZONES)
    )


def encode_edge(relation: str, weight: float = 1.0, distance: float = 0.0) -> List[float]:
    """Return one edge_features row in the EDGE_FEATURE_COLUMNS layout."""
    key = relation.strip().upper()
    if key not in EDGE_RELATIONS:
        raise ValueError(
            f"Unknown edge relation {relation!r}; expected one of {EDGE_RELATIONS}"
        )
    return [1.0 if r == key else 0.0 for r in EDGE_RELATIONS] + [float(weight), float(distance)]


# ── Decoding (used by the generator) ──────────────────────────────────────────

@dataclass(frozen=True)
class NodeInfo:
    """Building attributes recovered from one node_features row."""
    building_id: int
    width: float
    depth: float
    height: float
    floor_count: int
    type: str
    zone: str

    @property
    def name(self) -> str:
        # The graph carries no names; the backend re-attaches catalogue names
        # from the DB when it builds the blueprint.
        return f"{self.type.capitalize()} {self.building_id}"


@dataclass
class PreparedGraph:
    """A validated CampusGraph plus the normalised arrays the model consumes."""
    nodes: List[NodeInfo]
    site_width: float
    site_height: float
    node_inputs: np.ndarray         # [N, NODE_INPUT_DIM]
    edge_index: np.ndarray          # [2, 2E] — both directions
    edge_inputs: np.ndarray         # [2E, EDGE_INPUT_DIM]
    raw_edge_index: np.ndarray      # [2, E] as supplied
    raw_edge_features: np.ndarray   # [E, EDGE_FEATURE_DIM] padded / truncated

    @property
    def num_nodes(self) -> int:
        return len(self.nodes)

    @property
    def widths(self) -> np.ndarray:
        return np.array([n.width for n in self.nodes], dtype=np.float64)

    @property
    def depths(self) -> np.ndarray:
        return np.array([n.depth for n in self.nodes], dtype=np.float64)

    @property
    def zone_ids(self) -> np.ndarray:
        return np.array([ZONES.index(n.zone) for n in self.nodes], dtype=np.int64)


def _graph_field(graph: Any, snake: str, camel: str) -> Any:
    """Read a CampusGraph field from a dataclass, camelCase object or dict."""
    for key in (snake, camel):
        if isinstance(graph, dict):
            if key in graph:
                return graph[key]
        elif hasattr(graph, key):
            return getattr(graph, key)
    raise ValueError(f"CampusGraph is missing '{snake}' (or '{camel}')")


def _vocab_label(row: np.ndarray, vocab: Sequence[str]) -> str:
    if not np.any(row > 0):
        return "other"
    return vocab[int(np.argmax(row))]


def prepare_graph(campus_graph: Any) -> PreparedGraph:
    """
    Validate a CampusGraph and convert it into model-ready arrays.

    Accepts the contracts.layout.CampusGraph dataclass, an object with
    camelCase attributes, or a dict with snake_case / camelCase keys.
    Raises ValueError with a readable message on malformed input.
    """
    node = np.asarray(_graph_field(campus_graph, "node_features", "nodeFeatures"), dtype=np.float64)
    if node.ndim != 2 or node.shape[0] == 0:
        raise ValueError("node_features must be a non-empty [N, F] matrix")
    if node.shape[1] < NODE_FEATURE_DIM:
        raise ValueError(
            f"node_features rows need {NODE_FEATURE_DIM} columns "
            f"({', '.join(NODE_FEATURE_COLUMNS)}); got {node.shape[1]}. "
            "See ml/README.md for the layout."
        )
    node = node[:, :NODE_FEATURE_DIM]
    if not np.all(np.isfinite(node)):
        raise ValueError("node_features contains NaN or infinite values")

    site_width, site_height = float(node[0, 5]), float(node[0, 6])
    if site_width <= 0 or site_height <= 0:
        raise ValueError(f"site size must be positive, got {site_width} x {site_height}")
    if np.any(node[:, 1] <= 0) or np.any(node[:, 2] <= 0):
        raise ValueError("every building needs width > 0 and depth > 0")

    nodes = [
        NodeInfo(
            building_id=int(round(row[0])),
            width=float(row[1]),
            depth=float(row[2]),
            height=float(max(row[3], 0.0)),
            floor_count=max(1, int(round(row[4]))),
            type=_vocab_label(row[TYPE_START:ZONE_START], BUILDING_TYPES),
            zone=_vocab_label(row[ZONE_START:NODE_FEATURE_DIM], ZONES),
        )
        for row in node
    ]
    n = len(nodes)

    raw_index = np.asarray(_graph_field(campus_graph, "edge_index", "edgeIndex"), dtype=np.float64)
    if raw_index.size == 0:
        raw_index = np.zeros((2, 0))
    if raw_index.ndim != 2 or raw_index.shape[0] != 2:
        raise ValueError(f"edge_index must have shape [2, E], got {raw_index.shape}")
    edge_index = raw_index.astype(np.int64)
    if np.any(edge_index < 0) or np.any(edge_index >= n):
        raise ValueError(f"edge_index refers to nodes outside 0..{n - 1}")
    num_edges = edge_index.shape[1]

    raw_edge = np.asarray(_graph_field(campus_graph, "edge_features", "edgeFeatures"), dtype=np.float64)
    if raw_edge.size == 0:
        raw_edge = np.zeros((num_edges, 0))
    if raw_edge.ndim != 2 or raw_edge.shape[0] != num_edges:
        raise ValueError(
            f"edge_features must have one row per edge ({num_edges}), got shape {raw_edge.shape}"
        )
    edge = np.zeros((num_edges, EDGE_FEATURE_DIM))
    cols = min(EDGE_FEATURE_DIM, raw_edge.shape[1])
    edge[:, :cols] = raw_edge[:, :cols]
    if not np.all(np.isfinite(edge)):
        raise ValueError("edge_features contains NaN or infinite values")

    widths, depths = node[:, 1], node[:, 2]
    node_inputs = np.column_stack([
        widths / site_width,
        depths / site_height,
        node[:, 3] / _HEIGHT_SCALE,
        node[:, 4] / _FLOOR_SCALE,
        10.0 * widths * depths / (site_width * site_height),
        np.full(n, site_width / site_height),
        node[:, TYPE_START:NODE_FEATURE_DIM],
    ])

    edge_inputs = edge.copy()
    edge_inputs[:, DISTANCE_COLUMN] /= math.hypot(site_width, site_height)

    return PreparedGraph(
        nodes=nodes,
        site_width=site_width,
        site_height=site_height,
        node_inputs=node_inputs,
        edge_index=np.concatenate([edge_index, edge_index[::-1]], axis=1),
        edge_inputs=np.concatenate([edge_inputs, edge_inputs], axis=0),
        raw_edge_index=edge_index,
        raw_edge_features=edge,
    )
