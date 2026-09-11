# Revised Implementation Plan: Person 4 - Backend, Database & System Orchestration

## Core Principles
1. **Single Source of Truth**: The uploaded **Technical Architecture & 6-Person Execution Contract** project plan is the absolute source of truth.
2. **Zero Inventions**: No new REST endpoints, fields, entities, database tables, or contract response formats will be created.
3. **Strict Contract Boundaries**: Contractual requirements (Section 3 APIs, Section 4 Data Contracts, Section 5 DB Schemas) are strictly distinguished from backend implementation choices (framework defaults, JWT TTL, DB driver, migrations tool).
4. **No Silent ML Fallback**: If real P1/P2/P3 modules are installed/active and fail during execution or return invalid data, the backend will **NOT** silently fall back to the mock pipeline. Real pipeline failures must raise `422 GENERATION_FAILED` or `500 INTERNAL_SERVER_ERROR`.

---

## Contractual Requirements vs. Engineering Implementation Decisions

### A. Contractual Requirements (Fixed by Specification)
* **Master REST APIs**: Exactly the 17 endpoints listed in Section 3.
* **Data Contracts 1–9**: Exact JSON structures for `Building`, `CampusRequirements`, `Entrance`, `SpatialRelationship`, `CampusGraph`, `CandidateLayout`, `ValidationResult`, `RankedLayout`, and `Blueprint`.
* **Database Entities**: Exactly the 8 tables defined in Section 5 (`users`, `projects`, `campus_requirements`, `buildings`, `constraints`, `layout_runs`, `layouts`, `selected_plans`) with specified column names and types.
* **ML Interfaces**:
  * P1: `build_graph(campus_data: dict) -> CampusGraph`
  * P2: `generate_candidates(campus_graph: CampusGraph, num_candidates: int) -> list[CandidateLayout]`
  * P3: `optimize_layouts(candidates: list[CandidateLayout], requirements: dict, constraints: list[dict], top_k: int) -> list[RankedLayout]`

### B. Engineering Implementation Decisions (Not Specified in Contract)
* **JWT Settings**: Expiration time (default 24h), secret key resolution (`SECRET_KEY` environment variable), algorithm (`HS256`).
* **`road_data` Storage**: Preserved in database `campus_requirements` table as `JSONB`. Defaulted to `[]` in the database; **never** exposed as an API field on `/requirements` endpoints since the contract specification for `POST`/`GET` `/api/projects/{projectId}/requirements` does not contain a `road_data` property.
* **Optional Development Health Check**: `GET /` is an un-versioned development health check, **not** counted as one of the 17 master APIs.
* **Database Options**: Use of Alembic for migrations, PostgreSQL driver `psycopg2-binary`, foreign key delete behavior (RESTRICT vs CASCADE as appropriate).
* **Mock Pipeline**: Employs static/predetermined contract-compliant candidate objects for local frontend/Blender testing without simulating ML logic.

---

## Master API Contract Verification Matrix (Exhaustive 17 Endpoints)

| # | Method | Endpoint Path | Auth Required | Request Body | Response Status | Response Body Schema | Error Statuses & Messages |
|---|--------|---------------|---------------|--------------|-----------------|----------------------|---------------------------|
| 1 | `POST` | `/api/auth/register` | None | `{"name": "...", "email": "...", "password": "..."}` | `201 Created` | `{"id": 1, "name": "...", "email": "...", "role": "PROJECT_MANAGER"}` | `400 VALIDATION_ERROR`<br>`409 EMAIL_ALREADY_EXISTS` |
| 2 | `POST` | `/api/auth/login` | None | `{"email": "...", "password": "..."}` | `200 OK` | `{"accessToken": "...", "tokenType": "Bearer", "user": {"id": 1, "name": "...", "role": "PROJECT_MANAGER"}}` | `400 VALIDATION_ERROR`<br>`401 INVALID_CREDENTIALS` |
| 3 | `POST` | `/api/projects` | `Bearer <JWT>` | `{"name": "...", "description": "..."}` | `201 Created` | `{"id": 1, "name": "...", "description": "...", "status": "DRAFT"}` | `400 VALIDATION_ERROR`<br>`401 UNAUTHORIZED` |
| 4 | `GET` | `/api/projects/{projectId}` | `Bearer <JWT>` | None | `200 OK` | `{"id": 1, "name": "...", "description": "...", "status": "DRAFT"}` | `401 UNAUTHORIZED`<br>`403 FORBIDDEN`<br>`404 PROJECT_NOT_FOUND` |
| 5 | `PUT` | `/api/projects/{projectId}` | `Bearer <JWT>` | `{"name": "...", "description": "..."}` | `200 OK` | `{"id": 1, "name": "...", "description": "...", "status": "DRAFT"}` | `400 VALIDATION_ERROR`<br>`401 UNAUTHORIZED`<br>`403 FORBIDDEN`<br>`404 PROJECT_NOT_FOUND` |
| 6 | `DELETE` | `/api/projects/{projectId}` | `Bearer <JWT>` | None | `204 No Content` | None | `401 UNAUTHORIZED`<br>`403 FORBIDDEN`<br>`404 PROJECT_NOT_FOUND` |
| 7 | `POST` | `/api/projects/{projectId}/requirements` | `Bearer <JWT>` | `{"siteWidth": 300, "siteHeight": 300, "minGreenPercent": 25, "minParkingPercent": 10, "minRoadWidth": 8, "minBuildingGap": 10, "entrances": [{"x": 150, "y": 0, "width": 10}]}` | `201 Created` | `{"id": 1, "projectId": 1, "siteWidth": 300, "siteHeight": 300, "minGreenPercent": 25, "minParkingPercent": 10, "minRoadWidth": 8, "minBuildingGap": 10, "entrances": [...]}` | `400 VALIDATION_ERROR`<br>`401 UNAUTHORIZED`<br>`403 FORBIDDEN`<br>`404 PROJECT_NOT_FOUND` |
| 8 | `GET` | `/api/projects/{projectId}/requirements` | `Bearer <JWT>` | None | `200 OK` | `{"projectId": 1, "siteWidth": 300, "siteHeight": 300, "minGreenPercent": 25, "minParkingPercent": 10, "minRoadWidth": 8, "minBuildingGap": 10, "entrances": [...]}` | `401 UNAUTHORIZED`<br>`403 FORBIDDEN`<br>`404 PROJECT_NOT_FOUND` |
| 9 | `POST` | `/api/projects/{projectId}/buildings` | `Bearer <JWT>` | `{"name": "Academic Block A", "type": "academic", "zone": "academic", "width": 60, "depth": 40, "height": 18, "floorCount": 4, "requiredCount": 1}` | `201 Created` | `{"id": 1, "projectId": 1, "name": "Academic Block A", "type": "academic", "zone": "academic", "width": 60, "depth": 40, "height": 18, "floorCount": 4, "requiredCount": 1}` | `400 VALIDATION_ERROR`<br>`401 UNAUTHORIZED`<br>`403 FORBIDDEN`<br>`404 PROJECT_NOT_FOUND` |
| 10 | `GET` | `/api/projects/{projectId}/buildings` | `Bearer <JWT>` | None | `200 OK` | `{"buildings": [{"id": 1, "name": "Academic Block A", "type": "academic", "zone": "academic", "width": 60, "depth": 40, "height": 18, "floorCount": 4, "requiredCount": 1}]}` | `401 UNAUTHORIZED`<br>`403 FORBIDDEN`<br>`404 PROJECT_NOT_FOUND` |
| 11 | `POST` | `/api/projects/{projectId}/constraints` | `Bearer <JWT>` | `{"type": "MIN_DISTANCE", "sourceId": 1, "targetId": 5, "value": 100, "operator": ">=", "priority": "hard"}` | `201 Created` | `{"id": 1, "type": "MIN_DISTANCE", "sourceId": 1, "targetId": 5, "value": 100, "operator": ">=", "priority": "hard"}` | `400 VALIDATION_ERROR`<br>`401 UNAUTHORIZED`<br>`403 FORBIDDEN`<br>`404 PROJECT_NOT_FOUND` |
| 12 | `GET` | `/api/projects/{projectId}/constraints` | `Bearer <JWT>` | None | `200 OK` | `{"constraints": [{"id": 1, "type": "MIN_DISTANCE", "sourceId": 1, "targetId": 5, "value": 100, "operator": ">=", "priority": "hard"}]}` | `401 UNAUTHORIZED`<br>`403 FORBIDDEN`<br>`404 PROJECT_NOT_FOUND` |
| 13 | `POST` | `/api/projects/{projectId}/layout-runs` | `Bearer <JWT>` | `{"candidateCount": 100, "topK": 5, "algorithm": "GNN_NSGA2"}` | `200 OK` | `{"runId": 12, "status": "COMPLETED", "layoutCount": 5}` | `400 INVALID_REQUIREMENTS`<br>`404 PROJECT_NOT_FOUND`<br>`422 GENERATION_FAILED`<br>`500 INTERNAL_SERVER_ERROR` |
| 14 | `GET` | `/api/projects/{projectId}/layouts` | `Bearer <JWT>` | None | `200 OK` | `{"layouts": [{"id": 101, "rank": 1, "feasible": true, "metrics": {"landUtilization": 0.72, "greenRatio": 0.25, "parkingRatio": 0.12, "accessibilityScore": 0.84, "roadEfficiency": 0.78, "constraintScore": 1.0}}]}` | `401 UNAUTHORIZED`<br>`403 FORBIDDEN`<br>`404 PROJECT_NOT_FOUND` |
| 15 | `GET` | `/api/layouts/{layoutId}` | `Bearer <JWT>` | None | `200 OK` | `{"id": 101, "rank": 1, "feasible": true, "site": {"width": 300, "height": 300}, "buildings": [], "roads": [], "greenAreas": [], "parkingAreas": [], "entrances": [], "metrics": {}}` | `401 UNAUTHORIZED`<br>`404 LAYOUT_NOT_FOUND` |
| 16 | `POST` | `/api/layouts/{layoutId}/select` | `Bearer <JWT>` | `{}` | `200 OK` | `{"projectId": 1, "layoutId": 101, "status": "SELECTED"}` | `401 UNAUTHORIZED`<br>`404 LAYOUT_NOT_FOUND` |
| 17 | `GET` | `/api/layouts/{layoutId}/blueprint` | `Bearer <JWT>` | None | `200 OK` | `{"projectId": 1, "layoutId": 101, "site": {"width": 300, "height": 300}, "buildings": [{"id": 1, "name": "Academic Block A", "type": "academic", "zone": "academic", "x": 75, "y": 120, "width": 60, "depth": 40, "height": 18, "rotation": 0, "floorCount": 4}], "roads": [], "greenAreas": [], "parkingAreas": [], "entrances": []}` | `401 UNAUTHORIZED`<br>`404 LAYOUT_NOT_FOUND` |

---

## Detailed 12-Phase Implementation Plan

---

### Phase 1: Project Structure and Configuration
* **Objective**: Initialize backend project directory, FastAPI app, database session factory, CORS middleware, and environment settings.
* **Files to Create**:
  * `backend/__init__.py`
  * `backend/main.py`
  * `backend/config.py`
  * `backend/database.py`
  * `requirements.txt`
* **Files to Modify**: `README.md`
* **Database Changes**: None.
* **Pydantic Schemas Required**: None.
* **API Endpoints Involved**: `GET /` (Optional development health check; **not** counted toward the 17 master APIs).
* **Service/Repository Responsibilities**: Configuration manager (`Settings`), DB session dependency (`get_db`).
* **Dependencies on Other People**: None.
* **Dummy Input**: `GET http://localhost:8000/`
* **Expected Output**: `{"status": "ok", "app": "AI Campus Planner Backend"}`
* **Tests Required**: Server startup test, database session creation test.
* **Acceptance Criteria**: Server boots without error and connects to PostgreSQL.
* **Potential Integration Risks**: Incorrect DB URL syntax or missing environment variable fallbacks.

---

### Phase 2: Database and SQLAlchemy Models
* **Objective**: Define ORM models for all 8 tables specified in Section 5 of the contract.
* **Files to Create**:
  * `backend/models/__init__.py`
  * `backend/models/user.py` (`users`)
  * `backend/models/project.py` (`projects`)
  * `backend/models/requirement.py` (`campus_requirements`)
  * `backend/models/building.py` (`buildings`)
  * `backend/models/constraint.py` (`constraints`)
  * `backend/models/layout_run.py` (`layout_runs`)
  * `backend/models/layout.py` (`layouts`)
  * `backend/models/selected_plan.py` (`selected_plans`)
  * `alembic.ini` & `alembic/` migration scripts.
* **Files to Modify**: `backend/database.py`
* **Database Changes**:
  * Tables created: `users`, `projects`, `campus_requirements`, `buildings`, `constraints`, `layout_runs`, `layouts`, `selected_plans`.
  * Preserves `road_data JSONB` in `campus_requirements` as an internal DB column (defaulting to `[]`).
* **Pydantic Schemas Required**: None.
* **API Endpoints Involved**: None directly.
* **Service/Repository Responsibilities**: SQLAlchemy Base mappings. Foreign key behavior (RESTRICT by default; documented as an engineering decision).
* **Dependencies on Other People**: None.
* **Dummy Input**: Execution of `alembic upgrade head`.
* **Expected Output**: 8 PostgreSQL tables created matching Section 5 schema exactly.
* **Tests Required**: Contract compliance tests comparing SQLAlchemy table structures against Section 5 schema.
* **Acceptance Criteria**: 100% field name and type match with Section 5 DB contract.
* **Potential Integration Risks**: Schema naming divergence (snake_case DB names vs camelCase API schemas).

---

### Phase 3: Pydantic Schemas
* **Objective**: Create Pydantic validation schemas for all 17 master endpoints and 9 Master Data Contracts.
* **Files to Create**:
  * `backend/schemas/auth.py`
  * `backend/schemas/project.py`
  * `backend/schemas/requirement.py`
  * `backend/schemas/building.py`
  * `backend/schemas/constraint.py`
  * `backend/schemas/layout.py`
  * `backend/schemas/blueprint.py`
* **Files to Modify**: None.
* **Database Changes**: None.
* **Pydantic Schemas Required**: All schemas listed in the Master API Contract Verification Matrix above.
* **API Endpoints Involved**: All 17 Master APIs.
* **Service/Repository Responsibilities**: Data validation, camelCase serialization matching Section 3 payloads. No undocumented fields allowed.
* **Dependencies on Other People**: Guarantees contract compatibility for P5 (Frontend) and P6 (Blender).
* **Dummy Input**: Exact JSON payloads from Section 3.1–3.17 of project plan.
* **Expected Output**: Validated Pydantic models. Rejection of invalid types with `400 VALIDATION_ERROR`.
* **Tests Required**: Contract validation tests using the exact Section 3 sample JSON inputs.
* **Acceptance Criteria**: Zero field missing, zero extra fields added.
* **Potential Integration Risks**: Pydantic v2 `alias_generator` misconfigurations for camelCase fields.

---

### Phase 4: Authentication and Authorization
* **Objective**: Build password hashing, JWT issuance/validation, and Bearer token dependency.
* **Files to Create**:
  * `backend/security.py`
  * `backend/api/auth.py`
* **Files to Modify**: `backend/main.py`
* **Database Changes**: None.
* **Pydantic Schemas Required**: Auth request/response schemas.
* **API Endpoints Involved**:
  * `POST /api/auth/register` (Endpoint #1)
  * `POST /api/auth/login` (Endpoint #2)
* **Service/Repository Responsibilities**: Password hashing with `bcrypt`, JWT token generation, `get_current_user` auth dependency.
* **Dependencies on Other People**: P5 Frontend uses `/api/auth/login` token for all subsequent calls.
* **Dummy Input**: Register & login JSON payloads from Section 3.1 & 3.2.
* **Expected Output**: Token response per Section 3.2.
* **Tests Required**: Registration success test, duplicate email test (409), login success test, invalid credentials test (401).
* **Acceptance Criteria**: Strictly enforces `Authorization: Bearer <token>` for protected endpoints.
* **Potential Integration Risks**: Mismatched header capitalization or missing `Bearer` prefix.

---

### Phase 5: Project / Requirements / Buildings / Constraints APIs
* **Objective**: Build CRUD management endpoints for project configuration.
* **Files to Create**:
  * `backend/api/projects.py`
  * `backend/api/requirements.py`
  * `backend/api/buildings.py`
  * `backend/api/constraints.py`
  * `backend/repositories/project_repository.py`
* **Files to Modify**: `backend/main.py`
* **Database Changes**: Writes to `projects`, `campus_requirements`, `buildings`, `constraints`.
* **Pydantic Schemas Required**: Schemas for Endpoints #3–#12.
* **API Endpoints Involved**: Endpoints #3 through #12 in Master API Matrix.
* **Service/Repository Responsibilities**: Database persistence and user ownership verification (`project.user_id == current_user.id`).
* **Dependencies on Other People**: Supplies project setup data for P1 & P5.
* **Dummy Input**: Section 3.3–3.12 request bodies.
* **Expected Output**: Statuses `201`, `200`, `204` matching Section 3 documentation.
* **Tests Required**: Contract validation tests for Endpoints #3–#12, project authorization checks (403).
* **Acceptance Criteria**: Response structures match Section 3 specification verbatim.
* **Potential Integration Risks**: Foreign key constraint violations when referencing missing project IDs.

---

### Phase 6: Mock Layout-Generation Orchestration
* **Objective**: Implement `POST /api/projects/{projectId}/layout-runs` with a contract-compatible mock generator that returns pre-determined layouts without implementing ML algorithms.
* **Files to Create**:
  * `backend/services/orchestrator.py`
  * `backend/api/layouts.py`
* **Files to Modify**: `backend/main.py`
* **Database Changes**: Inserts into `layout_runs` and `layouts`.
* **Pydantic Schemas Required**: `LayoutRunCreateRequest`, `LayoutRunCreateResponse`.
* **API Endpoints Involved**: `POST /api/projects/{projectId}/layout-runs` (Endpoint #13).
* **Service/Repository Responsibilities**:
  * Validate requirements & buildings exist for project.
  * Return contract-compliant mock layout list (`mock_generate()`).
  * Save run record to `layout_runs` and layout records to `layouts`.
* **Dependencies on Other People**: P5 Frontend layout generation trigger.
* **Dummy Input**: `POST /api/projects/1/layout-runs` body `{"candidateCount": 100, "topK": 5, "algorithm": "GNN_NSGA2"}`
* **Expected Output**: `200 OK` body `{"runId": 12, "status": "COMPLETED", "layoutCount": 5}`.
* **Tests Required**: Mock generation execution test, missing requirements test (`400 INVALID_REQUIREMENTS`), project missing test (`404 PROJECT_NOT_FOUND`).
* **Acceptance Criteria**: Saves 5 valid mock layouts in DB satisfying Contract 8.
* **Potential Integration Risks**: Mock layouts containing building IDs that do not exist in the project's building configuration.

---

### Phase 7: Layout Retrieval
* **Objective**: Implement layout listing and detail retrieval endpoints.
* **Files to Create**: None (extend `backend/api/layouts.py`).
* **Files to Modify**: `backend/api/layouts.py`
* **Database Changes**: Reads `layouts` table.
* **Pydantic Schemas Required**: Schemas for Endpoints #14 & #15.
* **API Endpoints Involved**:
  * `GET /api/projects/{projectId}/layouts` (Endpoint #14)
  * `GET /api/layouts/{layoutId}` (Endpoint #15)
* **Service/Repository Responsibilities**: Query layouts by `project_id` or `layoutId`, format metrics & buildings arrays.
* **Dependencies on Other People**: P5 Frontend 2D Viewer.
* **Dummy Input**: `GET /api/projects/1/layouts`, `GET /api/layouts/101`
* **Expected Output**: Response JSON matching Section 3.14 & 3.15 contract.
* **Tests Required**: Contract verification tests for Endpoints #14 & #15.
* **Acceptance Criteria**: Accurate metrics JSON and candidate building coordinates returned.
* **Potential Integration Risks**: Serialization errors when converting JSONB columns to Pydantic models.

---

### Phase 8: Plan Selection
* **Objective**: Implement plan selection endpoint.
* **Files to Create**: None (extend `backend/api/layouts.py`).
* **Files to Modify**: `backend/api/layouts.py`
* **Database Changes**: Insert row into `selected_plans`, update `projects.status = "SELECTED"`.
* **Pydantic Schemas Required**: `LayoutSelectResponse` schema for Endpoint #16.
* **API Endpoints Involved**: `POST /api/layouts/{layoutId}/select` (Endpoint #16).
* **Service/Repository Responsibilities**: Record layout selection and update project workflow status.
* **Dependencies on Other People**: P5 Frontend.
* **Dummy Input**: `POST /api/layouts/101/select` body `{}`
* **Expected Output**: `200 OK` body `{"projectId": 1, "layoutId": 101, "status": "SELECTED"}`
* **Tests Required**: Plan selection test, invalid layout ID test (`404`).
* **Acceptance Criteria**: `selected_plans` row inserted and project status updated.
* **Potential Integration Risks**: Attempting selection on a non-existent layout ID.

---

### Phase 9: Blueprint Export
* **Objective**: Implement 3D Blender Blueprint export endpoint matching Contract 9.
* **Files to Create**: `backend/services/blueprint_service.py`
* **Files to Modify**: `backend/api/layouts.py`
* **Database Changes**: Reads `layouts`, `buildings`, `campus_requirements`, `projects`.
* **Pydantic Schemas Required**: `BlueprintResponse` schema for Endpoint #17.
* **API Endpoints Involved**: `GET /api/layouts/{layoutId}/blueprint` (Endpoint #17).
* **Service/Repository Responsibilities**: Merge candidate layout building positions (`x, y, rotation`) with building metadata (`width, depth, height, floorCount, name, type, zone`) and project site boundaries (`width, height`, `entrances`).
* **Dependencies on Other People**: P6 Blender 3D Engineer.
* **Dummy Input**: `GET /api/layouts/101/blueprint`
* **Expected Output**: Section 3.17 & Contract 9 compliant JSON body.
* **Tests Required**: Blueprint schema contract verification test.
* **Acceptance Criteria**: Output JSON matches Contract 9 structure verbatim.
* **Potential Integration Risks**: Mismatch between building IDs in candidate layout and database building table.

---

### Phase 10: P1/P2/P3 Integration & Error Handling
* **Objective**: Connect real Python modules (`build_graph`, `generate_candidates`, `optimize_layouts`) when active, with explicit failure handling.
* **Files to Create**: `backend/services/ml_bridge.py`
* **Files to Modify**: `backend/services/orchestrator.py`
* **Database Changes**: None.
* **Pydantic Schemas Required**: Python contracts for `CampusGraph`, `CandidateLayout`, `RankedLayout`.
* **API Endpoints Involved**: `POST /api/projects/{projectId}/layout-runs` (Endpoint #13).
* **Service/Repository Responsibilities**:
  * Execute real P1 $\rightarrow$ P2 $\rightarrow$ P3 pipeline when enabled/installed.
  * **Strict Failure Rule**: If real ML modules fail or return invalid/malformed data, raise `422 GENERATION_FAILED` or `500 INTERNAL_SERVER_ERROR`. **Never** silently fall back to mock generation.
  * Mock mode is used **only** when explicitly configured as the active pipeline mode.
* **Dependencies on Other People**: P1 (`ml/dataset/graph_builder.py`), P2 (`ml/inference/generate.py`), P3 (`optimization/optimizer.py`).
* **Dummy Input**: Execution call against installed ML modules.
* **Expected Output**: Saved Pareto-ranked layouts or explicit HTTP `422 GENERATION_FAILED` error response.
* **Tests Required**: Real pipeline execution test, pipeline failure surfacing test (`422 GENERATION_FAILED`), mock mode execution test.
* **Acceptance Criteria**: Real ML failures are properly reported to the user without masking symptoms.
* **Potential Integration Risks**: Incompatible function arguments or unhandled exceptions thrown by ML modules.

---

### Phase 11: End-to-End Testing (Contract Verification Suite)
* **Objective**: Execute automated test suite validating the backend against the project contract (rather than testing arbitrary Copilot code).
* **Files to Create**: `backend/tests/test_contract_verification.py`
* **Files to Modify**: None.
* **Database Changes**: Isolated test database setup/teardown.
* **Pydantic Schemas Required**: All schemas.
* **API Endpoints Involved**: All 17 Master APIs.
* **Service/Repository Responsibilities**: Verify contract compliance across entire user workflow.
* **Dependencies on Other People**: None.
* **Dummy Input**: Sequential API test runner.
* **Expected Output**: 100% test pass rate verifying contract compliance.
* **Tests Required**: Full 17-endpoint contract verification suite (Auth $\rightarrow$ Project $\rightarrow$ Requirements $\rightarrow$ Buildings $\rightarrow$ Constraints $\rightarrow$ Layout Run $\rightarrow$ Layout List $\rightarrow$ Layout Detail $\rightarrow$ Select $\rightarrow$ Blueprint).
* **Acceptance Criteria**: Every test case directly asserts against Section 3 API specs and Section 4 Data Contracts.
* **Potential Integration Risks**: Stale test DB data between test runs.

---

### Phase 12: Final Person 4 Audit
* **Objective**: Conduct final verification audit of code, documentation, OpenAPI spec, and deliverables.
* **Files to Create**: `docs/person_4_audit_report.md`
* **Files to Modify**: `README.md`
* **Database Changes**: None.
* **Pydantic Schemas Required**: None.
* **API Endpoints Involved**: All 17 Master APIs.
* **Service/Repository Responsibilities**: OpenAPI spec review (`/openapi.json`), deliverable check against Section 2 Person 4 Definition of Done.
* **Dependencies on Other People**: Handoff APIs to P5 & P6.
* **Dummy Input**: `/openapi.json`
* **Expected Output**: Completed Audit Report confirming 0 contract violations.
* **Tests Required**: Final `pytest` run.
* **Acceptance Criteria**: OpenAPI spec matches Section 3 specification exactly.
* **Potential Integration Risks**: None.

---

## Verification Plan

### Automated Contract Tests
* Run contract-verification test suite:
  ```bash
  pytest backend/tests/test_contract_verification.py -v
  ```

### Manual Verification
* Run OpenAPI schema comparison tool against Section 3 Master API Specification.
* Verify database schema using PostgreSQL `\d` commands.
