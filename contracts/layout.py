"""
contracts/layout.py
===================
Shared Python dataclass contracts for the AI Campus Planner project.
This is the single source of truth for all data shapes exchanged between modules.

Contract ownership (from architecture doc Section 4):
  CampusRequirements   — P4 produces, P1/P3 consume
  Building             — P4 produces, P1/P3 consume
  Constraint           — P4 produces, P1/P3 consume
  CampusGraph          — P1 produces, P2 consumes
  CandidateLayout      — P2 produces, P3 consumes
  RankedLayout         — P3 produces, P4 consumes
  Blueprint            — P4 produces, P6 consumes

DO NOT modify without team approval + version bump.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


# ---------------------------------------------------------------------------
# Coordinate system: origin = bottom-left, X = east, Y = north, metres.
# Rotation = degrees, counter-clockwise from east.
# ---------------------------------------------------------------------------


# ──────────────────────────────────────────────────────────────────────────────
# CONTRACT 2: Campus Requirements  (P4 → P1, P3)
# ──────────────────────────────────────────────────────────────────────────────
@dataclass
class Entrance:
    """Contract 3 — Entrance."""
    x: float
    y: float
    width: float


@dataclass
class CampusRequirements:
    """Contract 2 — Campus Requirements."""
    project_id: int
    site_width: float           # metres
    site_height: float          # metres
    min_green_percent: float    # 0–100
    min_parking_percent: float  # 0–100
    min_road_width: float       # metres
    min_building_gap: float     # metres
    entrances: List[Entrance] = field(default_factory=list)


# ──────────────────────────────────────────────────────────────────────────────
# CONTRACT 1: Building  (P4 → P1, P3)
# ──────────────────────────────────────────────────────────────────────────────
@dataclass
class Building:
    """Contract 1 — Building definition (catalogue entry, no position)."""
    id: int
    name: str
    type: str           # e.g. "academic", "library", "hostel"
    zone: str           # e.g. "academic", "residential", "sports"
    width: float        # metres (east-west footprint)
    depth: float        # metres (north-south footprint)
    height: float       # metres
    floor_count: int
    required_count: int = 1


# ──────────────────────────────────────────────────────────────────────────────
# CONTRACT (unnamed in doc): Constraint  (P4 → P1, P3)
# ──────────────────────────────────────────────────────────────────────────────
@dataclass
class Constraint:
    """Named constraint between two buildings."""
    id: int
    type: str           # "MIN_DISTANCE" | "MAX_DISTANCE" | "SAME_ZONE" | ...
    source_id: int      # building.id
    target_id: int      # building.id
    value: float
    operator: str       # ">=" | "<=" | "==" | "!="
    priority: str       # "hard" | "soft"


# ──────────────────────────────────────────────────────────────────────────────
# CONTRACT 4: Spatial Relationship  (P1 → P2)
# ──────────────────────────────────────────────────────────────────────────────
@dataclass
class SpatialRelationship:
    """Contract 4 — Spatial relationship (for graph edges)."""
    source_id: int
    target_id: int
    relation: str   # "NEAR" | "FAR" | "SAME_ZONE" | "ACCESSIBLE_FROM" | "ROAD_ACCESS"
    weight: float


# ──────────────────────────────────────────────────────────────────────────────
# CONTRACT 5: Campus Graph  (P1 → P2)
# ──────────────────────────────────────────────────────────────────────────────
@dataclass
class CampusGraph:
    """Contract 5 — Campus graph for GNN input."""
    node_features: List[List[float]]    # shape [N, F]
    edge_index: List[List[int]]         # shape [2, E]
    edge_features: List[List[float]]    # shape [E, G]


# ──────────────────────────────────────────────────────────────────────────────
# CONTRACT 6: Candidate Layout  (P2 → P3)
# ──────────────────────────────────────────────────────────────────────────────
@dataclass
class CandidateBuilding:
    """A building placed at a specific position within a candidate layout."""
    building_id: int
    x: float        # metres, bottom-left of bounding box
    y: float        # metres, bottom-left of bounding box
    rotation: float  # degrees
    # Width/depth are carried here for P3 constraint checks without a DB look-up.
    width: float = 0.0
    depth: float = 0.0
    zone: str = ""
    name: str = ""
    type: str = ""
    height: float = 0.0
    floor_count: int = 1


@dataclass
class CandidateLayout:
    """Contract 6 — Candidate layout produced by GNN/generator."""
    candidate_id: str
    site_width: float
    site_height: float
    buildings: List[CandidateBuilding] = field(default_factory=list)


# ──────────────────────────────────────────────────────────────────────────────
# Validation Result  (internal P3 type, also exposed to P4)
# ──────────────────────────────────────────────────────────────────────────────
@dataclass
class Violation:
    type: str
    building_ids: List[int]
    message: str
    severity: str   # "hard" | "soft"


@dataclass
class ValidationResult:
    """Contract 7 — Validation result."""
    feasible: bool
    violations: List[Violation] = field(default_factory=list)
    constraint_score: float = 1.0   # 1.0 = perfect, 0.0 = all violated


# ──────────────────────────────────────────────────────────────────────────────
# CONTRACT 8: Ranked Layout  (P3 → P4)
# ──────────────────────────────────────────────────────────────────────────────
@dataclass
class LayoutMetrics:
    land_utilization: float     # 0–1
    green_ratio: float          # 0–1
    parking_ratio: float        # 0–1
    accessibility_score: float  # 0–1
    road_efficiency: float      # 0–1
    constraint_score: float     # 0–1


@dataclass
class RankedLayout:
    """Contract 8 — Ranked layout returned by NSGA-II optimizer."""
    candidate_id: str
    rank: int
    feasible: bool
    buildings: List[CandidateBuilding]
    metrics: LayoutMetrics
    site_width: float = 300.0
    site_height: float = 300.0
    # Extra fields carried for Blueprint export (P4 fills roads/green/parking)
    validation: Optional[ValidationResult] = None


# ──────────────────────────────────────────────────────────────────────────────
# CONTRACT 9: Blueprint  (P4 → P6)
# ──────────────────────────────────────────────────────────────────────────────
@dataclass
class BlueprintBuilding:
    id: int
    name: str
    type: str
    zone: str
    x: float
    y: float
    width: float
    depth: float
    height: float
    rotation: float
    floor_count: int


@dataclass
class Road:
    x: float
    y: float
    width: float
    length: float
    rotation: float


@dataclass
class Area:
    x: float
    y: float
    width: float
    height: float


@dataclass
class Blueprint:
    """Contract 9 — Blueprint for Blender (P4 produces, P6 consumes)."""
    project_id: int
    layout_id: int
    site: dict          # {"width": float, "height": float}
    buildings: List[BlueprintBuilding] = field(default_factory=list)
    roads: List[Road] = field(default_factory=list)
    green_areas: List[Area] = field(default_factory=list)
    parking_areas: List[Area] = field(default_factory=list)
    entrances: List[Entrance] = field(default_factory=list)
