# AI Campus Planner

An AI-powered campus layout planning system that uses Graph Neural Networks, multi-objective optimization, and procedural 3D generation to automatically propose feasible campus designs.

## Team Ownership

| Module | Owner | Description |
|--------|-------|-------------|
| `ml/data/`, `ml/dataset/` | Person 1 | Campus schema, synthetic dataset, graph builder |
| `ml/models/`, `ml/training/`, `ml/inference/` | Person 2 | GNN encoder + layout decoder |
| `optimization/` | **Person 3** | Constraint engine + NSGA-II optimizer |
| `backend/` | Person 4 | FastAPI + PostgreSQL + orchestration |
| `frontend/` | Person 5 | React 2D campus planning UI |
| `blender/` | Person 6 | Procedural 3D campus generation |
| `contracts/` | Team (P4 coordinates) | Shared data contracts |

---

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+ (for frontend)
- Blender 3.6+ (for 3D generation, local install)
- PostgreSQL 15+

### Person 3 — Optimization Engine (Standalone)

```bash
# Install dependencies
cd e:\ArchOpt
pip install -r optimization/requirements.txt

# Run full demo (generates 100 mock candidates, ranks top 5, writes SVGs + HTML)
python -m optimization.optimizer

# Open the interactive comparison in your browser
start output\comparison.html

# Run all tests
pytest optimization/tests/ -v
```

---

## Architecture

```
React (P5)
    ↕ REST / JSON
FastAPI Backend (P4)
    ├── PostgreSQL
    └── Python AI Engine
            ├── Graph Builder (P1) → CampusGraph
            ├── GNN Generator (P2) → CandidateLayout[]
            └── Optimizer (P3)    → RankedLayout[]
                                          ↓
                              Blueprint JSON → Blender (P6) → 3D Campus
```

## Core Principle

> **AI decides WHERE** → **Optimization decides WHICH** → **Frontend lets the manager choose** → **Blender decides HOW**

---

## Person 3 Module — `optimization/`

### What it does

Takes 100 candidate layouts from the GNN (P2), validates each against hard and soft constraints, computes five objective metrics, runs NSGA-II multi-objective optimization, and returns the top 5 Pareto-ranked feasible layouts to the backend (P4).

### Pipeline

```
CandidateLayout[] (from P2)
    ↓
Constraint Engine  ←  CampusRequirements + Constraint[]
    ↓
Objective Functions
    ↓
NSGA-II (pure Python + optional pymoo)
    ↓
Pareto Ranking
    ↓
Top-5 RankedLayout[]  →  P4 Backend
```

### Public API

```python
from optimization import validate_layout, optimize_layouts

# Validate a single layout
result = validate_layout(layout, requirements, constraints)
# → ValidationResult(feasible=True, violations=[], constraint_score=0.875)

# Run full optimization pipeline
ranked = optimize_layouts(candidates, requirements, constraints, top_k=5)
# → [RankedLayout(rank=1, feasible=True, metrics=...), ...]
```

### Constraint Checkers

| File | Constraint | Severity |
|------|-----------|---------|
| `boundary.py` | Building within site boundary | Hard |
| `overlap.py` | No overlaps, minimum gap between buildings | Hard |
| `distance.py` | Named MIN/MAX distance constraints | Hard/Soft |
| `green.py` | Green-space coverage ≥ minGreenPercent | Hard |
| `parking.py` | Parking coverage ≥ minParkingPercent | Hard |
| `roads.py` | Every building reachable from an entrance | Hard |
| `zoning.py` | Same-zone buildings spatially clustered | Soft |

### Objective Functions

1. **Land Utilization** — maximize built footprint / site area
2. **Green Ratio** — maximize green coverage
3. **Parking Ratio** — maximize parking coverage
4. **Accessibility Score** — minimize mean distance to entrances
5. **Road Efficiency** — minimize spanning tree road length

### Output Files (after running demo)

```
output/
├── ranked_layouts.json    ← Top-5 as JSON (for P4 integration)
├── layout_1.svg           ← Rank 1 annotated SVG
├── layout_2.svg
├── layout_3.svg
├── layout_4.svg
├── layout_5.svg
└── comparison.html        ← Interactive browser comparison (open this!)
```

---

## Shared Contracts

All inter-module data shapes are defined in `contracts/`:

| Contract | Producer | Consumer |
|---------|---------|---------|
| `CampusRequirements` | P4 | P1, P3 |
| `Building` | P4 | P1, P3 |
| `CampusGraph` | P1 | P2 |
| `CandidateLayout` | P2 | P3 |
| `RankedLayout` | P3 | P4 |
| `Blueprint` | P4 | P6 |

**Do not modify `contracts/layout.py` or `contracts/layout.ts` without team approval.**

---

## Coordinate System

- **Origin**: bottom-left of campus plot
- **X**: east / west (metres)
- **Y**: north / south (metres)
- **Rotation**: degrees, counter-clockwise from east
- Blender converts directly from this system.

---

## Git Strategy

| Branch | Purpose |
|--------|---------|
| `main` | Stable releases only |
| `integration` | Pre-merge integration testing |
| `feature/p1-data` | Person 1's work |
| `feature/p2-gnn` | Person 2's work |
| `feature/p3-optimization` | Person 3's work |
| `feature/p4-backend` | Person 4's work |
| `feature/p5-frontend` | Person 5's work |
| `feature/p6-blender` | Person 6's work |

Commit convention: `feat:`, `fix:`, `test:`, `refactor:`, `docs:`, `chore:`

---

## MVP Campus

300 × 300 m site with:
- 2 Academic Blocks (60 × 40 m)
- 3 Hostels (50 × 30 m)
- 1 Library (30 × 25 m)
- 1 Administration (40 × 30 m)
- 1 Sports Complex (80 × 60 m)
- 1 Parking Area (40 × 30 m)
- 1 Main Entrance + 1 Side Entrance

---

## Docker (P4 sets up)

```bash
docker-compose up
```

Starts: PostgreSQL + FastAPI backend. Frontend and Blender run locally.