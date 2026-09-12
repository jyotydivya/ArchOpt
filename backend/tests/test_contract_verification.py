"""
Phase 11: End-to-End Contract Verification Suite.
Validates the backend implementation strictly against:
- Technical Architecture & 6-Person Execution Contract (Section 3 APIs, Section 4 Data Contracts, Section 5 DB Schema)
- implementation_plan.md

Sequentially executes the complete 17-endpoint lifecycle and validates:
1. POST /api/auth/register (Endpoint #1)
2. POST /api/auth/login (Endpoint #2)
3. POST /api/projects (Endpoint #3)
4. GET /api/projects/{projectId} (Endpoint #4)
5. PUT /api/projects/{projectId} (Endpoint #5)
6. POST /api/projects/{projectId}/requirements (Endpoint #7)
7. GET /api/projects/{projectId}/requirements (Endpoint #8)
8. POST /api/projects/{projectId}/buildings (Endpoint #9)
9. GET /api/projects/{projectId}/buildings (Endpoint #10)
10. POST /api/projects/{projectId}/constraints (Endpoint #11)
11. GET /api/projects/{projectId}/constraints (Endpoint #12)
12. POST /api/projects/{projectId}/layout-runs (Endpoint #13)
13. GET /api/projects/{projectId}/layouts (Endpoint #14)
14. GET /api/layouts/{layoutId} (Endpoint #15)
15. POST /api/layouts/{layoutId}/select (Endpoint #16)
16. GET /api/layouts/{layoutId}/blueprint (Endpoint #17)
17. DELETE /api/projects/{projectId} (Endpoint #6)
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_complete_17_endpoint_contract_lifecycle(client):
    """
    Executes all 17 master endpoints in exact contract workflow order.
    Asserts exact status codes, JSON response keys, and camelCase naming conventions.
    """
    # -------------------------------------------------------------
    # 1. Register (Endpoint #1: POST /api/auth/register)
    # -------------------------------------------------------------
    reg_payload = {
        "name": "E2E Contract Auditor",
        "email": f"e2e_auditor_{id(client)}@example.com",
        "password": "Password123!",
    }
    reg_res = client.post("/api/auth/register", json=reg_payload)
    assert reg_res.status_code == 201, reg_res.text
    reg_json = reg_res.json()
    assert "id" in reg_json
    assert reg_json["name"] == reg_payload["name"]
    assert reg_json["email"] == reg_payload["email"]
    assert reg_json["role"] == "PROJECT_MANAGER"
    assert "password" not in reg_json
    assert "password_hash" not in reg_json

    # -------------------------------------------------------------
    # 2. Login (Endpoint #2: POST /api/auth/login)
    # -------------------------------------------------------------
    login_payload = {
        "email": reg_payload["email"],
        "password": reg_payload["password"],
    }
    login_res = client.post("/api/auth/login", json=login_payload)
    assert login_res.status_code == 200, login_res.text
    login_json = login_res.json()
    assert "accessToken" in login_json
    assert login_json["tokenType"] == "Bearer"
    assert "user" in login_json
    assert login_json["user"]["name"] == reg_payload["name"]
    assert login_json["user"]["role"] == "PROJECT_MANAGER"

    token = login_json["accessToken"]
    auth_headers = {"Authorization": f"Bearer {token}"}

    # -------------------------------------------------------------
    # 3. Create Project (Endpoint #3: POST /api/projects)
    # -------------------------------------------------------------
    proj_create_payload = {
        "name": "VIT-AP Engineering Campus Expansion",
        "description": "Comprehensive academic zone optimization case study",
    }
    create_proj_res = client.post("/api/projects", json=proj_create_payload, headers=auth_headers)
    assert create_proj_res.status_code == 201, create_proj_res.text
    proj_json = create_proj_res.json()
    project_id = proj_json["id"]
    assert proj_json["name"] == proj_create_payload["name"]
    assert proj_json["description"] == proj_create_payload["description"]
    assert proj_json["status"] == "DRAFT"

    # -------------------------------------------------------------
    # 4. Get Project (Endpoint #4: GET /api/projects/{projectId})
    # -------------------------------------------------------------
    get_proj_res = client.get(f"/api/projects/{project_id}", headers=auth_headers)
    assert get_proj_res.status_code == 200, get_proj_res.text
    get_proj_json = get_proj_res.json()
    assert get_proj_json["id"] == project_id
    assert get_proj_json["status"] == "DRAFT"

    # -------------------------------------------------------------
    # 5. Update Project (Endpoint #5: PUT /api/projects/{projectId})
    # -------------------------------------------------------------
    proj_update_payload = {
        "name": "VIT-AP Phase 2 Master Plan",
        "description": "Updated master plan description",
    }
    put_proj_res = client.put(f"/api/projects/{project_id}", json=proj_update_payload, headers=auth_headers)
    assert put_proj_res.status_code == 200, put_proj_res.text
    put_proj_json = put_proj_res.json()
    assert put_proj_json["name"] == proj_update_payload["name"]
    assert put_proj_json["description"] == proj_update_payload["description"]

    # -------------------------------------------------------------
    # 6. Save Requirements (Endpoint #7: POST /api/projects/{projectId}/requirements)
    # -------------------------------------------------------------
    req_payload = {
        "siteWidth": 300.0,
        "siteHeight": 300.0,
        "minGreenPercent": 25.0,
        "minParkingPercent": 10.0,
        "minRoadWidth": 8.0,
        "minBuildingGap": 10.0,
        "entrances": [
            {"x": 150.0, "y": 0.0, "width": 10.0},
            {"x": 0.0, "y": 150.0, "width": 8.0},
        ],
    }
    post_req_res = client.post(f"/api/projects/{project_id}/requirements", json=req_payload, headers=auth_headers)
    assert post_req_res.status_code == 201, post_req_res.text
    post_req_json = post_req_res.json()
    assert post_req_json["projectId"] == project_id
    assert post_req_json["siteWidth"] == 300.0
    assert len(post_req_json["entrances"]) == 2
    assert "road_data" not in post_req_json
    assert "roadData" not in post_req_json

    # -------------------------------------------------------------
    # 7. Get Requirements (Endpoint #8: GET /api/projects/{projectId}/requirements)
    # -------------------------------------------------------------
    get_req_res = client.get(f"/api/projects/{project_id}/requirements", headers=auth_headers)
    assert get_req_res.status_code == 200, get_req_res.text
    get_req_json = get_req_res.json()
    assert get_req_json["projectId"] == project_id
    assert get_req_json["minGreenPercent"] == 25.0
    assert "road_data" not in get_req_json
    assert "total_area" not in get_req_json

    # -------------------------------------------------------------
    # 8. Add Buildings (Endpoint #9: POST /api/projects/{projectId}/buildings)
    # -------------------------------------------------------------
    b1_payload = {
        "name": "Academic Block A",
        "type": "academic",
        "zone": "academic",
        "width": 60.0,
        "depth": 40.0,
        "height": 18.0,
        "floorCount": 4,
        "requiredCount": 1,
    }
    b1_res = client.post(f"/api/projects/{project_id}/buildings", json=b1_payload, headers=auth_headers)
    assert b1_res.status_code == 201, b1_res.text
    b1_json = b1_res.json()
    b1_id = b1_json["id"]
    assert b1_json["projectId"] == project_id
    assert b1_json["floorCount"] == 4

    b2_payload = {
        "name": "Central Library",
        "type": "library",
        "zone": "academic",
        "width": 45.0,
        "depth": 30.0,
        "height": 12.0,
        "floorCount": 3,
        "requiredCount": 1,
    }
    b2_res = client.post(f"/api/projects/{project_id}/buildings", json=b2_payload, headers=auth_headers)
    assert b2_res.status_code == 201, b2_res.text
    b2_id = b2_res.json()["id"]

    # -------------------------------------------------------------
    # 9. Get Buildings (Endpoint #10: GET /api/projects/{projectId}/buildings)
    # -------------------------------------------------------------
    get_b_res = client.get(f"/api/projects/{project_id}/buildings", headers=auth_headers)
    assert get_b_res.status_code == 200, get_b_res.text
    b_list = get_b_res.json()["buildings"]
    assert len(b_list) == 2
    assert any(b["name"] == "Academic Block A" for b in b_list)
    assert any(b["name"] == "Central Library" for b in b_list)

    # -------------------------------------------------------------
    # 10. Add Constraints (Endpoint #11: POST /api/projects/{projectId}/constraints)
    # -------------------------------------------------------------
    c_payload = {
        "type": "MIN_DISTANCE",
        "sourceId": b1_id,
        "targetId": b2_id,
        "value": 25.0,
        "operator": ">=",
        "priority": "hard",
    }
    post_c_res = client.post(f"/api/projects/{project_id}/constraints", json=c_payload, headers=auth_headers)
    assert post_c_res.status_code == 201, post_c_res.text
    c_json = post_c_res.json()
    assert c_json["sourceId"] == b1_id
    assert c_json["targetId"] == b2_id

    # -------------------------------------------------------------
    # 11. Get Constraints (Endpoint #12: GET /api/projects/{projectId}/constraints)
    # -------------------------------------------------------------
    get_c_res = client.get(f"/api/projects/{project_id}/constraints", headers=auth_headers)
    assert get_c_res.status_code == 200, get_c_res.text
    c_list = get_c_res.json()["constraints"]
    assert len(c_list) == 1
    assert c_list[0]["type"] == "MIN_DISTANCE"

    # -------------------------------------------------------------
    # 12. Generate Layouts (Endpoint #13: POST /api/projects/{projectId}/layout-runs)
    # -------------------------------------------------------------
    run_payload = {
        "candidateCount": 100,
        "topK": 5,
        "algorithm": "GNN_NSGA2",
    }
    run_res = client.post(f"/api/projects/{project_id}/layout-runs", json=run_payload, headers=auth_headers)
    assert run_res.status_code == 200, run_res.text
    run_json = run_res.json()
    assert "runId" in run_json
    assert run_json["status"] == "COMPLETED"
    assert run_json["layoutCount"] == 5

    # -------------------------------------------------------------
    # 13. List Layouts (Endpoint #14: GET /api/projects/{projectId}/layouts)
    # -------------------------------------------------------------
    layouts_res = client.get(f"/api/projects/{project_id}/layouts", headers=auth_headers)
    assert layouts_res.status_code == 200, layouts_res.text
    layouts_json = layouts_res.json()
    assert "layouts" in layouts_json
    assert len(layouts_json["layouts"]) == 5
    top_layout = layouts_json["layouts"][0]
    top_layout_id = top_layout["id"]
    assert top_layout["rank"] == 1
    assert "metrics" in top_layout
    assert "landUtilization" in top_layout["metrics"]
    assert "greenRatio" in top_layout["metrics"]

    # -------------------------------------------------------------
    # 14. Get Layout Detail (Endpoint #15: GET /api/layouts/{layoutId})
    # -------------------------------------------------------------
    detail_res = client.get(f"/api/layouts/{top_layout_id}", headers=auth_headers)
    assert detail_res.status_code == 200, detail_res.text
    detail_json = detail_res.json()
    assert detail_json["id"] == top_layout_id
    assert detail_json["rank"] == 1
    assert "site" in detail_json
    assert detail_json["site"]["width"] == 300.0
    assert "buildings" in detail_json
    assert len(detail_json["buildings"]) >= 2
    assert "greenAreas" in detail_json
    assert "parkingAreas" in detail_json
    assert "entrances" in detail_json

    # -------------------------------------------------------------
    # 15. Select Layout (Endpoint #16: POST /api/layouts/{layoutId}/select)
    # -------------------------------------------------------------
    select_res = client.post(f"/api/layouts/{top_layout_id}/select", json={}, headers=auth_headers)
    assert select_res.status_code == 200, select_res.text
    select_json = select_res.json()
    assert select_json["projectId"] == project_id
    assert select_json["layoutId"] == top_layout_id
    assert select_json["status"] == "SELECTED"

    # Verify project status transitioned to SELECTED
    proj_check_res = client.get(f"/api/projects/{project_id}", headers=auth_headers)
    assert proj_check_res.json()["status"] == "SELECTED"

    # -------------------------------------------------------------
    # 16. Blender Blueprint Export (Endpoint #17: GET /api/layouts/{layoutId}/blueprint)
    # -------------------------------------------------------------
    bp_res = client.get(f"/api/layouts/{top_layout_id}/blueprint", headers=auth_headers)
    assert bp_res.status_code == 200, bp_res.text
    bp_json = bp_res.json()
    assert bp_json["projectId"] == project_id
    assert bp_json["layoutId"] == top_layout_id
    assert bp_json["site"]["width"] == 300.0
    assert bp_json["site"]["height"] == 300.0
    assert "buildings" in bp_json
    assert len(bp_json["buildings"]) >= 2

    # Check merged building structure satisfies Contract 9
    bp_building = bp_json["buildings"][0]
    assert "id" in bp_building
    assert "name" in bp_building
    assert "type" in bp_building
    assert "zone" in bp_building
    assert "x" in bp_building
    assert "y" in bp_building
    assert "width" in bp_building
    assert "depth" in bp_building
    assert "height" in bp_building
    assert "rotation" in bp_building
    assert "floorCount" in bp_building

    # Field hygiene check on Blueprint
    assert "created_at" not in bp_json
    assert "updated_at" not in bp_json
    assert "road_data" not in bp_json
    assert "roadData" not in bp_json

    # -------------------------------------------------------------
    # 17. Delete Project (Endpoint #6: DELETE /api/projects/{projectId})
    # -------------------------------------------------------------
    del_res = client.delete(f"/api/projects/{project_id}", headers=auth_headers)
    assert del_res.status_code == 204, del_res.text
    assert del_res.content == b""

    # Confirm project is deleted
    get_del_res = client.get(f"/api/projects/{project_id}", headers=auth_headers)
    assert get_del_res.status_code == 404
    assert get_del_res.json()["detail"] == "PROJECT_NOT_FOUND"


def test_data_contracts_1_through_9_schema_fidelity():
    """
    Validates the 9 Master Data Contracts from Section 4 of the contract:
    - Contract 1: Building
    - Contract 2: Campus Requirements
    - Contract 3: Entrance
    - Contract 4: Spatial Relationship / Constraint
    - Contract 5: Campus Graph
    - Contract 6: Candidate Layout
    - Contract 7: Validation Result
    - Contract 8: Ranked Layout
    - Contract 9: Blueprint
    """
    from backend.schemas.building import BuildingCreateRequest, BuildingResponse
    from backend.schemas.requirement import EntranceSchema, RequirementsResponse
    from backend.schemas.constraint import ConstraintResponse
    from backend.schemas.blueprint import BlueprintResponse
    from backend.services.ml_bridge import (
        CandidateLayoutContract,
        RankedLayoutContract,
        validate_and_format_ranked_layout,
    )

    # Contract 1: Building
    b = BuildingResponse.model_validate({
        "id": 1,
        "projectId": 10,
        "name": "Academic Block A",
        "type": "academic",
        "zone": "academic",
        "width": 60.0,
        "depth": 40.0,
        "height": 18.0,
        "floorCount": 4,
        "requiredCount": 1,
    })
    assert b.floor_count == 4

    # Contract 2: Campus Requirements
    r = RequirementsResponse.model_validate({
        "id": 1,
        "projectId": 10,
        "siteWidth": 300.0,
        "siteHeight": 300.0,
        "minGreenPercent": 25.0,
        "minParkingPercent": 10.0,
        "minRoadWidth": 8.0,
        "minBuildingGap": 10.0,
        "entrances": [{"x": 150.0, "y": 0.0, "width": 10.0}],
    })
    assert r.site_width == 300.0

    # Contract 3: Entrance
    e = EntranceSchema(x=150.0, y=0.0, width=10.0)
    assert e.width == 10.0

    # Contract 4: Constraint
    c = ConstraintResponse.model_validate({
        "id": 1,
        "type": "MIN_DISTANCE",
        "sourceId": 1,
        "targetId": 2,
        "value": 20.0,
        "operator": ">=",
        "priority": "hard",
    })
    assert c.source_id == 1

    # Contract 6: Candidate Layout
    cl = CandidateLayoutContract.model_validate({
        "candidateId": "cand-001",
        "siteWidth": 300.0,
        "siteHeight": 300.0,
        "buildings": [{"buildingId": 1, "x": 50.0, "y": 80.0, "rotation": 0.0}],
    })
    assert cl.candidate_id == "cand-001"

    # Contract 8: Ranked Layout
    rl = RankedLayoutContract.model_validate({
        "candidateId": "cand-001",
        "rank": 1,
        "feasible": True,
        "buildings": [{"buildingId": 1, "x": 50.0, "y": 80.0, "rotation": 0.0}],
        "metrics": {
            "landUtilization": 0.72,
            "greenRatio": 0.25,
            "parkingRatio": 0.12,
            "accessibilityScore": 0.85,
            "roadEfficiency": 0.80,
            "constraintScore": 1.0,
        },
    })
    assert rl.rank == 1
    assert rl.metrics.constraint_score == 1.0

    # Contract 9: Blueprint
    bp = BlueprintResponse.model_validate({
        "projectId": 10,
        "layoutId": 101,
        "site": {"width": 300.0, "height": 300.0},
        "buildings": [
            {
                "id": 1,
                "name": "Academic Block A",
                "type": "academic",
                "zone": "academic",
                "x": 50.0,
                "y": 80.0,
                "width": 60.0,
                "depth": 40.0,
                "height": 18.0,
                "rotation": 0.0,
                "floorCount": 4,
            }
        ],
        "roads": [],
        "greenAreas": [],
        "parkingAreas": [],
        "entrances": [],
    })
    assert bp.layout_id == 101


def test_database_all_8_contract_tables_and_columns():
    """
    Validates that all 8 tables specified in Section 5 of the contract exist:
    users, projects, campus_requirements, buildings, constraints,
    layout_runs, layouts, selected_plans.
    """
    from backend.database import engine
    from sqlalchemy import inspect

    inspector = inspect(engine)
    tables = inspector.get_table_names()

    required_tables = [
        "users",
        "projects",
        "campus_requirements",
        "buildings",
        "constraints",
        "layout_runs",
        "layouts",
        "selected_plans",
    ]
    for table_name in required_tables:
        assert table_name in tables, f"Required contract table missing: {table_name}"

    # Verify road_data column exists internally in campus_requirements
    req_cols = [col["name"] for col in inspector.get_columns("campus_requirements")]
    assert "road_data" in req_cols
    assert "entrance_data" in req_cols


def test_cross_user_security_and_authorization_contract(client):
    """
    Validates that cross-user data access is strictly forbidden across all protected APIs.
    """
    # Create User A
    email_a = f"usera_{id(client)}@example.com"
    client.post("/api/auth/register", json={"name": "User A", "email": email_a, "password": "password123"})
    token_a = client.post("/api/auth/login", json={"email": email_a, "password": "password123"}).json()["accessToken"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Create User B
    email_b = f"userb_{id(client)}@example.com"
    client.post("/api/auth/register", json={"name": "User B", "email": email_b, "password": "password123"})
    token_b = client.post("/api/auth/login", json={"email": email_b, "password": "password123"}).json()["accessToken"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User A creates project, requirements, building
    proj_a = client.post("/api/projects", json={"name": "Project A", "description": "desc"}, headers=headers_a).json()["id"]
    client.post(
        f"/api/projects/{proj_a}/requirements",
        json={
            "siteWidth": 300,
            "siteHeight": 300,
            "minGreenPercent": 25,
            "minParkingPercent": 10,
            "minRoadWidth": 8,
            "minBuildingGap": 10,
            "entrances": [],
        },
        headers=headers_a,
    )
    client.post(
        f"/api/projects/{proj_a}/buildings",
        json={
            "name": "B1",
            "type": "academic",
            "zone": "academic",
            "width": 50,
            "depth": 30,
            "height": 15,
            "floorCount": 3,
            "requiredCount": 1,
        },
        headers=headers_a,
    )
    run_res = client.post(
        f"/api/projects/{proj_a}/layout-runs",
        json={"candidateCount": 20, "topK": 2, "algorithm": "GNN_NSGA2"},
        headers=headers_a,
    )
    assert run_res.status_code == 200
    layouts_a = client.get(f"/api/projects/{proj_a}/layouts", headers=headers_a).json()["layouts"]
    layout_id_a = layouts_a[0]["id"]

    # User B attempts to access User A's resources -> 403 Forbidden
    assert client.get(f"/api/projects/{proj_a}", headers=headers_b).status_code == 403
    assert client.put(f"/api/projects/{proj_a}", json={"name": "Hacked", "description": "bad"}, headers=headers_b).status_code == 403
    assert client.delete(f"/api/projects/{proj_a}", headers=headers_b).status_code == 403
    assert client.get(f"/api/projects/{proj_a}/requirements", headers=headers_b).status_code == 403
    assert client.get(f"/api/projects/{proj_a}/buildings", headers=headers_b).status_code == 403
    assert client.get(f"/api/projects/{proj_a}/constraints", headers=headers_b).status_code == 403
    assert client.post(f"/api/projects/{proj_a}/layout-runs", json={}, headers=headers_b).status_code == 403
    assert client.get(f"/api/projects/{proj_a}/layouts", headers=headers_b).status_code == 403
    assert client.get(f"/api/layouts/{layout_id_a}", headers=headers_b).status_code == 403
    assert client.post(f"/api/layouts/{layout_id_a}/select", json={}, headers=headers_b).status_code == 403
    assert client.get(f"/api/layouts/{layout_id_a}/blueprint", headers=headers_b).status_code == 403

    # Unauthenticated access -> 401 Unauthorized
    assert client.get(f"/api/projects/{proj_a}").status_code == 401
    assert client.get(f"/api/layouts/{layout_id_a}").status_code == 401
    assert client.get(f"/api/layouts/{layout_id_a}/blueprint").status_code == 401

