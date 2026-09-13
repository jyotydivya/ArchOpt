# ArchOpt — Team Integration Architecture & Execution Contract Guide
**Document Version**: 1.0.0 — Final Implementation Reference  
**Audience**: All 6 Project Engineers (Persons 1, 2, 3, 4, 5, and 6)  
**Authoritative Contracts**:
- `Technical Architecture & 6-Person Execution Contract`
- `implementation_plan.md`
- Completed Backend Implementation (Phases 1–12)

---

# ARCHOPT — TEAM INTEGRATION & ONBOARDING GUIDE
## INDEX

This document contains 16 parts covering the complete ArchOpt development, integration, API, environment, and team handoff workflow.

* **PART 1 — Current System Status**: Covers the current state of ArchOpt, completed Phases 1–12, backend readiness, and remaining P1/P2/P3 dependencies.
* **PART 2 — Master API Contract**: Covers all 17 master REST APIs, authentication, ownership, request/response conventions, camelCase rules, errors, and data contracts.
* **PART 3 — End-to-End Data Flow**: Covers the complete flow from frontend $\rightarrow$ backend $\rightarrow$ P1 $\rightarrow$ P2 $\rightarrow$ P3 $\rightarrow$ backend $\rightarrow$ frontend $\rightarrow$ Blender.
* **PART 4 — Person 1 Guide**: Covers P1's responsibilities, graph-builder module, API/data inputs, CampusGraph output, Contract 5, and integration with P2.
* **PART 5 — Person 2 Guide**: Covers P2's responsibilities, GNN candidate generation, CampusGraph input, CandidateLayout[] output, Contract 6, and integration with P3.
* **PART 6 — Person 3 Guide**: Covers P3's responsibilities, NSGA-II optimization, candidate/requirements/constraint inputs, RankedLayout[] output, Contract 8, and integration with P4.
* **PART 7 — Person 4 Guide**: Covers backend ownership, orchestration, ML bridge, MOCK vs REAL pipeline modes, error handling, persistence, and P1/P2/P3 integration.
* **PART 8 — Person 5 Guide**: Covers frontend responsibilities, authentication, project workflow, requirements/buildings/constraints APIs, layout retrieval, comparison, and layout selection.
* **PART 9 — Person 6 Guide**: Covers Blender/3D responsibilities, Contract 9 blueprint consumption, building/road/green/parking/entrance data, and coordinate-system requirements.
* **PART 10 — Cross-Person Contract Table**: Covers every major producer $\rightarrow$ consumer boundary, including exact data exchanged, contract, function/API, and failure behavior.
* **PART 11 — Who Changes What**: Covers file ownership, integration boundaries, permitted modifications, and files/modules each person should avoid changing.
* **PART 12 — Implementation Order**: Covers the recommended development and integration sequence, dependencies between people, and which work can happen in parallel.
* **PART 13 — API Quick Reference**: Provides a compact API cheat sheet showing endpoint $\rightarrow$ purpose $\rightarrow$ input $\rightarrow$ output $\rightarrow$ consumer.
* **PART 14 — Do Not Break These Rules**: Contains the critical architecture, API, security, contract, integration, and collaboration rules that everyone must follow.
* **PART 15 — Final Integration Checklist**: Contains completion checklists for P1–P6 and the final end-to-end system verification.
* **PART 16 — Repository Cloning & Local Setup Guide**: Covers cloning, prerequisites, Python environment, dependencies, environment variables, PostgreSQL, Alembic migrations, backend startup, testing, person-specific setup, Git workflow, troubleshooting, integration checkpoints, and new-developer quickstart.

---

### DOCUMENT MAP & READING PATH

| Section | Target Focus | Contents |
|---|---|---|
| **Parts 1–3** | **SYSTEM & ARCHITECTURE** | Understand the existing system, 17 master APIs, and how data flows. |
| **Parts 4–9** | **PERSON-BY-PERSON IMPLEMENTATION** | Understand exactly what each person builds, consumes, and produces. |
| **Parts 10–12** | **INTEGRATION & OWNERSHIP** | Understand how everyone's work connects and who owns what. |
| **Parts 13–15** | **REFERENCE & VERIFICATION** | Quick API reference, non-negotiable rules, and completion checks. |
| **Part 16** | **CLONE & ENVIRONMENT SETUP** | Get a developer from a fresh clone to a working development environment. |

> [!TIP]
> **Intended Reading Order for a New Teammate**:  
> **`Part 16`** (Setup) $\rightarrow$ **`Part 1`** (Status) $\rightarrow$ **`Part 2`** (APIs) $\rightarrow$ **`Part 3`** (Data Flow) $\rightarrow$ **`[Your Assigned Part 4–9]`** $\rightarrow$ **`Part 10`** (Contracts) $\rightarrow$ **`Part 11`** (Ownership) $\rightarrow$ **`Part 12`** (Order) $\rightarrow$ **`Part 13`** (Cheat Sheet) $\rightarrow$ **`Part 14`** (Rules) $\rightarrow$ **`Part 15`** (Checklist)

* **Part 2 (Master API Contract)** is the central API reference.
* **Parts 4–9** define individual responsibilities.
* **Part 10** defines integration boundaries.
* **Part 11** defines file ownership.
* **Part 14** contains the rules that must not be violated.
* **Part 16** gets each developer's local environment ready before implementation.

---

# PART 1 — CURRENT SYSTEM STATUS

### Verified Repository & System State
The central application backend (Person 4) has completed and verified **Phases 1 through 12**:
1. **17 Master REST APIs**: Fully implemented, validated, and registered under `/api`.
2. **Development Health Check**: `GET /` operational (`{"status": "ok", "app": "AI Campus Planner Backend"}`).
3. **Database Layer**: PostgreSQL contains exactly the **8 contract tables** mapped via SQLAlchemy and managed by Alembic at revision `001_initial_schema (head)`.
4. **Phase 10 ML Bridge Boundary**: [`backend/services/ml_bridge.py`](backend/services/ml_bridge.py) defines the explicit integration boundary for upstream ML/optimization modules.
5. **Phase 11 End-to-End Contract Verification**: [`backend/tests/test_contract_verification.py`](backend/tests/test_contract_verification.py) verifies the entire 17-endpoint lifecycle, data contracts 1–9, schema fidelity, and cross-user isolation.
6. **Phase 12 Deliverables**: Complete OpenAPI specification at [`docs/openapi.json`](docs/openapi.json), comprehensive audit report at [`docs/person_4_audit_report.md`](docs/person_4_audit_report.md), and documentation in `README.md`.
7. **Test Suite Baseline**: **70 tests passing, 0 failures, 0 errors** across all 9 test suites.

### Critical Architecture Note: Backend Completion vs. ML Pipeline
> [!IMPORTANT]
> **Backend completion does NOT mean the actual ML algorithms/models are complete.**
> Person 4 has built the orchestration framework, the database, the authentication layer, the REST endpoints, and the integration bridge. 
> Upstream Python files for **Person 1 (`ml/dataset/graph_builder.py`)**, **Person 2 (`ml/inference/generate.py`)**, and **Person 3 (`optimization/optimizer.py`)** are currently external deliverables that must be authored by Persons 1, 2, and 3.
> Person 4 has provided an explicitly configured **`MOCK`** mode so that Person 5 (Frontend) and Person 6 (Blender) can develop immediately without waiting for model training. When **`REAL`** mode is active, Person 4's backend strictly dispatches to P1 $\rightarrow$ P2 $\rightarrow$ P3 and will never invent or simulate their internal logic.

---

# PART 2 — MASTER API CONTRACT
## MASTER API RULES — DO NOT BREAK THESE

### Fundamental Rules
1. **Zero Endpoint Inventions**: Exactly these 17 endpoints exist. No team member may introduce new endpoints or alternate URLs.
2. **Pure camelCase JSON**: All JSON keys across request bodies and response payloads use `camelCase` (e.g., `projectId`, `siteWidth`, `floorCount`, `sourceId`, `candidateCount`, `topK`, `layoutId`, `buildingId`). Never rename these to `snake_case` in API payloads.
3. **Authentication Mechanism**:
   - Public Endpoints: Only `POST /api/auth/register` and `POST /api/auth/login`.
   - Protected Endpoints (15 of 17): Require HTTP header `Authorization: Bearer <accessToken>`.
4. **Strict Ownership Scoping**:
   - Every project, requirement, building, constraint, layout, and blueprint belongs to the authenticated user.
   - Cross-user data access is strictly forbidden and returns HTTP `403 FORBIDDEN`.
   - Requesting a missing entity returns HTTP `404 NOT_FOUND`.
5. **Contract/Implementation Discrepancies Noted & Preserved**:
   - **CONTRACT / IMPLEMENTATION DISCREPANCY — `road_data` & `total_area`**:
     The Database Contract (Section 5) defines `road_data JSONB` and `total_area FLOAT` on `campus_requirements`. However, the API Contract (Section 3.7 & 3.8) does NOT accept or return these fields. The backend preserves `road_data` and `total_area` internally in PostgreSQL (defaulting to `[]` and `site_width * site_height`), but strictly omits them from public API schemas to maintain 100% contract compliance.
   - **CONTRACT / IMPLEMENTATION DISCREPANCY — Login User Summary**:
     Section 3.2 specifies that login returns `{"user": {"id": 1, "name": "...", "role": "PROJECT_MANAGER"}}` (omitting `email`, which is returned in register). The backend adheres strictly to Section 3.2.

---

### Detailed Specification of All 17 Master Endpoints

#### 1. `POST /api/auth/register`
- **Purpose**: Register a new user account with default role `PROJECT_MANAGER`.
- **Consumer**: Person 5 (Frontend)
- **Backend Owner**: Person 4
- **Modifiable by Others**: NO
- **Authentication**: None (Public)
- **Request Body**:
  ```json
  {
    "name": "Student",
    "email": "student@example.com",
    "password": "password123"
  }
  ```
- **Expected Response (`201 Created`)**:
  ```json
  {
    "id": 1,
    "name": "Student",
    "email": "student@example.com",
    "role": "PROJECT_MANAGER"
  }
  ```
- **Common Errors**: `400 VALIDATION_ERROR` (malformed payload), `409 EMAIL_ALREADY_EXISTS` (duplicate email).
- **Data Contract**: Section 3.1 Auth Specification.

#### 2. `POST /api/auth/login`
- **Purpose**: Authenticate user credentials and issue a signed JWT Bearer access token.
- **Consumer**: Person 5 (Frontend)
- **Backend Owner**: Person 4
- **Modifiable by Others**: NO
- **Authentication**: None (Public)
- **Request Body**:
  ```json
  {
    "email": "student@example.com",
    "password": "password123"
  }
  ```
- **Expected Response (`200 OK`)**:
  ```json
  {
    "accessToken": "eyJhbGci...",
    "tokenType": "Bearer",
    "user": {
      "id": 1,
      "name": "Student",
      "role": "PROJECT_MANAGER"
    }
  }
  ```
- **Common Errors**: `400 VALIDATION_ERROR`, `401 INVALID_CREDENTIALS`.
- **Data Contract**: Section 3.2 Auth Specification.

#### 3. `POST /api/projects`
- **Purpose**: Create a new campus planning project in `DRAFT` status.
- **Consumer**: Person 5 (Frontend)
- **Backend Owner**: Person 4
- **Modifiable by Others**: NO
- **Authentication**: `Bearer <token>`
- **Request Body**:
  ```json
  {
    "name": "VIT Campus Expansion",
    "description": "Campus planning case study"
  }
  ```
- **Expected Response (`201 Created`)**:
  ```json
  {
    "id": 1,
    "name": "VIT Campus Expansion",
    "description": "Campus planning case study",
    "status": "DRAFT"
  }
  ```
- **Common Errors**: `400 VALIDATION_ERROR`, `401 UNAUTHORIZED`.
- **Data Contract**: Section 3.3 Project Specification.

#### 4. `GET /api/projects/{projectId}`
- **Purpose**: Retrieve project details by ID.
- **Consumer**: Person 5 (Frontend)
- **Backend Owner**: Person 4
- **Modifiable by Others**: NO
- **Authentication**: `Bearer <token>`
- **Request Body**: None (Path param `projectId: int`)
- **Expected Response (`200 OK`)**:
  ```json
  {
    "id": 1,
    "name": "VIT Campus Expansion",
    "description": "Campus planning case study",
    "status": "DRAFT"
  }
  ```
- **Common Errors**: `401 UNAUTHORIZED`, `403 FORBIDDEN` (not project owner), `404 PROJECT_NOT_FOUND`.
- **Data Contract**: Section 3.4 Project Specification.

#### 5. `PUT /api/projects/{projectId}`
- **Purpose**: Update project name and description.
- **Consumer**: Person 5 (Frontend)
- **Backend Owner**: Person 4
- **Modifiable by Others**: NO
- **Authentication**: `Bearer <token>`
- **Request Body**:
  ```json
  {
    "name": "Updated Campus Expansion",
    "description": "Updated description"
  }
  ```
- **Expected Response (`200 OK`)**:
  ```json
  {
    "id": 1,
    "name": "Updated Campus Expansion",
    "description": "Updated description",
    "status": "DRAFT"
  }
  ```
- **Common Errors**: `400 VALIDATION_ERROR`, `401 UNAUTHORIZED`, `403 FORBIDDEN`, `404 PROJECT_NOT_FOUND`.
- **Data Contract**: Section 3.5 Project Specification.

#### 6. `DELETE /api/projects/{projectId}`
- **Purpose**: Delete project and cascade-delete all associated requirements, buildings, constraints, and layout runs.
- **Consumer**: Person 5 (Frontend)
- **Backend Owner**: Person 4
- **Modifiable by Others**: NO
- **Authentication**: `Bearer <token>`
- **Request Body**: None
- **Expected Response (`204 No Content`)**: Empty response body.
- **Common Errors**: `401 UNAUTHORIZED`, `403 FORBIDDEN`, `404 PROJECT_NOT_FOUND`.
- **Data Contract**: Section 3.6 Project Specification.

#### 7. `POST /api/projects/{projectId}/requirements`
- **Purpose**: Create or update campus site boundaries, environmental percentages, and entrance coordinates.
- **Consumer**: Person 5 (Frontend)
- **Backend Owner**: Person 4
- **Modifiable by Others**: NO
- **Authentication**: `Bearer <token>`
- **Request Body**:
  ```json
  {
    "siteWidth": 300,
    "siteHeight": 300,
    "minGreenPercent": 25,
    "minParkingPercent": 10,
    "minRoadWidth": 8,
    "minBuildingGap": 10,
    "entrances": [
      {
        "x": 150,
        "y": 0,
        "width": 10
      }
    ]
  }
  ```
- **Expected Response (`201 Created`)**:
  ```json
  {
    "id": 1,
    "projectId": 1,
    "siteWidth": 300,
    "siteHeight": 300,
    "minGreenPercent": 25,
    "minParkingPercent": 10,
    "minRoadWidth": 8,
    "minBuildingGap": 10,
    "entrances": [
      {
        "x": 150,
        "y": 0,
        "width": 10
      }
    ]
  }
  ```
- **Common Errors**: `400 VALIDATION_ERROR`, `401 UNAUTHORIZED`, `403 FORBIDDEN`, `404 PROJECT_NOT_FOUND`.
- **Data Contract**: Data Contract 2 (`CampusRequirements`) and Contract 3 (`Entrance`).

#### 8. `GET /api/projects/{projectId}/requirements`
- **Purpose**: Retrieve campus site constraints and requirements for the project.
- **Consumer**: Person 5 (Frontend), Person 1 (Dataset/Graph)
- **Backend Owner**: Person 4
- **Modifiable by Others**: NO
- **Authentication**: `Bearer <token>`
- **Request Body**: None
- **Expected Response (`200 OK`)**:
  ```json
  {
    "projectId": 1,
    "siteWidth": 300,
    "siteHeight": 300,
    "minGreenPercent": 25,
    "minParkingPercent": 10,
    "minRoadWidth": 8,
    "minBuildingGap": 10,
    "entrances": [
      {
        "x": 150,
        "y": 0,
        "width": 10
      }
    ]
  }
  ```
- **Common Errors**: `401 UNAUTHORIZED`, `403 FORBIDDEN`, `404 PROJECT_NOT_FOUND`.
- **Data Contract**: Data Contract 2 (`CampusRequirements`).

#### 9. `POST /api/projects/{projectId}/buildings`
- **Purpose**: Add a building specification to the project inventory.
- **Consumer**: Person 5 (Frontend)
- **Backend Owner**: Person 4
- **Modifiable by Others**: NO
- **Authentication**: `Bearer <token>`
- **Request Body**:
  ```json
  {
    "name": "Academic Block A",
    "type": "academic",
    "zone": "academic",
    "width": 60,
    "depth": 40,
    "height": 18,
    "floorCount": 4,
    "requiredCount": 1
  }
  ```
- **Expected Response (`201 Created`)**:
  ```json
  {
    "id": 1,
    "projectId": 1,
    "name": "Academic Block A",
    "type": "academic",
    "zone": "academic",
    "width": 60,
    "depth": 40,
    "height": 18,
    "floorCount": 4,
    "requiredCount": 1
  }
  ```
- **Common Errors**: `400 VALIDATION_ERROR`, `401 UNAUTHORIZED`, `403 FORBIDDEN`, `404 PROJECT_NOT_FOUND`.
- **Data Contract**: Data Contract 1 (`Building`).

#### 10. `GET /api/projects/{projectId}/buildings`
- **Purpose**: List all configured buildings for a project.
- **Consumer**: Person 5 (Frontend), Person 1 (Dataset/Graph)
- **Backend Owner**: Person 4
- **Modifiable by Others**: NO
- **Authentication**: `Bearer <token>`
- **Request Body**: None
- **Expected Response (`200 OK`)**:
  ```json
  {
    "buildings": [
      {
        "id": 1,
        "name": "Academic Block A",
        "type": "academic",
        "zone": "academic",
        "width": 60,
        "depth": 40,
        "height": 18,
        "floorCount": 4,
        "requiredCount": 1
      }
    ]
  }
  ```
- **Common Errors**: `401 UNAUTHORIZED`, `403 FORBIDDEN`, `404 PROJECT_NOT_FOUND`.
- **Data Contract**: Data Contract 1 (`Building`).

#### 11. `POST /api/projects/{projectId}/constraints`
- **Purpose**: Define spatial or relational rules between campus entities (e.g. `MIN_DISTANCE`, `MAX_DISTANCE`, `SAME_ZONE`).
- **Consumer**: Person 5 (Frontend)
- **Backend Owner**: Person 4
- **Modifiable by Others**: NO
- **Authentication**: `Bearer <token>`
- **Request Body**:
  ```json
  {
    "type": "MIN_DISTANCE",
    "sourceId": 1,
    "targetId": 5,
    "value": 100,
    "operator": ">=",
    "priority": "hard"
  }
  ```
- **Expected Response (`201 Created`)**:
  ```json
  {
    "id": 1,
    "type": "MIN_DISTANCE",
    "sourceId": 1,
    "targetId": 5,
    "value": 100,
    "operator": ">=",
    "priority": "hard"
  }
  ```
- **Common Errors**: `400 VALIDATION_ERROR`, `401 UNAUTHORIZED`, `403 FORBIDDEN`, `404 PROJECT_NOT_FOUND`.
- **Data Contract**: Data Contract 4 (`SpatialRelationship`).

#### 12. `GET /api/projects/{projectId}/constraints`
- **Purpose**: Retrieve all defined spatial constraints for a project.
- **Consumer**: Person 5 (Frontend), Person 1 (Dataset/Graph), Person 3 (Optimizer)
- **Backend Owner**: Person 4
- **Modifiable by Others**: NO
- **Authentication**: `Bearer <token>`
- **Request Body**: None
- **Expected Response (`200 OK`)**:
  ```json
  {
    "constraints": [
      {
        "id": 1,
        "type": "MIN_DISTANCE",
        "sourceId": 1,
        "targetId": 5,
        "value": 100,
        "operator": ">=",
        "priority": "hard"
      }
    ]
  }
  ```
- **Common Errors**: `401 UNAUTHORIZED`, `403 FORBIDDEN`, `404 PROJECT_NOT_FOUND`.
- **Data Contract**: Data Contract 4 (`SpatialRelationship`).

#### 13. `POST /api/projects/{projectId}/layout-runs`
- **Purpose**: Execute an optimization run to generate, optimize, rank, and persist candidate campus layouts.
- **Consumer**: Person 5 (Frontend)
- **Backend Owner**: Person 4 (interfaces with P1 $\rightarrow$ P2 $\rightarrow$ P3)
- **Modifiable by Others**: NO
- **Authentication**: `Bearer <token>`
- **Request Body**:
  ```json
  {
    "candidateCount": 100,
    "topK": 5,
    "algorithm": "GNN_NSGA2"
  }
  ```
- **Expected Response (`200 OK`)**:
  ```json
  {
    "runId": 12,
    "status": "COMPLETED",
    "layoutCount": 5
  }
  ```
- **Common Errors**: 
  - `400 INVALID_REQUIREMENTS`: Missing requirements or buildings in the project.
  - `404 PROJECT_NOT_FOUND`: Non-existent or inaccessible project.
  - `422 GENERATION_FAILED`: Upstream ML failure in REAL mode (missing module, crash, or malformed layout output).
  - `500 INTERNAL_SERVER_ERROR`: Unhandled internal database or system crash.
- **Data Contracts Involved**: Data Contract 5 (`CampusGraph`), Contract 6 (`CandidateLayout`), Contract 8 (`RankedLayout`).

#### 14. `GET /api/projects/{projectId}/layouts`
- **Purpose**: Retrieve summary list and Pareto metrics for all generated layouts in a project.
- **Consumer**: Person 5 (Frontend Plan Comparison Screen)
- **Backend Owner**: Person 4
- **Modifiable by Others**: NO
- **Authentication**: `Bearer <token>`
- **Request Body**: None
- **Expected Response (`200 OK`)**:
  ```json
  {
    "layouts": [
      {
        "id": 101,
        "rank": 1,
        "feasible": true,
        "metrics": {
          "landUtilization": 0.72,
          "greenRatio": 0.25,
          "parkingRatio": 0.12,
          "accessibilityScore": 0.84,
          "roadEfficiency": 0.78,
          "constraintScore": 1.0
        }
      }
    ]
  }
  ```
- **Common Errors**: `401 UNAUTHORIZED`, `403 FORBIDDEN`, `404 PROJECT_NOT_FOUND`.
- **Data Contract**: Section 3.14 Specification & Data Contract 8 (`RankedLayout`).

#### 15. `GET /api/layouts/{layoutId}`
- **Purpose**: Retrieve full 2D spatial layout coordinates, site boundaries, green/parking areas, and road networks for 2D canvas rendering.
- **Consumer**: Person 5 (Frontend 2D Canvas Viewer)
- **Backend Owner**: Person 4
- **Modifiable by Others**: NO
- **Authentication**: `Bearer <token>`
- **Request Body**: None
- **Expected Response (`200 OK`)**:
  ```json
  {
    "id": 101,
    "rank": 1,
    "feasible": true,
    "site": {
      "width": 300,
      "height": 300
    },
    "buildings": [
      {
        "buildingId": 1,
        "x": 75,
        "y": 120,
        "rotation": 0
      }
    ],
    "roads": [],
    "greenAreas": [],
    "parkingAreas": [],
    "entrances": [
      {
        "x": 150,
        "y": 0,
        "width": 10
      }
    ],
    "metrics": {
      "landUtilization": 0.72,
      "greenRatio": 0.25,
      "parkingRatio": 0.12,
      "accessibilityScore": 0.84,
      "roadEfficiency": 0.78,
      "constraintScore": 1.0
    }
  }
  ```
- **Common Errors**: `401 UNAUTHORIZED`, `403 FORBIDDEN`, `404 LAYOUT_NOT_FOUND`.
- **Data Contract**: Data Contract 6 (`CandidateLayout`), Contract 8 (`RankedLayout`).

#### 16. `POST /api/layouts/{layoutId}/select`
- **Purpose**: Select a layout as the official campus plan. Records selection in `selected_plans` table and updates `project.status = "SELECTED"`.
- **Consumer**: Person 5 (Frontend Manager Selection Action)
- **Backend Owner**: Person 4
- **Modifiable by Others**: NO
- **Authentication**: `Bearer <token>`
- **Request Body**: `{}` (Empty JSON object)
- **Expected Response (`200 OK`)**:
  ```json
  {
    "projectId": 1,
    "layoutId": 101,
    "status": "SELECTED"
  }
  ```
- **Common Errors**: `401 UNAUTHORIZED`, `403 FORBIDDEN`, `404 LAYOUT_NOT_FOUND`.
- **Data Contract**: Section 3.16 Specification.

#### 17. `GET /api/layouts/{layoutId}/blueprint`
- **Purpose**: Export the complete 3D Blender Blueprint JSON. Merges candidate building spatial coordinates (`x, y, rotation`) with canonical building catalog metadata (`name, type, zone, width, depth, height, floorCount`) and site boundary dimensions.
- **Consumer**: Person 6 (Blender 3D Procedural Automation)
- **Backend Owner**: Person 4
- **Modifiable by Others**: NO
- **Authentication**: `Bearer <token>`
- **Request Body**: None
- **Expected Response (`200 OK`)**:
  ```json
  {
    "projectId": 1,
    "layoutId": 101,
    "site": {
      "width": 300,
      "height": 300
    },
    "buildings": [
      {
        "id": 1,
        "name": "Academic Block A",
        "type": "academic",
        "zone": "academic",
        "x": 75,
        "y": 120,
        "width": 60,
        "depth": 40,
        "height": 18,
        "rotation": 0,
        "floorCount": 4
      }
    ],
    "roads": [],
    "greenAreas": [],
    "parkingAreas": [],
    "entrances": []
  }
  ```
- **Common Errors**: `401 UNAUTHORIZED`, `403 FORBIDDEN`, `404 LAYOUT_NOT_FOUND`.
- **Data Contract**: Data Contract 9 (`Blueprint`).

---

# PART 3 — END-TO-END DATA FLOW

```
[ Frontend / Manager UI (Person 5) ]
         │
         │  POST /api/projects
         │  POST /api/projects/{id}/requirements
         │  POST /api/projects/{id}/buildings
         │  POST /api/projects/{id}/constraints
         ▼
[ FastAPI Backend & PostgreSQL (Person 4) ]
         │
         │  POST /api/projects/{id}/layout-runs (candidateCount=100, topK=5)
         ▼
[ Orchestrator & ML Bridge (Person 4) ]
         │
         │  campus_data: { siteWidth, siteHeight, buildings[], constraints[], entrances[] }
         ▼
[ Graph Builder: build_graph() (Person 1) ]
         │
         │  CampusGraph: { nodeFeatures, edgeIndex, edgeFeatures } (Contract 5)
         ▼
[ GNN Generator: generate_candidates() (Person 2) ]
         │
         │  CandidateLayout[]: 100 candidate layouts (Contract 6)
         ▼
[ Multi-Objective Optimizer: optimize_layouts() (Person 3) ]
         │
         │  RankedLayout[]: top 5 Pareto-optimal layouts with metrics (Contract 8)
         ▼
[ Backend Persistence (Person 4) ]
         │  Inserts into layout_runs and layouts tables
         │  Returns {"runId": 12, "status": "COMPLETED", "layoutCount": 5}
         ▼
[ Frontend Comparison (Person 5) ]
         │  GET /api/projects/{id}/layouts -> Compares metrics
         │  GET /api/layouts/{id}         -> Renders 2D Canvas layout
         │  POST /api/layouts/{id}/select -> Confirms selection
         ▼
[ Blueprint Export (Person 4) ]
         │  GET /api/layouts/{id}/blueprint -> Synthesizes Contract 9 Blueprint
         ▼
[ Blender Procedural 3D (Person 6) ]
         │  Reads Blueprint JSON
         ▼
[ 3D Model (.blend) & Render (.png) ]
```

### Exact Data Crossing Each Boundary
1. **P5 $\rightarrow$ P4**: HTTP JSON request payloads over REST APIs (Auth, Requirements, Buildings, Constraints).
2. **P4 $\rightarrow$ P1**: Python dictionary `campus_data` with site dimensions, building definitions, and constraints.
3. **P1 $\rightarrow$ P2**: `CampusGraph` object conforming to Data Contract 5 (`nodeFeatures`, `edgeIndex`, `edgeFeatures`).
4. **P2 $\rightarrow$ P3**: Python list of 100 `CandidateLayout` objects conforming to Data Contract 6 (`candidateId`, `siteWidth`, `siteHeight`, `buildings: [{buildingId, x, y, rotation}]`).
5. **P3 $\rightarrow$ P4**: Python list of top 5 `RankedLayout` objects conforming to Data Contract 8 with validated metrics.
6. **P4 $\rightarrow$ P5**: REST JSON response objects (`/layouts` and `/layouts/{id}`) providing Pareto metrics and 2D coordinates.
7. **P4 $\rightarrow$ P6**: REST JSON Blueprint matching Data Contract 9 (`site`, merged `buildings`, `roads`, `greenAreas`, `parkingAreas`, `entrances`).

---

# PART 4 — PERSON 1 GUIDE
## PERSON 1 — DATASET / CAMPUS GRAPH BUILDER

### 1. Responsibility
Person 1 owns the mathematical and structural representation of the campus planning problem. Person 1 translates real campus requirements and building catalogs into a structured graph that the GNN can consume.

### 2. Required Files
- **Primary Interface**: `ml/dataset/graph_builder.py`
- **Internal Helper Modules**:
  - `ml/data/schemas.py`
  - `ml/data/campus_schema.py`
  - `ml/data/building_schema.py`
  - `ml/data/constraint_schema.py`
  - `ml/data/relationships.py`
  - `ml/dataset/generator.py` (synthetic campus generator)
  - `ml/dataset/validation.py`

### 3. Required Function Signature
```python
def build_graph(campus_data: dict) -> CampusGraph:
    """
    Constructs a heterogeneous/homogeneous graph representation of campus requirements.
    Must return a CampusGraph conforming to Data Contract 5.
    """
```

### 4. Exact Input Structure (`campus_data: dict`)
`campus_data` is supplied directly by Person 4 (derived from `requirements`, `buildings`, and `constraints` APIs):
```json
{
  "projectId": 1,
  "siteWidth": 300.0,
  "siteHeight": 300.0,
  "minGreenPercent": 25.0,
  "minParkingPercent": 10.0,
  "minRoadWidth": 8.0,
  "minBuildingGap": 10.0,
  "entrances": [
    {"x": 150.0, "y": 0.0, "width": 10.0}
  ],
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
      "requiredCount": 1
    }
  ],
  "constraints": [
    {
      "id": 1,
      "type": "MIN_DISTANCE",
      "sourceId": 1,
      "targetId": 5,
      "value": 100.0,
      "operator": ">=",
      "priority": "hard"
    }
  ]
}
```

### 5. Exact Output Structure (Contract 5: `CampusGraph`)
Person 1's function must return an object or dict with:
- `nodeFeatures`: 2D list of floats (`float[][]`) representing building properties (e.g., width, depth, height, floorCount, encoded type/zone).
- `edgeIndex`: 2D list of integers (`int[2][E]`) representing graph adjacency connections between buildings.
- `edgeFeatures`: 2D list of floats (`float[][]`) representing relationship types (e.g. distance requirements, accessibility weight, zone proximity).

```python
class CampusGraph:
    def __init__(self, node_features: list[list[float]], edge_index: list[list[int]], edge_features: list[list[float]]):
        self.nodeFeatures = node_features
        self.edgeIndex = edge_index
        self.edgeFeatures = edge_features
```

### 6. What Person 1 MUST NOT Do
- **Do NOT modify backend code**: Do not touch files in `backend/` or `alembic/`.
- **Do NOT create new REST APIs**: Graph construction is internal Python; it does not have an HTTP endpoint.
- **Do NOT write to PostgreSQL**: Person 1 is strictly a data producer for Person 2.
- **Do NOT invent extra fields** outside Contract 5.

---

# PART 5 — PERSON 2 GUIDE
## PERSON 2 — GNN / CANDIDATE LAYOUT GENERATOR

### 1. Responsibility
Person 2 owns the deep learning model (Graph Neural Network) that takes a `CampusGraph` and predicts 2D coordinates (`x, y`) and orientation (`rotation`) for all buildings on the campus plot.

### 2. Required Files
- **Primary Interface**: `ml/inference/generate.py`
- **Internal Model Modules**:
  - `ml/models/gnn_encoder.py`
  - `ml/models/layout_decoder.py`
  - `ml/models/campus_model.py`
  - `ml/training/train.py`
  - `ml/training/loss.py`
  - `ml/training/evaluate.py`

### 3. Required Function Signature
```python
def generate_candidates(
    campus_graph: CampusGraph,
    num_candidates: int = 100
) -> list[CandidateLayout]:
    """
    Executes model inference to generate candidate campus layouts.
    Must return a list of CandidateLayout objects conforming to Data Contract 6.
    """
```

### 4. Exact Input Structure
- `campus_graph`: The `CampusGraph` produced by Person 1's `build_graph()` function.
- `num_candidates`: Integer specifying the number of candidates to sample (default: 100).

### 5. Exact Output Structure (Contract 6: `CandidateLayout`)
Person 2 must return a Python list of candidate dictionaries or dataclasses matching:
```json
[
  {
    "candidateId": "candidate-001",
    "siteWidth": 300.0,
    "siteHeight": 300.0,
    "buildings": [
      {
        "buildingId": 1,
        "x": 72.4,
        "y": 120.8,
        "rotation": 0.0
      }
    ]
  }
]
```

### 6. Coordinate Standards (Crucial for Downstream Geometry & Blender)
- **Origin `(0, 0)`**: Bottom-left corner of the campus bounding box.
- **X**: East / West (range: `0.0` to `siteWidth`).
- **Y**: North / South (range: `0.0` to `siteHeight`).
- **Units**: Metres.
- **Rotation**: Degrees counter-clockwise (default: `0.0`).

### 7. What Person 2 MUST NOT Do
- **Do NOT modify backend routes or database tables**.
- **Do NOT create REST endpoints**: Person 2 is invoked directly as a Python function by Person 4's `ml_bridge`.
- **Do NOT filter candidates**: Person 2 generates the diverse population (e.g. 100 layouts). Filtering, constraint validation, and ranking belong strictly to Person 3.

---

# PART 6 — PERSON 3 GUIDE
## PERSON 3 — NSGA-II OPTIMIZER

### 1. Responsibility
Person 3 owns the algorithmic evaluation, hard-constraint verification, and multi-objective optimization (NSGA-II) engine that evaluates candidate layouts and selects the top-5 Pareto-optimal layouts.

### 2. Required Files
- **Primary Interface**: `optimization/optimizer.py`
- **Internal Optimization Modules**:
  - `optimization/constraints/boundary.py`
  - `optimization/constraints/overlap.py`
  - `optimization/constraints/distance.py`
  - `optimization/constraints/zoning.py`
  - `optimization/constraints/roads.py`
  - `optimization/constraints/green.py`
  - `optimization/constraints/parking.py`
  - `optimization/validator.py`
  - `optimization/objectives.py`
  - `optimization/nsga2.py`
  - `optimization/ranking.py`

### 3. Required Function Signature
```python
def optimize_layouts(
    candidates: list[CandidateLayout],
    requirements: dict,
    constraints: list[dict],
    top_k: int = 5
) -> list[RankedLayout]:
    """
    Validates hard constraints, computes multi-objective fitness scores,
    runs NSGA-II selection, and returns top_k Pareto-ranked layouts.
    """
```

### 4. Exact Inputs Received
- `candidates`: List of `CandidateLayout` objects from Person 2.
- `requirements`: Dictionary containing site constraints (`siteWidth`, `siteHeight`, `minGreenPercent`, `minParkingPercent`, `minRoadWidth`, `minBuildingGap`, `entrances`).
- `constraints`: List of defined project constraints (`type`, `sourceId`, `targetId`, `value`, `operator`, `priority`).
- `top_k`: Number of top ranked plans to return (default: 5).

### 5. Exact Output Structure (Contract 8: `RankedLayout`)
Must return a list of exactly `top_k` ranked layout dictionaries or dataclasses:
```json
[
  {
    "candidateId": "candidate-001",
    "rank": 1,
    "feasible": true,
    "buildings": [
      {
        "buildingId": 1,
        "x": 72.4,
        "y": 120.8,
        "rotation": 0.0
      }
    ],
    "metrics": {
      "landUtilization": 0.72,
      "greenRatio": 0.25,
      "parkingRatio": 0.12,
      "accessibilityScore": 0.84,
      "roadEfficiency": 0.78,
      "constraintScore": 1.0
    }
  }
]
```

### 6. Failure Behavior
- If hard constraints are violated and no feasible plans exist, Person 3 must raise an exception or set `feasible: false` with violations.
- Never return an empty list or malformed dictionary. Person 4 catches any exception and surfaces `HTTP 422 GENERATION_FAILED` to the user.

---

# PART 7 — PERSON 4 GUIDE
## PERSON 4 — BACKEND / ORCHESTRATION

### 1. Responsibility
Person 4 owns the centralized FastAPI application, PostgreSQL database, Alembic migrations, security/auth, Pydantic schemas, and the system orchestration pipeline.

### 2. Files Owned
- `backend/main.py`
- `backend/config.py`
- `backend/database.py`
- `backend/security.py`
- `backend/api/*` (`auth.py`, `projects.py`, `requirements.py`, `buildings.py`, `constraints.py`, `layouts.py`)
- `backend/models/*` (all 8 SQLAlchemy models)
- `backend/schemas/*` (all Pydantic validation schemas)
- `backend/services/orchestrator.py`
- `backend/services/ml_bridge.py`
- `backend/services/blueprint_service.py`
- `alembic.ini` & `alembic/*`
- `backend/tests/*`

### 3. Pipeline Modes (`backend/config.py`)
- **`PIPELINE_MODE=mock` (Default)**:
  - Invokes `mock_generate()` in `backend/services/orchestrator.py`.
  - Produces deterministic, contract-compliant candidate layouts so Person 5 and Person 6 can develop and test immediately without GPU/model weights.
- **`PIPELINE_MODE=real`**:
  - Invokes `run_real_pipeline()` in `backend/services/ml_bridge.py`.
  - Executes Person 1 $\rightarrow$ Person 2 $\rightarrow$ Person 3 in sequence.
  - **No Silent Fallback**: If Person 1, 2, or 3 fails, the backend immediately raises `HTTP 422 GENERATION_FAILED`. It will never fall back to mock data.

---

# PART 8 — PERSON 5 GUIDE
## PERSON 5 — FRONTEND / 2D CAMPUS PLANNING

### 1. Responsibility
Person 5 builds the React/TypeScript web application that allows the campus project manager to authenticate, create projects, configure requirements and buildings, trigger layout generation, compare Pareto metrics, view 2D plans on a canvas, and select the winning plan.

### 2. Base Configuration
- **API Base URL**: `http://localhost:8000`
- **Interactive API Documentation**: `http://localhost:8000/docs`
- **OpenAPI JSON Spec**: `http://localhost:8000/openapi.json` (or [`docs/openapi.json`](docs/openapi.json))

### 3. Exact Frontend User Flow
1. **Register & Login**:
   - `POST /api/auth/register` $\rightarrow$ `POST /api/auth/login`
   - Store `accessToken` in memory or local storage.
   - Attach header to all subsequent calls: `Authorization: Bearer <accessToken>`.
2. **Project Setup**:
   - `POST /api/projects` $\rightarrow$ returns `{ "id": projectId, ... }`.
   - `POST /api/projects/{projectId}/requirements` $\rightarrow$ saves site dimensions (`siteWidth`, `siteHeight`) and entrance list.
   - `POST /api/projects/{projectId}/buildings` $\rightarrow$ adds each required building (`name`, `type`, `zone`, `width`, `depth`, `height`, `floorCount`).
   - `POST /api/projects/{projectId}/constraints` $\rightarrow$ adds distance and zoning constraints.
3. **Trigger Generation**:
   - `POST /api/projects/{projectId}/layout-runs` with body `{"candidateCount": 100, "topK": 5, "algorithm": "GNN_NSGA2"}`.
   - Returns `{ "runId": 12, "status": "COMPLETED", "layoutCount": 5 }`.
4. **Compare Plans**:
   - `GET /api/projects/{projectId}/layouts` $\rightarrow$ returns array of top layouts with their 6 Pareto metrics (`landUtilization`, `greenRatio`, `parkingRatio`, `accessibilityScore`, `roadEfficiency`, `constraintScore`).
5. **Inspect 2D Canvas**:
   - `GET /api/layouts/{layoutId}` $\rightarrow$ returns site dimensions and building `(x, y, rotation)` coordinates for rendering on HTML5 Canvas or SVG.
6. **Select Winning Plan**:
   - `POST /api/layouts/{layoutId}/select` with body `{}`.
   - Confirms selection and updates project status to `SELECTED`.

### 4. What Person 5 MUST NOT Do
- **Do NOT connect directly to PostgreSQL**.
- **Do NOT call Python modules directly**: All communication is through the 17 REST APIs.
- **Do NOT change JSON field casing**: All API payloads are strictly `camelCase`.

---

# PART 9 — PERSON 6 GUIDE
## PERSON 6 — BLENDER / 3D PROCEDURAL GENERATION

### 1. Responsibility
Person 6 builds the automated Blender Python pipeline that converts the manager's selected 2D layout blueprint into a 3D architectural visualization and rendered presentation image.

### 2. Primary API Consumed
- **Endpoint**: `GET /api/layouts/{layoutId}/blueprint`
- **Header**: `Authorization: Bearer <token>`
- **Transport**: HTTP GET request (or feeding exported blueprint JSON file to Blender Python script).

### 3. Exact Blueprint Structure (Data Contract 9)
```json
{
  "projectId": 1,
  "layoutId": 101,
  "site": {
    "width": 300.0,
    "height": 300.0
  },
  "buildings": [
    {
      "id": 1,
      "name": "Academic Block A",
      "type": "academic",
      "zone": "academic",
      "x": 75.0,
      "y": 120.0,
      "width": 60.0,
      "depth": 40.0,
      "height": 18.0,
      "rotation": 0.0,
      "floorCount": 4
    }
  ],
  "roads": [],
  "greenAreas": [],
  "parkingAreas": [],
  "entrances": [
    {
      "x": 150.0,
      "y": 0.0,
      "width": 10.0
    }
  ]
}
```

### 4. Blender Coordinate Mapping Rules
- **Origin `(0, 0, 0)`**: Bottom-left corner of the campus ground plane.
- **X**: East / West $\rightarrow$ Maps to Blender **X-axis**.
- **Y**: North / South $\rightarrow$ Maps to Blender **Y-axis**.
- **Z**: Height $\rightarrow$ Maps to Blender **Z-axis** (vertical elevation).
- **Rotation**: Degrees counter-clockwise around the Z-axis.
- **Building Footprint**: Centered at `(x + width/2, y + depth/2, height/2)` in Blender coordinates if modeling from center, or positioned from corner depending on mesh origin.

### 5. What Person 6 MUST NOT Do
- **Do NOT query PostgreSQL directly**.
- **Do NOT invent a separate REST server**: Blender is an offline/procedural client that consumes the Blueprint JSON.

---

# PART 10 — CROSS-PERSON CONTRACT TABLE

| Producer | Output Artifact | Consumer | Contract | Interface / Transport | Failure / Error Behavior |
|:---:|:---:|:---:|:---:|:---:|:---:|
| **Person 4** | `campus_data: dict` | **Person 1** | Requirements / Buildings / Constraints | Internal Python dictionary | `400 INVALID_REQUIREMENTS` if missing |
| **Person 1** | `CampusGraph` | **Person 2** | Contract 5 (`nodeFeatures`, `edgeIndex`, `edgeFeatures`) | `build_graph()` in `ml/dataset/graph_builder.py` | `422 GENERATION_FAILED` if fails |
| **Person 2** | `CandidateLayout[]` | **Person 3** | Contract 6 (`candidateId`, `siteWidth`, `siteHeight`, `buildings`) | `generate_candidates()` in `ml/inference/generate.py` | `422 GENERATION_FAILED` if fails |
| **Person 3** | `RankedLayout[]` | **Person 4** | Contract 8 (`candidateId`, `rank`, `feasible`, `buildings`, `metrics`) | `optimize_layouts()` in `optimization/optimizer.py` | `422 GENERATION_FAILED` if fails |
| **Person 4** | REST Responses | **Person 5** | Section 3 APIs (camelCase JSON) | HTTP REST (`http://localhost:8000/api`) | `400`, `401`, `403`, `404`, `422` |
| **Person 4** | Blueprint JSON | **Person 6** | Contract 9 (`projectId`, `layoutId`, `site`, `buildings`, etc.) | `GET /api/layouts/{layoutId}/blueprint` | `401`, `403`, `404` |

---

# PART 11 — WHO CHANGES WHAT: STRICT REPOSITORY OWNERSHIP

| Person | Directory / Files Owned | Integration Boundary Files | Strict Prohibitions |
|:---:|---|---|---|
| **P1** | `ml/data/*`<br>`ml/dataset/*`<br>`ml/datasets/*` | `ml/dataset/graph_builder.py` | Must **NOT** modify `backend/`, `alembic/`, or create REST APIs. |
| **P2** | `ml/models/*`<br>`ml/training/*`<br>`ml/inference/*` | `ml/inference/generate.py` | Must **NOT** modify backend database models or alter Contract 6. |
| **P3** | `optimization/*` | `optimization/optimizer.py` | Must **NOT** bypass Person 4 or invent new REST endpoints. |
| **P4** | `backend/*`<br>`alembic/*`<br>`docs/*`<br>`requirements.txt` | `backend/services/ml_bridge.py`<br>`backend/services/orchestrator.py` | Must **NOT** invent or hard-code real ML model weights. |
| **P5** | `frontend/*` | `frontend/src/api/*` | Must **NOT** access PostgreSQL directly or call Python ML modules. |
| **P6** | `blender/*` | `blender/generator.py` | Must **NOT** access PostgreSQL; consumes only Blueprint Contract 9. |

---

# PART 12 — IMPLEMENTATION & MERGE ORDER

1. **Step 1 — Parallel Foundation (Already Active)**:
   - Backend Phases 1–12 complete: REST APIs, DB tables, and MOCK pipeline operational.
   - Person 5 builds frontend against the 17 REST APIs in MOCK mode.
   - Person 6 builds procedural Blender script against Contract 9 Blueprint JSON.
2. **Step 2 — Person 1 Delivers Graph Builder**:
   - Person 1 authors `ml/dataset/graph_builder.py` $\rightarrow$ `build_graph(campus_data)`.
   - Verified with unit test asserting Contract 5 output.
3. **Step 3 — Person 2 Delivers Candidate Generator**:
   - Person 2 trains model and authors `ml/inference/generate.py` $\rightarrow$ `generate_candidates(graph, 100)`.
   - Verified with unit test asserting Contract 6 output.
4. **Step 4 — Person 3 Delivers NSGA-II Optimizer**:
   - Person 3 authors `optimization/optimizer.py` $\rightarrow$ `optimize_layouts(candidates, reqs, constraints, 5)`.
   - Verified with unit test asserting Contract 8 output.
5. **Step 5 — Full System Integration**:
   - Set environment variable `PIPELINE_MODE=real`.
   - Execute `POST /api/projects/{projectId}/layout-runs` to run the real end-to-end pipeline.
   - Run complete test suite: `pytest backend/tests -v`.

---

# PART 13 — API QUICK REFERENCE CHEAT SHEET

| Method | Endpoint Path | Input | Key Output | Primary Consumer |
|:---:|---|---|---|:---:|
| `POST` | `/api/auth/register` | `name`, `email`, `password` | `id`, `role` | Person 5 |
| `POST` | `/api/auth/login` | `email`, `password` | `accessToken`, `user` | Person 5 |
| `POST` | `/api/projects` | `name`, `description` | `id`, `status: "DRAFT"` | Person 5 |
| `GET` | `/api/projects/{projectId}` | None | Project entity | Person 5 |
| `PUT` | `/api/projects/{projectId}` | `name`, `description` | Updated project entity | Person 5 |
| `DELETE` | `/api/projects/{projectId}` | None | `204 No Content` | Person 5 |
| `POST` | `/api/projects/{projectId}/requirements` | `siteWidth`, `siteHeight`, `entrances`, etc. | Requirements entity | Person 5 |
| `GET` | `/api/projects/{projectId}/requirements` | None | Requirements entity | Person 5, Person 1 |
| `POST` | `/api/projects/{projectId}/buildings` | `name`, `type`, `zone`, `width`, `depth`, etc. | Building entity | Person 5 |
| `GET` | `/api/projects/{projectId}/buildings` | None | `buildings: [...]` | Person 5, Person 1 |
| `POST` | `/api/projects/{projectId}/constraints` | `type`, `sourceId`, `targetId`, `value`, etc. | Constraint entity | Person 5 |
| `GET` | `/api/projects/{projectId}/constraints` | None | `constraints: [...]` | Person 5, Person 1, Person 3 |
| `POST` | `/api/projects/{projectId}/layout-runs` | `candidateCount`, `topK`, `algorithm` | `runId`, `status`, `layoutCount` | Person 5 |
| `GET` | `/api/projects/{projectId}/layouts` | None | `layouts: [{id, rank, metrics}]` | Person 5 |
| `GET` | `/api/layouts/{layoutId}` | None | `site`, `buildings`, `metrics`, etc. | Person 5 |
| `POST` | `/api/layouts/{layoutId}/select` | `{}` | `projectId`, `layoutId`, `status: "SELECTED"` | Person 5 |
| `GET` | `/api/layouts/{layoutId}/blueprint` | None | Full Contract 9 Blueprint JSON | Person 6 |

---

# PART 14 — DO NOT BREAK THESE RULES CHECKLIST

- [ ] **Do NOT change master API paths**: Keep all 17 paths verbatim.
- [ ] **Do NOT change camelCase REST fields**: Maintain `projectId`, `siteWidth`, `floorCount`, etc.
- [ ] **Do NOT bypass authentication**: All protected endpoints require `Bearer <token>`.
- [ ] **Do NOT bypass ownership checks**: Users may only access their own projects.
- [ ] **Do NOT access PostgreSQL directly from Frontend or Blender**.
- [ ] **Do NOT create duplicate APIs**: Use only the 17 master endpoints.
- [ ] **Do NOT silently fall back from REAL to MOCK**: Real errors must surface `422 GENERATION_FAILED`.
- [ ] **Do NOT invent missing P1/P2/P3 implementations in backend code**.
- [ ] **Do NOT alter Data Contracts 5, 6, 8, or 9 without full team approval**.
- [ ] **Do NOT expose internal database fields** (`road_data`, `total_area`, `password_hash`).
- [ ] **Do NOT modify another person's directory without coordination**.
- [ ] **Test all integration code against the 70 existing backend verification tests**.

---

# PART 15 — FINAL INTEGRATION CHECKLIST

### PERSON 1 (Dataset / Campus Graph):
- [ ] `ml/dataset/graph_builder.py` exists and is importable.
- [ ] `build_graph(campus_data)` function implemented.
- [ ] Output satisfies Contract 5 (`nodeFeatures`, `edgeIndex`, `edgeFeatures`).
- [ ] Unit test verifies graph construction from sample campus requirements.

### PERSON 2 (GNN / Layout Generator):
- [ ] `ml/inference/generate.py` exists and is importable.
- [ ] `generate_candidates(campus_graph, num_candidates)` function implemented.
- [ ] Output satisfies Contract 6 (list of `CandidateLayout` objects).
- [ ] Coordinates respect `(0, 0)` bottom-left origin and metre units.

### PERSON 3 (NSGA-II Optimizer):
- [ ] `optimization/optimizer.py` exists and is importable.
- [ ] `optimize_layouts(candidates, requirements, constraints, top_k)` function implemented.
- [ ] Output satisfies Contract 8 (list of `RankedLayout` objects with 6 metrics).
- [ ] Hard constraints validated without silently ignoring invalid inputs.

### PERSON 4 (Backend / Orchestrator):
- [ ] Both `MOCK` and `REAL` pipeline modes verified.
- [ ] Zero silent fallback from `REAL` to `MOCK` verified.
- [ ] Missing or failing ML modules surface `422 GENERATION_FAILED`.
- [ ] All 70 backend tests pass with zero failures.

### PERSON 5 (Frontend / 2D Planner):
- [ ] Register and Login workflows complete and store Bearer token.
- [ ] Project, requirements, buildings, and constraints forms integrated.
- [ ] Layout generation triggered and progress/completion handled.
- [ ] Layout comparison screen and 2D canvas viewer render coordinates correctly.
- [ ] Plan selection endpoint successfully triggered.

### PERSON 6 (Blender / 3D Procedural):
- [ ] Consumes `GET /api/layouts/{layoutId}/blueprint` JSON.
- [ ] Successfully parses Contract 9 structure.
- [ ] Maps 2D coordinates `(x, y)` and `height` to 3D Blender geometry.
- [ ] Automated render script outputs `.blend` and `.png`.

### FINAL TEAM ACCEPTANCE:
- [ ] Real pipeline executes: Person 1 $\rightarrow$ Person 2 $\rightarrow$ Person 3 $\rightarrow$ Person 4.
- [ ] Generated layouts persist in PostgreSQL.
- [ ] Frontend successfully displays real generated layouts and selects a plan.
- [ ] Blender generates 3D campus from selected blueprint.
- [ ] Full end-to-end test suite passes: `pytest backend/tests -v`.

---

# PART 16 — REPOSITORY CLONING & LOCAL SETUP GUIDE
## Complete "CLONE → SETUP → RUN → VERIFY" Guide for Every Teammate

This section provides an unambiguous, step-by-step onboarding procedure for a teammate joining the project on a clean development machine.

---

### 16.1 Prerequisites

The table below distinguishes dependencies verified in the repository from upstream dependencies that must be declared by the respective module owners:

| Dependency | Required By | Version Discovered / Expected | Required / Optional | Purpose |
|---|---|:---:|:---:|---|
| **Git** | All Teammates | `>= 2.30` | **Required** | Source code version control and branch management |
| **Python** | Persons 1, 2, 3, 4, 6 | `3.11.x` (Verified `3.11.9`) | **Required** | Runtime for backend, ML pipeline, and optimizer |
| **pip / venv** | Persons 1, 2, 3, 4 | Standard with Python 3.11 | **Required** | Package management and virtual environment isolation |
| **PostgreSQL** | Person 4 (Backend) | `>= 15.0` (Docker container) | **Required for P4** (Optional for P1, P2, P3, P5, P6) | Relational persistence for the 8 contract tables |
| **Node.js & npm** | Person 5 (Frontend) | `>= 18.0` / npm `>= 9.0` | **Required for P5** (Optional for others) | React / Vite development server and build tools |
| **Blender** | Person 6 (3D) | `>= 3.6 LTS` / `4.x` | **Required for P6** (Optional for others) | Procedural 3D scene execution and rendering |
| **PyTorch & PyG** | Person 1, Person 2 | *To be declared by P1/P2* | **Required for P1/P2** | Graph neural network training and inference |
| **pymoo / Shapely**| Person 3 (Optimizer) | *To be declared by P3* | **Required for P3** | NSGA-II multi-objective optimization & geometry |

> [!NOTE]
> *Dependency Declaration Note*: P1, P2, and P3 dependencies (such as `torch`, `torch-geometric`, `pymoo`, `shapely`) are **not** currently locked in the backend `requirements.txt` to keep the backend lightweight and decouple development. These dependencies must be supplied/declared by the respective module owners in their feature branches.

---

### 16.2 Clone the Repository

Clone the official GitHub repository and navigate into the root directory:

```bash
git clone https://github.com/jyotydivya/ArchOpt.git
cd ArchOpt
```

#### Branch Strategy & Naming Conventions
The repository uses feature branches per contributor. Existing team branches discovered in the remote:
- `main` — Production-ready, reviewed, and contract-verified code.
- `dev/krish` — Backend orchestration and core API baseline.
- `dev/anshika`, `dev/dj`, `dev/jeet`, `dev/tanmayi`, `dev/tanuj` — Teammate development branches.

**Branch Rule**:
Always branch from `main` or checkout your designated development branch. Never commit directly to `main`.
```bash
git checkout -b feature/person-<N>-<module-name>
# Example: git checkout -b feature/p1-graph-builder
```

---

### 16.3 Python Virtual Environment

Create and activate an isolated Python 3.11 virtual environment in the repository root:

#### On Windows (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

#### On Linux / macOS (Bash):
```bash
python3 -m venv .venv
source .venv/bin/activate
```

#### Install Verified Backend Dependencies:
The repository provides a clean `requirements.txt` locking core backend dependencies:
```bash
pip install -r requirements.txt
```

#### Verify Installation:
```bash
python --version   # Must output Python 3.11.x
pip list           # Must show fastapi, sqlalchemy, alembic, pydantic, PyJWT, bcrypt
```

---

### 16.4 Environment Variables

The backend uses `pydantic-settings` to load configuration from environment variables or a local `.env` file.

Copy the provided template to create your `.env`:
```bash
cp .env.example .env     # Linux / macOS
copy .env.example .env   # Windows
```

#### Configuration Reference Table

| Variable | Default / Example Value | Used By | Required? | Purpose |
|---|---|:---:|:---:|---|
| `DATABASE_URL` | `postgresql://postgres:postgres@localhost:5433/campus_planner` | Person 4, Alembic | **Yes** | PostgreSQL connection URL (Port `5433` for container, `5432` for local) |
| `SECRET_KEY` | `archopt_development_super_secret_key_32_bytes_min!` | Person 4 | **Yes** | Secret HMAC key for signing JWT tokens (min 32 bytes for HS256) |
| `ALGORITHM` | `HS256` | Person 4 | No (default `HS256`) | Cryptographic algorithm for JWT |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` (24 hours) | Person 4 | No (default `1440`) | Token lifetime before expiration |
| `PIPELINE_MODE` | `mock` | Person 4 | **Yes** | Execution mode: `mock` (no ML needed) or `real` (requires P1/P2/P3) |
| `DEBUG` | `True` | Person 4 | No (default `True`) | FastAPI debug mode |
| `APP_NAME` | `AI Campus Planner Backend` | Person 4 | No | Application display title |

#### Choosing Your `PIPELINE_MODE`:
- **`PIPELINE_MODE=mock` (Recommended for Persons 4, 5, 6 during development)**:
  - Generates deterministic, Contract 6/8 compliant layouts immediately without ML libraries.
  - Allows full frontend UI and 3D Blender integration to proceed without waiting for model training.
- **`PIPELINE_MODE=real` (Used when integrating Persons 1, 2, and 3)**:
  - Dispatches execution directly to `ml.dataset.graph_builder`, `ml.inference.generate`, and `optimization.optimizer`.
  - **Zero Silent Fallback**: If any ML module is missing, throws an exception, or outputs malformed data, the backend strictly returns `422 GENERATION_FAILED`.

---

### 16.5 PostgreSQL Setup

The backend stores all entities in PostgreSQL across the **8 contract tables**:
1. `users`
2. `projects`
3. `campus_requirements` (internally preserves `road_data JSONB`)
4. `buildings`
5. `constraints`
6. `layout_runs`
7. `layouts`
8. `selected_plans`

#### Recommended Setup via Docker:
Run a dedicated PostgreSQL 15+ container matching the default `backend/config.py` configuration:
```bash
docker run --name archopt-postgres -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=campus_planner -p 5433:5432 -d postgres:15
```
*(If running native local PostgreSQL on port 5432, update `DATABASE_URL` in `.env` to port 5432).*

---

### 16.6 Database Initialization & Alembic Migrations

Run database migrations to generate all 8 contract tables in PostgreSQL:

```bash
# Apply migrations to head
python -m alembic upgrade head

# Verify migration state
python -m alembic current
# Expected Output: 001_initial_schema (head)
```

> [!NOTE]
> *Seed Data Note*: The repository does not require or provide an automatic database seed script. The database is initialized empty, and test fixtures populate isolated test records dynamically during test execution.

---

### 16.7 Backend Startup

Start the FastAPI application with Uvicorn:

```bash
python -m uvicorn backend.main:app --reload --port 8000
```

#### Expected Startup Log:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [...]
INFO:     Started server process [...]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

#### Critical URLs:
- **Root Health Check**: `http://localhost:8000/` (`{"status": "ok", "app": "AI Campus Planner Backend"}`)
- **Interactive Swagger Docs**: `http://localhost:8000/docs`
- **OpenAPI JSON Spec**: `http://localhost:8000/openapi.json`

---

### 16.8 Minimal Backend Verification Procedure

Follow these 9 verification steps to confirm system health on a fresh machine:
1. Ensure PostgreSQL container is running (`docker ps` shows `archopt-postgres`).
2. Activate `.venv`.
3. Ensure `.env` exists with valid `SECRET_KEY`.
4. Run `python -m alembic current` $\rightarrow$ must show `001_initial_schema (head)`.
5. Start backend: `python -m uvicorn backend.main:app --port 8000`.
6. Open browser to `http://localhost:8000/docs`.
7. Execute `POST /api/auth/register` with `{"name": "Admin", "email": "admin@example.com", "password": "password123"}` $\rightarrow$ Expect `201 Created`.
8. Execute `POST /api/auth/login` $\rightarrow$ Expect `200 OK` with `accessToken`.
9. Authorize Swagger with the token and execute `POST /api/projects` $\rightarrow$ Expect `201 Created`.

---

### 16.9 Running the Automated Test Suite

Execute the complete 70-test backend verification suite:

```bash
# Quick summary execution
python -m pytest backend/tests -q

# Verbose execution with full test case names
python -m pytest backend/tests -v
```

- **Expected Result**: `70 passed in ~60s` (Exit Code 0).
- **Rule for Teammates**: All existing 70 tests must remain GREEN at all times. If a teammate adds tests for their module, they must add them in their own test file without modifying or breaking existing tests.

---

### 16.10 Person-Specific Setup Requirements

#### PERSON 1 (Dataset / Campus Graph):
- **Local Requirements**: Git, Python 3.11, virtual environment, PyTorch / graph libraries.
- **Database Needed?**: **NO direct PostgreSQL access needed.** Person 1's `build_graph()` receives `campus_data: dict` pre-formatted by Person 4 from the database.
- **Deliverable**: `ml/dataset/graph_builder.py` exporting `build_graph(campus_data: dict) -> CampusGraph`.
- **Verification**: Ensure output matches Data Contract 5 (`nodeFeatures`, `edgeIndex`, `edgeFeatures`).

#### PERSON 2 (GNN / Layout Generator):
- **Local Requirements**: Git, Python 3.11, virtual environment, PyTorch, PyTorch Geometric, trained model weights/checkpoints.
- **Database Needed?**: **NO direct PostgreSQL access needed.** Person 2 receives `CampusGraph` from Person 1.
- **Deliverable**: `ml/inference/generate.py` exporting `generate_candidates(campus_graph, num_candidates=100) -> list[CandidateLayout]`.
- **Verification**: Ensure output matches Data Contract 6 (`candidateId`, `siteWidth`, `siteHeight`, `buildings: [{buildingId, x, y, rotation}]`).

#### PERSON 3 (NSGA-II Optimizer):
- **Local Requirements**: Git, Python 3.11, virtual environment, `pymoo`, `shapely`.
- **Database Needed?**: **NO direct PostgreSQL access needed.** Person 3 receives candidate layouts, requirements, and constraints from Person 4's orchestrator.
- **Deliverable**: `optimization/optimizer.py` exporting `optimize_layouts(candidates, requirements, constraints, top_k=5) -> list[RankedLayout]`.
- **Verification**: Ensure output matches Data Contract 8 (`candidateId`, `rank`, `feasible`, `buildings`, `metrics`).

#### PERSON 4 (Backend / Orchestration):
- **Local Requirements**: Git, Python 3.11, virtual environment, PostgreSQL, Docker, Alembic.
- **Database Needed?**: **YES.** Person 4 owns the PostgreSQL schema and all 8 tables.
- **Deliverable**: Full backend API, DB migrations, ML bridge, and test suites.

#### PERSON 5 (Frontend / 2D Planner):
- **Local Requirements**: Git, Node.js 18+, npm, browser.
- **Database Needed?**: **NO.** Person 5 connects exclusively via HTTP REST APIs (`http://localhost:8000/api`).
- **Backend Needed?**: **YES.** Person 5 runs backend locally in `PIPELINE_MODE=mock`.
- **Deliverable**: React/TypeScript planning interface and 2D canvas layout viewer.

#### PERSON 6 (Blender / 3D Procedural):
- **Local Requirements**: Git, Blender 3.6 LTS or 4.x with bundled Python environment.
- **Database Needed?**: **NO.** Direct PostgreSQL access is prohibited.
- **Backend Needed?**: **YES (or exported JSON file).** Consumes `GET /api/layouts/{layoutId}/blueprint`.
- **Deliverable**: Procedural 3D campus generation script importing Contract 9 Blueprint JSON.

---

### 16.11 Shared Database vs. Local Database

- **Option A — Shared PostgreSQL Database**: All teammates connect to a shared hosted database (e.g. cloud or lab server). Enables shared project data but risks data collisions during test runs.
- **Option B — Local PostgreSQL Container (Recommended & Default)**: Each developer runs their own local Docker container (`archopt-postgres`) on port 5433.
- **Repository Default**: The repository code is configured for **Option B (Local Container)**. If the team chooses a shared database, update `DATABASE_URL` in `.env`.

---

### 16.12 Test Data Classifications

Teammates must strictly distinguish between three data tiers:
1. **Real Application Data**: Persisted in PostgreSQL when creating projects and running layout runs via the actual API or frontend.
2. **Test Fixture Data**: Created and destroyed on the fly by `pytest` in `backend/tests/*`. Does not pollute development data.
3. **Mock Pipeline Data**: Pre-calculated, contract-compliant layout candidates generated by `mock_generate()` when `PIPELINE_MODE=mock`.
   > [!WARNING]
   > Mock layouts are provided for frontend and Blender decoupling. **Do not mistake mock data for real GNN/optimizer outputs.**

---

### 16.13 First 30-Minute Onboarding Checklist

Complete this checklist within 30 minutes of cloning the repository:
- [ ] 1. Clone repository: `git clone https://github.com/jyotydivya/ArchOpt.git`
- [ ] 2. Checkout your feature branch: `git checkout -b feature/p<N>-<name>`
- [ ] 3. Create virtual environment: `python -m venv .venv` and activate it.
- [ ] 4. Install dependencies: `pip install -r requirements.txt`
- [ ] 5. Copy configuration: `cp .env.example .env`
- [ ] 6. Start PostgreSQL container: `docker run --name archopt-postgres -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=campus_planner -p 5433:5432 -d postgres:15`
- [ ] 7. Apply migrations: `python -m alembic upgrade head`
- [ ] 8. Verify migration status: `python -m alembic current` $\rightarrow$ `001_initial_schema (head)`
- [ ] 9. Run test suite: `python -m pytest backend/tests -q` $\rightarrow$ `70 passed`
- [ ] 10. Start server: `python -m uvicorn backend.main:app --port 8000`
- [ ] 11. Open Swagger at `http://localhost:8000/docs` and test `POST /api/auth/register`.

---

### 16.14 Troubleshooting Guide

| Problem / Symptom | Likely Cause | Solution |
|---|---|---|
| `connection to server at "localhost", port 5433 failed` | PostgreSQL container is not running | Run `docker start archopt-postgres` or check `docker ps`. |
| `ValidationError: 1 validation error for Settings SECRET_KEY` | Missing `SECRET_KEY` in environment | Copy `.env.example` to `.env` or export `SECRET_KEY="your_secret_key"`. |
| `alembic.util.exc.CommandError: Can't locate revision` | Outdated migration tree | Run `git pull origin main` and check `alembic/versions/`. |
| `HTTP 401 UNAUTHORIZED` | Missing or expired JWT token | Call `POST /api/auth/login` and attach header `Authorization: Bearer <token>`. |
| `HTTP 403 FORBIDDEN` | Accessing resource owned by another user | Ensure token matches the user who created the project/layout. |
| `HTTP 404 PROJECT_NOT_FOUND` / `LAYOUT_NOT_FOUND` | Non-existent ID or wrong user | Verify entity ID and ownership. |
| `HTTP 422 GENERATION_FAILED` | `PIPELINE_MODE=real` but P1/P2/P3 failed | Check if `ml.dataset.graph_builder`, `ml.inference.generate`, or `optimization.optimizer` raised an exception. |
| `ModuleNotFoundError: No module named 'ml'` | Upstream ML package not yet created | Keep `PIPELINE_MODE=mock` until P1/P2 submit their code. |
| CORS errors in Frontend | Frontend port not in `CORS_ORIGINS` | Add frontend URL to `CORS_ORIGINS` in `backend/config.py`. |

---

### 16.15 Git Collaboration & Coordination Rules

1. **Pull Latest Main**: Always run `git pull origin main` before starting a work session.
2. **One Branch Per Feature**: Work in `feature/p<N>-<feature-name>`.
3. **Contract Modification Protocol**:
   If Person 1, 2, or 3 requires a change to a data contract, they **must not edit backend contracts directly**. They must report:
   - Specific field change requested
   - Technical reason
   - Affected Data Contract (e.g. Contract 5, 6, or 8)
   - Downstream impact
   - Request approval from Person 4 and the project lead before merging.
4. **Pre-Push Validation**: Always run `pytest backend/tests -q` before pushing commits.

---

### 16.16 Ten Integration Checkpoints

| Checkpoint | Milestone | Owner | Input | Expected Output | Verification Command | Blocking Condition |
|:---:|---|:---:|---|---|---|---|
| **CP 1** | Repository Cloned & Verified | All | Git clone | Clean environment | `python -m pytest backend/tests -q` | Must pass 70/70 tests |
| **CP 2** | Database & Alembic Verified | P4 | Migrations | 8 tables in PostgreSQL | `python -m alembic current` | Must show `001_initial_schema (head)` |
| **CP 3** | REST APIs in MOCK Mode | P4 / P5 | Mock layout run | Top-5 layouts generated | `POST /api/projects/{id}/layout-runs` | Blocks P5/P6 if failing |
| **CP 4** | P1 Graph Builder Delivery | P1 | `campus_data: dict` | Contract 5 `CampusGraph` | Unit test in `ml/dataset/tests/` | Blocks Person 2 |
| **CP 5** | P2 GNN Generator Delivery | P2 | `CampusGraph` | 100 `CandidateLayout` objects | Unit test in `ml/inference/tests/` | Blocks Person 3 |
| **CP 6** | P3 NSGA-II Optimizer Delivery | P3 | 100 candidates + constraints | Top-5 `RankedLayout` objects | Unit test in `optimization/tests/` | Blocks REAL pipeline |
| **CP 7** | Backend REAL Mode Integration | P4 | `PIPELINE_MODE=real` | Real layouts stored in DB | `POST /layout-runs` in REAL mode | Blocks final system test |
| **CP 8** | Frontend Complete Workflow | P5 | Backend REST APIs | Full UI planning workflow | Manual flow through React UI | Blocks end-to-end demo |
| **CP 9** | Blender 3D Procedural Delivery | P6 | Contract 9 Blueprint | 3D Campus model & render | Blender headless execution test | Blocks final visual demo |
| **CP 10**| Final System Acceptance | All | Full system | Complete pipeline execution | Full test suite + live demo | Project completion |

---

### 16.17 Final "New Developer" Quickstart

#### IF YOU JUST JOINED ARCHOPT, DO THIS:
1. Clone repo: `git clone https://github.com/jyotydivya/ArchOpt.git && cd ArchOpt`
2. Set up venv: `python -m venv .venv` and activate it.
3. Install dependencies: `pip install -r requirements.txt`
4. Create `.env`: `cp .env.example .env`
5. Start PostgreSQL container: `docker run --name archopt-postgres -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=campus_planner -p 5433:5432 -d postgres:15`
6. Run migrations: `python -m alembic upgrade head`
7. Verify baseline tests: `python -m pytest backend/tests -q` (Must show 70 passed).
8. Start backend: `python -m uvicorn backend.main:app --port 8000`
9. Open `http://localhost:8000/docs` to inspect the 17 live REST endpoints.
10. Read your person-specific guide in this document and implement ONLY your owned module!

#### Architectural Responsibility & Dependency Matrix

| Teammate | Needs Direct PostgreSQL? | Needs Backend Running? | Depends on P1? | Depends on P2? | Depends on P3? | Primary Deliverable / Output |
|:---:|:---:|:---:|:---:|:---:|:---:|---|
| **Person 1** | **NO** | Optional (can use mock dict) | — | No | No | `build_graph()` $\rightarrow$ Contract 5 `CampusGraph` |
| **Person 2** | **NO** | Optional | **YES** | — | No | `generate_candidates()` $\rightarrow$ Contract 6 `CandidateLayout[]` |
| **Person 3** | **NO** | Optional | No | **YES** | — | `optimize_layouts()` $\rightarrow$ Contract 8 `RankedLayout[]` |
| **Person 4** | **YES** | **YES (Owner)** | Eventually | Eventually | Eventually | 17 REST APIs, DB schema, ML Bridge, Orchestration |
| **Person 5** | **NO** | **YES (in MOCK mode)** | No | No | No | React UI, 2D Canvas viewer, Plan comparison |
| **Person 6** | **NO (Prohibited)** | **YES (or JSON file)** | No | No | No | Blender procedural 3D campus & render (.png) |

