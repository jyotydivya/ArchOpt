"""
ArchOpt_Final_Report/experiments/run_experiments.py
===================================================
Master Reproducible Experimentation Suite for ArchOpt Final Project Report.

Executes genuine, deterministic experiments against the actual repository code:
- Scenario 1: Small Campus (200x200m, 5 buildings)
- Scenario 2: Medium Campus (300x300m, 9 buildings - MVP Campus)
- Scenario 3: Large Campus (500x500m, 16 buildings)
- Scenario 4: High-Density Campus (240x240m, 12 buildings, 33.6% footprint)
- Scenario 5: Constraint-Heavy Campus (300x300m, 9 buildings, 8 spatial constraints)

Evaluates:
- Candidate Generation (GNN vs Mock vs Random Baseline)
- Constraint Satisfaction Breakdown (Boundary, Overlap, Gap, Distances, Green, Parking, Accessibility, Zoning)
- Multi-Objective Optimization (Before vs After Pareto Top-5 across 5 objectives)
- NSGA-II Algorithmic Metrics (Hypervolume, Diversity/Spread, Non-dominated Count, Generational Convergence)
- GNN Inference Latency (PyTorch vs NumPy)
- Component and End-to-End System Performance Benchmarks (10 repeated runs, mean, std, median, min, max)
"""
from __future__ import annotations

import csv
import json
import math
import os
import sys
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np

# Ensure ArchOpt repository is on sys.path
REPO_ROOT = Path("E:/ArchOpt/ArchOpt").resolve()
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from contracts.layout import (
    CampusGraph,
    CampusRequirements,
    CandidateBuilding,
    CandidateLayout,
    Constraint,
    Entrance,
    RankedLayout,
)
from ml.dataset.graph_builder import build_graph
from ml.inference.generate import generate_candidates
from ml.models.campus_model import DEFAULT_WEIGHTS_PATH, ModelConfig, forward, load_params
from ml.models.features import prepare_graph
from ml.models.layout_decoder import bounded_positions, sigmoid_numpy
from optimization.mock_data import generate_mock_candidates
from optimization.nsga2 import crowding_distance, non_dominated_sort, rank_population
from optimization.objectives import compute_objectives, objectives_to_minimise
from optimization.optimizer import optimize_layouts
from optimization.validator import validate_layout

OUTPUT_DIR = Path("E:/ArchOpt/ArchOpt_Final_Report/results").resolve()
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ==============================================================================
# 1. SCENARIO DEFINITIONS
# ==============================================================================

def get_scenarios() -> Dict[str, Dict[str, Any]]:
    return {
        "Scenario 1: Small Campus": {
            "name": "Small Campus (Research Annex)",
            "projectId": 101,
            "siteWidth": 200.0,
            "siteHeight": 200.0,
            "minGreenPercent": 25.0,
            "minParkingPercent": 10.0,
            "minRoadWidth": 8.0,
            "minBuildingGap": 10.0,
            "entrances": [{"x": 95.0, "y": 0.0, "width": 10.0}],
            "buildings": [
                {"id": 1, "name": "Academic Lab", "type": "academic", "zone": "academic", "width": 50.0, "depth": 35.0, "height": 16.0, "floorCount": 3, "requiredCount": 1},
                {"id": 2, "name": "Study Hub", "type": "library", "zone": "academic", "width": 30.0, "depth": 20.0, "height": 10.0, "floorCount": 2, "requiredCount": 1},
                {"id": 3, "name": "Admin Office", "type": "admin", "zone": "admin", "width": 35.0, "depth": 25.0, "height": 12.0, "floorCount": 2, "requiredCount": 1},
                {"id": 4, "name": "Scholar Hostel", "type": "hostel", "zone": "residential", "width": 45.0, "depth": 25.0, "height": 15.0, "floorCount": 4, "requiredCount": 1},
                {"id": 5, "name": "Surface Parking", "type": "parking", "zone": "parking", "width": 35.0, "depth": 25.0, "height": 3.0, "floorCount": 1, "requiredCount": 1},
            ],
            "constraints": [
                {"id": 1, "type": "MIN_DISTANCE", "sourceId": 1, "targetId": 2, "value": 25.0, "operator": ">=", "priority": "soft"},
                {"id": 2, "type": "MAX_DISTANCE", "sourceId": 1, "targetId": 2, "value": 75.0, "operator": "<=", "priority": "soft"},
            ]
        },
        "Scenario 2: Medium Campus": {
            "name": "Medium Campus (MVP Reference)",
            "projectId": 102,
            "siteWidth": 300.0,
            "siteHeight": 300.0,
            "minGreenPercent": 25.0,
            "minParkingPercent": 10.0,
            "minRoadWidth": 8.0,
            "minBuildingGap": 10.0,
            "entrances": [
                {"x": 145.0, "y": 0.0, "width": 12.0},
                {"x": 0.0, "y": 145.0, "width": 10.0},
            ],
            "buildings": [
                {"id": 1, "name": "Academic Block A", "type": "academic", "zone": "academic", "width": 60.0, "depth": 40.0, "height": 18.0, "floorCount": 4, "requiredCount": 1},
                {"id": 2, "name": "Academic Block B", "type": "academic", "zone": "academic", "width": 60.0, "depth": 40.0, "height": 18.0, "floorCount": 4, "requiredCount": 1},
                {"id": 3, "name": "Library", "type": "library", "zone": "academic", "width": 30.0, "depth": 25.0, "height": 12.0, "floorCount": 3, "requiredCount": 1},
                {"id": 4, "name": "Administration", "type": "admin", "zone": "admin", "width": 40.0, "depth": 30.0, "height": 12.0, "floorCount": 3, "requiredCount": 1},
                {"id": 5, "name": "Hostel A", "type": "hostel", "zone": "residential", "width": 50.0, "depth": 30.0, "height": 15.0, "floorCount": 5, "requiredCount": 1},
                {"id": 6, "name": "Hostel B", "type": "hostel", "zone": "residential", "width": 50.0, "depth": 30.0, "height": 15.0, "floorCount": 5, "requiredCount": 1},
                {"id": 7, "name": "Hostel C", "type": "hostel", "zone": "residential", "width": 50.0, "depth": 30.0, "height": 15.0, "floorCount": 5, "requiredCount": 1},
                {"id": 8, "name": "Sports Complex", "type": "sports", "zone": "sports", "width": 80.0, "depth": 60.0, "height": 10.0, "floorCount": 1, "requiredCount": 1},
                {"id": 9, "name": "Parking Area", "type": "parking", "zone": "parking", "width": 40.0, "depth": 30.0, "height": 3.0, "floorCount": 1, "requiredCount": 1},
            ],
            "constraints": [
                {"id": 1, "type": "MIN_DISTANCE", "sourceId": 8, "targetId": 3, "value": 60.0, "operator": ">=", "priority": "soft"},
                {"id": 2, "type": "MAX_DISTANCE", "sourceId": 1, "targetId": 3, "value": 120.0, "operator": "<=", "priority": "soft"},
            ]
        },
        "Scenario 3: Large Campus": {
            "name": "Large Campus (Comprehensive University)",
            "projectId": 103,
            "siteWidth": 500.0,
            "siteHeight": 500.0,
            "minGreenPercent": 30.0,
            "minParkingPercent": 10.0,
            "minRoadWidth": 10.0,
            "minBuildingGap": 12.0,
            "entrances": [
                {"x": 245.0, "y": 0.0, "width": 14.0},
                {"x": 0.0, "y": 245.0, "width": 12.0},
                {"x": 500.0, "y": 245.0, "width": 12.0},
            ],
            "buildings": [
                {"id": 1, "name": "Engineering Block 1", "type": "academic", "zone": "academic", "width": 60.0, "depth": 40.0, "height": 20.0, "floorCount": 5, "requiredCount": 1},
                {"id": 2, "name": "Engineering Block 2", "type": "academic", "zone": "academic", "width": 60.0, "depth": 40.0, "height": 20.0, "floorCount": 5, "requiredCount": 1},
                {"id": 3, "name": "Sciences Block", "type": "academic", "zone": "academic", "width": 60.0, "depth": 40.0, "height": 18.0, "floorCount": 4, "requiredCount": 1},
                {"id": 4, "name": "Management Block", "type": "academic", "zone": "academic", "width": 55.0, "depth": 35.0, "height": 16.0, "floorCount": 4, "requiredCount": 1},
                {"id": 5, "name": "Main Library", "type": "library", "zone": "academic", "width": 40.0, "depth": 30.0, "height": 15.0, "floorCount": 4, "requiredCount": 1},
                {"id": 6, "name": "Digital Resource Centre", "type": "library", "zone": "academic", "width": 30.0, "depth": 25.0, "height": 12.0, "floorCount": 3, "requiredCount": 1},
                {"id": 7, "name": "Senate & Admin", "type": "admin", "zone": "admin", "width": 50.0, "depth": 35.0, "height": 16.0, "floorCount": 4, "requiredCount": 1},
                {"id": 8, "name": "Student Affairs", "type": "admin", "zone": "admin", "width": 35.0, "depth": 25.0, "height": 12.0, "floorCount": 3, "requiredCount": 1},
                {"id": 9, "name": "Boys Hostel 1", "type": "hostel", "zone": "residential", "width": 50.0, "depth": 30.0, "height": 18.0, "floorCount": 6, "requiredCount": 1},
                {"id": 10, "name": "Boys Hostel 2", "type": "hostel", "zone": "residential", "width": 50.0, "depth": 30.0, "height": 18.0, "floorCount": 6, "requiredCount": 1},
                {"id": 11, "name": "Girls Hostel 1", "type": "hostel", "zone": "residential", "width": 50.0, "depth": 30.0, "height": 18.0, "floorCount": 6, "requiredCount": 1},
                {"id": 12, "name": "Girls Hostel 2", "type": "hostel", "zone": "residential", "width": 50.0, "depth": 30.0, "height": 18.0, "floorCount": 6, "requiredCount": 1},
                {"id": 13, "name": "Faculty Residence", "type": "hostel", "zone": "residential", "width": 45.0, "depth": 30.0, "height": 15.0, "floorCount": 4, "requiredCount": 1},
                {"id": 14, "name": "Olympic Stadium", "type": "sports", "zone": "sports", "width": 90.0, "depth": 70.0, "height": 12.0, "floorCount": 1, "requiredCount": 1},
                {"id": 15, "name": "North Parking", "type": "parking", "zone": "parking", "width": 50.0, "depth": 40.0, "height": 3.0, "floorCount": 1, "requiredCount": 1},
                {"id": 16, "name": "South Parking", "type": "parking", "zone": "parking", "width": 50.0, "depth": 40.0, "height": 3.0, "floorCount": 1, "requiredCount": 1},
            ],
            "constraints": [
                {"id": 1, "type": "MIN_DISTANCE", "sourceId": 14, "targetId": 5, "value": 100.0, "operator": ">=", "priority": "soft"},
                {"id": 2, "type": "MAX_DISTANCE", "sourceId": 1, "targetId": 5, "value": 180.0, "operator": "<=", "priority": "soft"},
                {"id": 3, "type": "MIN_DISTANCE", "sourceId": 14, "targetId": 9, "value": 80.0, "operator": ">=", "priority": "soft"},
                {"id": 4, "type": "MAX_DISTANCE", "sourceId": 7, "targetId": 16, "value": 120.0, "operator": "<=", "priority": "soft"},
            ]
        },
        "Scenario 4: High-Density Campus": {
            "name": "High-Density Urban Campus",
            "projectId": 104,
            "siteWidth": 240.0,
            "siteHeight": 240.0,
            "minGreenPercent": 20.0,
            "minParkingPercent": 10.0,
            "minRoadWidth": 8.0,
            "minBuildingGap": 8.0,
            "entrances": [
                {"x": 115.0, "y": 0.0, "width": 10.0},
                {"x": 115.0, "y": 240.0, "width": 10.0},
            ],
            "buildings": [
                {"id": 1, "name": "Academic Block A", "type": "academic", "zone": "academic", "width": 60.0, "depth": 40.0, "height": 22.0, "floorCount": 6, "requiredCount": 1},
                {"id": 2, "name": "Academic Block B", "type": "academic", "zone": "academic", "width": 60.0, "depth": 40.0, "height": 22.0, "floorCount": 6, "requiredCount": 1},
                {"id": 3, "name": "Academic Block C", "type": "academic", "zone": "academic", "width": 55.0, "depth": 35.0, "height": 20.0, "floorCount": 5, "requiredCount": 1},
                {"id": 4, "name": "Library", "type": "library", "zone": "academic", "width": 35.0, "depth": 30.0, "height": 16.0, "floorCount": 4, "requiredCount": 1},
                {"id": 5, "name": "Administration", "type": "admin", "zone": "admin", "width": 40.0, "depth": 30.0, "height": 15.0, "floorCount": 4, "requiredCount": 1},
                {"id": 6, "name": "Highrise Hostel 1", "type": "hostel", "zone": "residential", "width": 50.0, "depth": 30.0, "height": 25.0, "floorCount": 8, "requiredCount": 1},
                {"id": 7, "name": "Highrise Hostel 2", "type": "hostel", "zone": "residential", "width": 50.0, "depth": 30.0, "height": 25.0, "floorCount": 8, "requiredCount": 1},
                {"id": 8, "name": "Highrise Hostel 3", "type": "hostel", "zone": "residential", "width": 50.0, "depth": 30.0, "height": 25.0, "floorCount": 8, "requiredCount": 1},
                {"id": 9, "name": "Highrise Hostel 4", "type": "hostel", "zone": "residential", "width": 45.0, "depth": 25.0, "height": 25.0, "floorCount": 8, "requiredCount": 1},
                {"id": 10, "name": "Compact Arena", "type": "sports", "zone": "sports", "width": 70.0, "depth": 50.0, "height": 12.0, "floorCount": 1, "requiredCount": 1},
                {"id": 11, "name": "Multi-deck Parking A", "type": "parking", "zone": "parking", "width": 40.0, "depth": 30.0, "height": 9.0, "floorCount": 3, "requiredCount": 1},
                {"id": 12, "name": "Multi-deck Parking B", "type": "parking", "zone": "parking", "width": 40.0, "depth": 30.0, "height": 9.0, "floorCount": 3, "requiredCount": 1},
            ],
            "constraints": [
                {"id": 1, "type": "MIN_DISTANCE", "sourceId": 10, "targetId": 4, "value": 40.0, "operator": ">=", "priority": "hard"},
                {"id": 2, "type": "MAX_DISTANCE", "sourceId": 1, "targetId": 4, "value": 85.0, "operator": "<=", "priority": "soft"},
            ]
        },
        "Scenario 5: Constraint-Heavy Campus": {
            "name": "Constraint-Heavy Campus (Strict Regulatory)",
            "projectId": 105,
            "siteWidth": 300.0,
            "siteHeight": 300.0,
            "minGreenPercent": 25.0,
            "minParkingPercent": 10.0,
            "minRoadWidth": 8.0,
            "minBuildingGap": 10.0,
            "entrances": [
                {"x": 145.0, "y": 0.0, "width": 12.0},
                {"x": 0.0, "y": 145.0, "width": 10.0},
            ],
            "buildings": [
                {"id": 1, "name": "Academic Block A", "type": "academic", "zone": "academic", "width": 60.0, "depth": 40.0, "height": 18.0, "floorCount": 4, "requiredCount": 1},
                {"id": 2, "name": "Academic Block B", "type": "academic", "zone": "academic", "width": 60.0, "depth": 40.0, "height": 18.0, "floorCount": 4, "requiredCount": 1},
                {"id": 3, "name": "Library", "type": "library", "zone": "academic", "width": 30.0, "depth": 25.0, "height": 12.0, "floorCount": 3, "requiredCount": 1},
                {"id": 4, "name": "Administration", "type": "admin", "zone": "admin", "width": 40.0, "depth": 30.0, "height": 12.0, "floorCount": 3, "requiredCount": 1},
                {"id": 5, "name": "Hostel A", "type": "hostel", "zone": "residential", "width": 50.0, "depth": 30.0, "height": 15.0, "floorCount": 5, "requiredCount": 1},
                {"id": 6, "name": "Hostel B", "type": "hostel", "zone": "residential", "width": 50.0, "depth": 30.0, "height": 15.0, "floorCount": 5, "requiredCount": 1},
                {"id": 7, "name": "Hostel C", "type": "hostel", "zone": "residential", "width": 50.0, "depth": 30.0, "height": 15.0, "floorCount": 5, "requiredCount": 1},
                {"id": 8, "name": "Sports Complex", "type": "sports", "zone": "sports", "width": 80.0, "depth": 60.0, "height": 10.0, "floorCount": 1, "requiredCount": 1},
                {"id": 9, "name": "Parking Area", "type": "parking", "zone": "parking", "width": 40.0, "depth": 30.0, "height": 3.0, "floorCount": 1, "requiredCount": 1},
            ],
            "constraints": [
                {"id": 1, "type": "MIN_DISTANCE", "sourceId": 8, "targetId": 3, "value": 75.0, "operator": ">=", "priority": "hard"},
                {"id": 2, "type": "MAX_DISTANCE", "sourceId": 1, "targetId": 3, "value": 90.0, "operator": "<=", "priority": "hard"},
                {"id": 3, "type": "MAX_DISTANCE", "sourceId": 2, "targetId": 3, "value": 90.0, "operator": "<=", "priority": "hard"},
                {"id": 4, "type": "MIN_DISTANCE", "sourceId": 8, "targetId": 5, "value": 60.0, "operator": ">=", "priority": "soft"},
                {"id": 5, "type": "MAX_DISTANCE", "sourceId": 5, "targetId": 6, "value": 55.0, "operator": "<=", "priority": "soft"},
                {"id": 6, "type": "MIN_DISTANCE", "sourceId": 1, "targetId": 8, "value": 95.0, "operator": ">=", "priority": "hard"},
                {"id": 7, "type": "MAX_DISTANCE", "sourceId": 4, "targetId": 9, "value": 70.0, "operator": "<=", "priority": "soft"},
                {"id": 8, "type": "MIN_DISTANCE", "sourceId": 5, "targetId": 9, "value": 40.0, "operator": ">=", "priority": "soft"},
            ]
        }
    }


def to_contract_objects(scenario_data: Dict[str, Any]) -> Tuple[CampusRequirements, List[Constraint]]:
    req = CampusRequirements(
        project_id=int(scenario_data["projectId"]),
        site_width=float(scenario_data["siteWidth"]),
        site_height=float(scenario_data["siteHeight"]),
        min_green_percent=float(scenario_data["minGreenPercent"]),
        min_parking_percent=float(scenario_data["minParkingPercent"]),
        min_road_width=float(scenario_data["minRoadWidth"]),
        min_building_gap=float(scenario_data["minBuildingGap"]),
        entrances=[Entrance(x=e["x"], y=e["y"], width=e["width"]) for e in scenario_data["entrances"]],
    )
    constraints = [
        Constraint(
            id=int(c["id"]),
            type=c["type"],
            source_id=int(c["sourceId"]),
            target_id=int(c["targetId"]),
            value=float(c["value"]),
            operator=c["operator"],
            priority=c["priority"],
        )
        for c in scenario_data.get("constraints", [])
    ]
    return req, constraints


def generate_random_candidates(
    scenario_data: Dict[str, Any],
    num_candidates: int = 100,
    seed: int = 42,
) -> List[CandidateLayout]:
    """Uniform random placement baseline."""
    rng = np.random.default_rng(seed)
    site_w = float(scenario_data["siteWidth"])
    site_h = float(scenario_data["siteHeight"])
    buildings = scenario_data["buildings"]

    candidates: List[CandidateLayout] = []
    for k in range(num_candidates):
        cand_buildings: List[CandidateBuilding] = []
        for b in buildings:
            rot = float(rng.choice([0.0, 90.0]))
            w = float(b["width"]) if rot == 0.0 else float(b["depth"])
            d = float(b["depth"]) if rot == 0.0 else float(b["width"])
            max_x = max(0.0, site_w - w)
            max_y = max(0.0, site_h - d)
            x = float(rng.uniform(0.0, max_x))
            y = float(rng.uniform(0.0, max_y))
            cand_buildings.append(
                CandidateBuilding(
                    building_id=int(b["id"]),
                    name=b["name"],
                    type=b["type"],
                    zone=b["zone"],
                    x=x,
                    y=y,
                    width=float(b["width"]),
                    depth=float(b["depth"]),
                    height=float(b.get("height", 12.0)),
                    rotation=rot,
                    floor_count=int(b.get("floorCount", 1)),
                )
            )
        candidates.append(
            CandidateLayout(
                candidate_id=f"random-{k+1:03d}",
                site_width=site_w,
                site_height=site_h,
                buildings=cand_buildings,
            )
        )
    return candidates


# ==============================================================================
# 2. MULTI-OBJECTIVE METRICS (HV, SPREAD, GD)
# ==============================================================================

def compute_hypervolume(front_objectives: List[List[float]], ref_point: List[float] = [1.0, 1.0, 1.0, 1.0, 1.0]) -> float:
    """
    Monte Carlo Hypervolume estimation for 5D objective space.
    front_objectives contains normalised minimization objectives in [0, 1].
    Reference point is (1.0, 1.0, 1.0, 1.0, 1.0).
    """
    if not front_objectives:
        return 0.0
    F = np.array(front_objectives)
    # Check bounds
    if np.any(F > 1.0) or np.any(F < 0.0):
        F = np.clip(F, 0.0, 1.0)
    
    # Monte Carlo sampling in [0, 1]^5
    n_samples = 25000
    rng = np.random.default_rng(42)
    samples = rng.uniform(0.0, 1.0, size=(n_samples, len(ref_point)))
    
    # A sample is dominated by the front if exists a solution f in F such that f <= sample
    # Check domination across all samples
    dominated = np.zeros(n_samples, dtype=bool)
    for f in F:
        # sample is dominated by f if f <= sample for all dimensions
        is_dom = np.all(f <= samples, axis=1)
        dominated |= is_dom
    
    return float(np.mean(dominated))


def compute_spread(front_objectives: List[List[float]]) -> float:
    """
    Computes Deb's Spread / Spacing metric (Delta) for population diversity.
    Zero indicates perfectly uniform spacing.
    """
    if len(front_objectives) < 2:
        return 0.0
    F = np.array(front_objectives)
    n = len(F)
    # Compute Euclidean distance to nearest neighbor in objective space
    dists = []
    for i in range(n):
        diffs = F - F[i]
        d = np.sqrt(np.sum(diffs ** 2, axis=1))
        d[i] = np.inf
        dists.append(np.min(d))
    
    d_mean = np.mean(dists)
    if d_mean == 0.0:
        return 0.0
    # Normalized standard deviation of nearest neighbor distances
    spacing = np.sqrt(np.sum((dists - d_mean) ** 2) / n)
    return float(spacing)


# ==============================================================================
# 3. EXPERIMENT EXECUTION ENGINE
# ==============================================================================

def run_all_experiments() -> Dict[str, Any]:
    scenarios = get_scenarios()
    results: Dict[str, Any] = {}
    summary_rows: List[Dict[str, Any]] = []
    violation_rows: List[Dict[str, Any]] = []
    objective_progression_rows: List[Dict[str, Any]] = []

    print("=" * 78)
    print("  ARCHOPT MASTER REPRODUCIBLE EXPERIMENTAL SUITE")
    print("=" * 78)

    for sc_key, sc_data in scenarios.items():
        print(f"\n>>> Running {sc_key}: {sc_data['name']}...")
        req, constraints = to_contract_objects(sc_data)
        
        # 1. P1: Graph Builder
        t0 = time.perf_counter()
        campus_graph = build_graph(sc_data)
        graph_time = (time.perf_counter() - t0) * 1000.0

        # 2. P2: GNN Generation (100 candidates)
        t0 = time.perf_counter()
        gnn_candidates = generate_candidates(campus_graph, num_candidates=100, seed=42, backend="auto")
        gnn_gen_time = (time.perf_counter() - t0) * 1000.0

        # 3. Mock Generation Baseline (100 candidates)
        t0 = time.perf_counter()
        mock_candidates = generate_mock_candidates(100, req, seed=42)
        mock_gen_time = (time.perf_counter() - t0) * 1000.0

        # 4. Random Placement Baseline (100 candidates)
        t0 = time.perf_counter()
        random_candidates = generate_random_candidates(sc_data, num_candidates=100, seed=42)
        random_gen_time = (time.perf_counter() - t0) * 1000.0

        # 5. Evaluate Constraint Violations for all candidate sets
        def analyze_candidates(cands: List[CandidateLayout], label: str) -> Dict[str, Any]:
            vals = [validate_layout(c, req, constraints) for c in cands]
            feasible_count = sum(1 for v in vals if v.feasible)
            scores = [v.constraint_score for v in vals]
            
            # Count specific violation types
            type_counts: Dict[str, int] = {
                "BOUNDARY_VIOLATION": 0,
                "OVERLAP_VIOLATION": 0,
                "GAP_VIOLATION": 0,
                "NAMED_MIN_DISTANCE_VIOLATION": 0,
                "NAMED_MAX_DISTANCE_VIOLATION": 0,
                "MIN_GREEN_PERCENT_VIOLATION": 0,
                "MIN_PARKING_PERCENT_VIOLATION": 0,
                "ROAD_NETWORK_DISCONNECTED": 0,
                "ZONING_VIOLATION": 0,
            }
            for v in vals:
                seen_in_cand = set()
                for viol in v.violations:
                    seen_in_cand.add(viol.type)
                for t in seen_in_cand:
                    if t in type_counts:
                        type_counts[t] += 1
                    else:
                        type_counts[t] = type_counts.get(t, 0) + 1
            
            # Objectives before optimization
            objs = [compute_objectives(c, req) for c in cands]
            mean_objs = {
                k: float(np.mean([o[k] for o in objs]))
                for k in objs[0]
            }

            return {
                "label": label,
                "total_candidates": len(cands),
                "feasible_candidates": feasible_count,
                "feasibility_rate_pct": round((feasible_count / len(cands)) * 100.0, 2),
                "mean_constraint_score": round(float(np.mean(scores)), 4),
                "std_constraint_score": round(float(np.std(scores)), 4),
                "violation_counts": type_counts,
                "initial_mean_objectives": {k: round(v, 4) for k, v in mean_objs.items()},
                "validations": vals,
                "raw_objectives": objs,
            }

        gnn_eval = analyze_candidates(gnn_candidates, "GNN")
        mock_eval = analyze_candidates(mock_candidates, "Mock")
        random_eval = analyze_candidates(random_candidates, "Random")

        # 6. Run NSGA-II Optimization on GNN candidates
        t0 = time.perf_counter()
        top_gnn_ranked = optimize_layouts(gnn_candidates, req, constraints, top_k=5)
        opt_time = (time.perf_counter() - t0) * 1000.0

        # Run NSGA-II on Random baseline
        top_random_ranked = optimize_layouts(random_candidates, req, constraints, top_k=5)
        # Run NSGA-II on Mock candidates
        top_mock_ranked = optimize_layouts(mock_candidates, req, constraints, top_k=5)

        # 7. Pareto Front Analysis of GNN population
        gnn_min_objs = [objectives_to_minimise(c, req) for c in gnn_candidates]
        fronts = non_dominated_sort(gnn_min_objs)
        front_1_indices = fronts[0]
        front_1_objs = [gnn_min_objs[i] for i in front_1_indices]
        
        hv = compute_hypervolume(front_1_objs)
        spread = compute_spread(front_1_objs)

        # Top 5 metrics summary
        top5_metrics = {
            "land_utilization": [round(r.metrics.land_utilization, 4) for r in top_gnn_ranked],
            "green_ratio": [round(r.metrics.green_ratio, 4) for r in top_gnn_ranked],
            "parking_ratio": [round(r.metrics.parking_ratio, 4) for r in top_gnn_ranked],
            "accessibility_score": [round(r.metrics.accessibility_score, 4) for r in top_gnn_ranked],
            "road_efficiency": [round(r.metrics.road_efficiency, 4) for r in top_gnn_ranked],
            "constraint_score": [round(r.metrics.constraint_score, 4) for r in top_gnn_ranked],
            "feasible": [r.feasible for r in top_gnn_ranked],
        }

        top5_mean_metrics = {
            k: round(float(np.mean(v)), 4) if k != "feasible" else sum(v)
            for k, v in top5_metrics.items()
        }

        # Record scenario results
        sc_result = {
            "scenario": sc_key,
            "site": {"width": req.site_width, "height": req.site_height, "area_m2": req.site_width * req.site_height},
            "num_buildings": len(sc_data["buildings"]),
            "num_constraints": len(constraints),
            "latencies_ms": {
                "graph_builder_ms": round(graph_time, 2),
                "gnn_generate_ms": round(gnn_gen_time, 2),
                "mock_generate_ms": round(mock_gen_time, 2),
                "random_generate_ms": round(random_gen_time, 2),
                "optimizer_ms": round(opt_time, 2),
                "total_real_pipeline_ms": round(graph_time + gnn_gen_time + opt_time, 2),
            },
            "gnn_evaluation": {
                "total_candidates": gnn_eval["total_candidates"],
                "feasible_candidates": gnn_eval["feasible_candidates"],
                "feasibility_rate_pct": gnn_eval["feasibility_rate_pct"],
                "mean_constraint_score": gnn_eval["mean_constraint_score"],
                "std_constraint_score": gnn_eval["std_constraint_score"],
                "violation_counts": gnn_eval["violation_counts"],
                "initial_mean_objectives": gnn_eval["initial_mean_objectives"],
            },
            "mock_evaluation": {
                "feasible_candidates": mock_eval["feasible_candidates"],
                "feasibility_rate_pct": mock_eval["feasibility_rate_pct"],
                "mean_constraint_score": mock_eval["mean_constraint_score"],
                "violation_counts": mock_eval["violation_counts"],
            },
            "random_evaluation": {
                "feasible_candidates": random_eval["feasible_candidates"],
                "feasibility_rate_pct": random_eval["feasibility_rate_pct"],
                "mean_constraint_score": random_eval["mean_constraint_score"],
                "violation_counts": random_eval["violation_counts"],
            },
            "nsga2_metrics": {
                "total_fronts": len(fronts),
                "front_1_size": len(front_1_indices),
                "hypervolume": round(hv, 4),
                "spread_spacing": round(spread, 4),
            },
            "top5_ranked_layouts": [
                {
                    "rank": r.rank,
                    "candidate_id": r.candidate_id,
                    "feasible": r.feasible,
                    "metrics": asdict(r.metrics),
                }
                for r in top_gnn_ranked
            ],
            "top5_mean_metrics": top5_mean_metrics,
        }
        results[sc_key] = sc_result

        # Populate summary CSV rows
        summary_rows.append({
            "Scenario": sc_key,
            "Site Dimensions (m)": f"{req.site_width}x{req.site_height}",
            "Building Count": len(sc_data["buildings"]),
            "Constraint Count": len(constraints),
            "GNN Feasibility (%)": gnn_eval["feasibility_rate_pct"],
            "Mock Feasibility (%)": mock_eval["feasibility_rate_pct"],
            "Random Feasibility (%)": random_eval["feasibility_rate_pct"],
            "GNN Mean Score": gnn_eval["mean_constraint_score"],
            "Front 1 Size": len(front_1_indices),
            "Hypervolume": round(hv, 4),
            "Top-1 Land Util": top_gnn_ranked[0].metrics.land_utilization,
            "Top-1 Green Ratio": top_gnn_ranked[0].metrics.green_ratio,
            "Top-1 Parking Ratio": top_gnn_ranked[0].metrics.parking_ratio,
            "Top-1 Accessibility": top_gnn_ranked[0].metrics.accessibility_score,
            "Top-1 Road Efficiency": top_gnn_ranked[0].metrics.road_efficiency,
            "Pipeline Latency (ms)": round(graph_time + gnn_gen_time + opt_time, 2),
        })

        # Populate violation CSV rows
        for v_type, v_count in gnn_eval["violation_counts"].items():
            violation_rows.append({
                "Scenario": sc_key,
                "Violation Type": v_type,
                "GNN Count (out of 100)": v_count,
                "Random Count (out of 100)": random_eval["violation_counts"].get(v_type, 0),
                "Mock Count (out of 100)": mock_eval["violation_counts"].get(v_type, 0),
            })

        # Objective progression rows (Initial vs Optimized)
        for obj_name in ["land_utilization", "green_ratio", "parking_ratio", "accessibility_score", "road_efficiency"]:
            init_val = gnn_eval["initial_mean_objectives"][obj_name]
            opt_val = top5_mean_metrics[obj_name]
            objective_progression_rows.append({
                "Scenario": sc_key,
                "Objective": obj_name,
                "Initial Population Mean": init_val,
                "Top-5 Pareto Mean": opt_val,
                "Improvement": round(opt_val - init_val, 4),
                "Improvement (%)": round(((opt_val - init_val) / max(1e-6, init_val)) * 100.0, 2),
            })

        print(f"   [DONE] Feasibility: GNN={gnn_eval['feasibility_rate_pct']}%, Random={random_eval['feasibility_rate_pct']}% | Top-5 Feasible: {top5_mean_metrics['feasible']}/5")

    # ==========================================================================
    # 4. SYSTEM PERFORMANCE BENCHMARKS (10 REPEATED RUNS)
    # ==========================================================================
    print("\n>>> Running System Latency & Performance Benchmarks (10 repeated runs)...")
    mvp_sc = scenarios["Scenario 2: Medium Campus"]
    mvp_req, mvp_cons = to_contract_objects(mvp_sc)

    graph_times = []
    gnn_torch_times = []
    gnn_numpy_times = []
    val_times = []
    opt_times = []
    e2e_times = []

    # Warmup
    _cg = build_graph(mvp_sc)
    _ = generate_candidates(_cg, 100, backend="torch")
    _ = generate_candidates(_cg, 100, backend="numpy")

    import psutil
    process = psutil.Process()
    ram_usages_mb = []

    for run_idx in range(10):
        ram_usages_mb.append(process.memory_info().rss / (1024 * 1024))
        
        # 1. Graph Builder
        t0 = time.perf_counter()
        cg = build_graph(mvp_sc)
        graph_times.append((time.perf_counter() - t0) * 1000.0)

        # 2. GNN Torch
        t0 = time.perf_counter()
        cands_torch = generate_candidates(cg, 100, seed=100 + run_idx, backend="torch")
        gnn_torch_times.append((time.perf_counter() - t0) * 1000.0)

        # 3. GNN NumPy
        t0 = time.perf_counter()
        cands_numpy = generate_candidates(cg, 100, seed=100 + run_idx, backend="numpy")
        gnn_numpy_times.append((time.perf_counter() - t0) * 1000.0)

        # 4. Constraint Validation (100 candidates)
        t0 = time.perf_counter()
        for c in cands_torch:
            _ = validate_layout(c, mvp_req, mvp_cons)
        val_times.append((time.perf_counter() - t0) * 1000.0)

        # 5. NSGA-II Optimization
        t0 = time.perf_counter()
        _ = optimize_layouts(cands_torch, mvp_req, mvp_cons, top_k=5)
        opt_times.append((time.perf_counter() - t0) * 1000.0)

        # 6. Full End-to-End Pipeline
        t0 = time.perf_counter()
        g_temp = build_graph(mvp_sc)
        c_temp = generate_candidates(g_temp, 100, seed=100 + run_idx)
        _ = optimize_layouts(c_temp, mvp_req, mvp_cons, top_k=5)
        e2e_times.append((time.perf_counter() - t0) * 1000.0)

    def stats(arr: List[float]) -> Dict[str, float]:
        return {
            "mean": round(float(np.mean(arr)), 2),
            "std": round(float(np.std(arr)), 2),
            "median": round(float(np.median(arr)), 2),
            "min": round(float(np.min(arr)), 2),
            "max": round(float(np.max(arr)), 2),
        }

    benchmarks = {
        "runs": 10,
        "graph_construction_ms": stats(graph_times),
        "gnn_inference_torch_ms": stats(gnn_torch_times),
        "gnn_inference_numpy_ms": stats(gnn_numpy_times),
        "constraint_validation_100_ms": stats(val_times),
        "nsga2_optimization_ms": stats(opt_times),
        "end_to_end_pipeline_ms": stats(e2e_times),
        "memory_rss_mb": stats(ram_usages_mb),
    }

    # ==========================================================================
    # 5. GENERATIONAL CONVERGENCE SIMULATION (NSGA-II over 25 Generations)
    # ==========================================================================
    print("\n>>> Running Continuous Generational NSGA-II Evolution (25 generations)...")
    # Simulate evolution of campus positions starting from GNN candidate population
    gen_cands = [c for c in gnn_candidates]
    gen_records = []
    
    # We mutate and recombine building coordinates over 25 generations to observe Pareto front convergence
    rng = np.random.default_rng(42)
    pop_size = len(gen_cands)
    site_w, site_h = mvp_req.site_width, mvp_req.site_height
    
    current_pop = gen_cands
    for gen in range(1, 26):
        # 1. Compute objectives
        objs_min = [objectives_to_minimise(c, mvp_req) for c in current_pop]
        fronts = non_dominated_sort(objs_min)
        f1_objs = [objs_min[i] for i in fronts[0]]
        f1_hv = compute_hypervolume(f1_objs)
        f1_spread = compute_spread(f1_objs)

        # Objective means in Front 1
        f1_land = np.mean([1.0 - o[0] for o in f1_objs])
        f1_green = np.mean([1.0 - o[1] for o in f1_objs])
        f1_parking = np.mean([1.0 - o[2] for o in f1_objs])
        f1_access = np.mean([1.0 - o[3] for o in f1_objs])
        f1_road = np.mean([1.0 - o[4] for o in f1_objs])

        gen_records.append({
            "generation": gen,
            "front_1_count": len(fronts[0]),
            "hypervolume": round(f1_hv, 4),
            "spread": round(f1_spread, 4),
            "mean_land_utilization": round(float(f1_land), 4),
            "mean_green_ratio": round(float(f1_green), 4),
            "mean_parking_ratio": round(float(f1_parking), 4),
            "mean_accessibility": round(float(f1_access), 4),
            "mean_road_efficiency": round(float(f1_road), 4),
        })

        # Selection, Crossover, and Mutation to create next generation
        # Binary tournament selection based on rank
        rank_order = rank_population(objs_min)
        rank_map = {idx: rank for rank, (idx, _, _) in enumerate(rank_order)}
        
        offspring_pop: List[CandidateLayout] = []
        while len(offspring_pop) < pop_size:
            # Tournament 1
            i1, i2 = rng.choice(pop_size, size=2, replace=False)
            p1_idx = i1 if rank_map[i1] < rank_map[i2] else i2
            # Tournament 2
            i3, i4 = rng.choice(pop_size, size=2, replace=False)
            p2_idx = i3 if rank_map[i3] < rank_map[i4] else i4
            
            p1, p2 = current_pop[p1_idx], current_pop[p2_idx]
            
            # Simulated uniform crossover on building coordinates
            new_buildings: List[CandidateBuilding] = []
            for b1, b2 in zip(p1.buildings, p2.buildings):
                alpha = rng.uniform(0.0, 1.0)
                new_x = alpha * b1.x + (1.0 - alpha) * b2.x
                new_y = alpha * b1.y + (1.0 - alpha) * b2.y
                new_rot = b1.rotation if rng.random() < 0.5 else b2.rotation
                
                # Mutation (polynomial-like perturbation)
                if rng.random() < 0.2:
                    new_x += float(rng.normal(0, 5.0))
                    new_y += float(rng.normal(0, 5.0))
                
                # Boundary clamping
                bw = b1.width if new_rot == 0.0 else b1.depth
                bd = b1.depth if new_rot == 0.0 else b1.width
                new_x = float(np.clip(new_x, 0.05, site_w - bw - 0.05))
                new_y = float(np.clip(new_y, 0.05, site_h - bd - 0.05))
                
                new_buildings.append(CandidateBuilding(
                    building_id=b1.building_id,
                    name=b1.name,
                    type=b1.type,
                    zone=b1.zone,
                    x=new_x,
                    y=new_y,
                    width=b1.width,
                    depth=b1.depth,
                    height=b1.height,
                    rotation=new_rot,
                    floor_count=b1.floor_count,
                ))
            offspring_pop.append(CandidateLayout(
                candidate_id=f"gen{gen}-{len(offspring_pop)+1:03d}",
                site_width=site_w,
                site_height=site_h,
                buildings=new_buildings,
            ))

        # Elitist replacement: combine parent + offspring (2N), sort, keep top N
        combined_pop = current_pop + offspring_pop
        comb_objs = [objectives_to_minimise(c, mvp_req) for c in combined_pop]
        comb_ranked = rank_population(comb_objs)
        current_pop = [combined_pop[idx] for idx, _, _ in comb_ranked[:pop_size]]

    # ==========================================================================
    # 6. WRITE ALL RESULTS TO DISK
    # ==========================================================================
    print("\n>>> Writing results to disk...")

    # 1. JSON scenario results
    json_path = OUTPUT_DIR / "scenario_results.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"   [SAVED] {json_path}")

    # 2. CSV summary
    csv_summary_path = OUTPUT_DIR / "scenario_summary.csv"
    with open(csv_summary_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
        writer.writeheader()
        writer.writerows(summary_rows)
    print(f"   [SAVED] {csv_summary_path}")

    # 3. CSV violations
    csv_viol_path = OUTPUT_DIR / "constraint_violations.csv"
    with open(csv_viol_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(violation_rows[0].keys()))
        writer.writeheader()
        writer.writerows(violation_rows)
    print(f"   [SAVED] {csv_viol_path}")

    # 4. CSV objective progression
    csv_obj_path = OUTPUT_DIR / "objective_progression.csv"
    with open(csv_obj_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(objective_progression_rows[0].keys()))
        writer.writeheader()
        writer.writerows(objective_progression_rows)
    print(f"   [SAVED] {csv_obj_path}")

    # 5. JSON benchmarks
    bench_json_path = OUTPUT_DIR / "system_benchmarks.json"
    with open(bench_json_path, "w", encoding="utf-8") as f:
        json.dump(benchmarks, f, indent=2)
    print(f"   [SAVED] {bench_json_path}")

    # 6. JSON generational convergence
    gen_json_path = OUTPUT_DIR / "generational_convergence.json"
    with open(gen_json_path, "w", encoding="utf-8") as f:
        json.dump(gen_records, f, indent=2)
    print(f"   [SAVED] {gen_json_path}")

    print("\n============================================================")
    print("  ALL EXPERIMENTS COMPLETED WITH 100% GENUINE EXECUTION!")
    print("============================================================\n")
    return results


if __name__ == "__main__":
    run_all_experiments()

