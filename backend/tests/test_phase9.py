import uuid
from fastapi.testclient import TestClient

from backend.database import SessionLocal
from backend.main import app
from backend.models.user import User
from backend.schemas.blueprint import BlueprintResponse


def _unique_email(prefix: str = "phase9") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}@example.com"


def _cleanup_user(email: str) -> None:
    with SessionLocal() as db:
        user = db.query(User).filter(User.email == email).first()
        if user:
            db.delete(user)
            db.commit()


def _register_and_login(email: str = None):
    email = email or _unique_email("user")
    payload = {"name": "Student", "email": email, "password": "password123"}
    client = TestClient(app)
    reg = client.post("/api/auth/register", json=payload)
    assert reg.status_code == 201, reg.text
    login = client.post("/api/auth/login", json={"email": email, "password": "password123"})
    assert login.status_code == 200, login.text
    token = login.json()["accessToken"]
    return client, token, email


def _setup_full_project_with_run(client, headers, top_k: int = 3):
    # 1. Project
    project = client.post(
        "/api/projects",
        json={"name": "Campus Phase 9", "description": "Phase 9 test project"},
        headers=headers,
    ).json()

    # 2. Requirements
    req_payload = {
        "siteWidth": 300.0,
        "siteHeight": 300.0,
        "minGreenPercent": 25.0,
        "minParkingPercent": 10.0,
        "minRoadWidth": 8.0,
        "minBuildingGap": 10.0,
        "entrances": [{"x": 150.0, "y": 0.0, "width": 10.0}],
    }
    client.post(f"/api/projects/{project['id']}/requirements", json=req_payload, headers=headers)

    # 3. Buildings
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
    b2_payload = {
        "name": "Hostel Block 1",
        "type": "residential",
        "zone": "residential",
        "width": 50.0,
        "depth": 30.0,
        "height": 15.0,
        "floorCount": 3,
        "requiredCount": 1,
    }
    b1 = client.post(f"/api/projects/{project['id']}/buildings", json=b1_payload, headers=headers).json()
    b2 = client.post(f"/api/projects/{project['id']}/buildings", json=b2_payload, headers=headers).json()

    # 4. Trigger Layout Run
    run_resp = client.post(
        f"/api/projects/{project['id']}/layout-runs",
        json={"candidateCount": 100, "topK": top_k},
        headers=headers,
    )
    assert run_resp.status_code == 200, run_resp.text

    # 5. Get generated layouts
    layouts_resp = client.get(f"/api/projects/{project['id']}/layouts", headers=headers)
    assert layouts_resp.status_code == 200, layouts_resp.text
    layouts = layouts_resp.json()["layouts"]

    return project, [b1, b2], layouts


def test_blueprint_endpoint_requires_authentication():
    client = TestClient(app)
    resp = client.get("/api/layouts/1/blueprint")
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Not authenticated"


def test_blueprint_missing_layout_returns_404():
    client, token, email = _register_and_login()
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = client.get("/api/layouts/999999/blueprint", headers=headers)
        assert resp.status_code == 404, resp.text
        assert resp.json()["detail"] == "LAYOUT_NOT_FOUND"
    finally:
        _cleanup_user(email)


def test_blueprint_cross_user_forbidden_403():
    client_a, token_a, email_a = _register_and_login()
    client_b, token_b, email_b = _register_and_login()
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    try:
        project_a, _, layouts_a = _setup_full_project_with_run(client_a, headers_a)
        layout_id = layouts_a[0]["id"]

        # User B attempts to access User A's blueprint
        resp = client_b.get(f"/api/layouts/{layout_id}/blueprint", headers=headers_b)
        assert resp.status_code == 403, resp.text
        assert resp.json()["detail"] == "FORBIDDEN"
    finally:
        _cleanup_user(email_a)
        _cleanup_user(email_b)


def test_successful_blueprint_retrieval_and_schema_validation():
    client, token, email = _register_and_login()
    headers = {"Authorization": f"Bearer {token}"}
    try:
        project, buildings, layouts = _setup_full_project_with_run(client, headers)
        layout_id = layouts[0]["id"]

        resp = client.get(f"/api/layouts/{layout_id}/blueprint", headers=headers)
        assert resp.status_code == 200, resp.text
        body = resp.json()

        # Validate through Pydantic schema
        validated = BlueprintResponse.model_validate(body)
        assert validated.project_id == project["id"]
        assert validated.layout_id == layout_id

        # Site checks
        assert validated.site.width == 300.0
        assert validated.site.height == 300.0

        # Buildings checks
        assert len(validated.buildings) == len(buildings)
        for b in validated.buildings:
            assert b.id in [b1["id"] for b1 in buildings]
            assert b.width in [60.0, 50.0]
            assert b.depth in [40.0, 30.0]
            assert b.floor_count in [4, 3]
            assert b.x >= 0.0
            assert b.y >= 0.0

        # Contract arrays
        assert validated.roads == []
        assert validated.green_areas == []
        assert validated.parking_areas == []

        # Entrances
        assert len(validated.entrances) == 1
        assert validated.entrances[0].x == 150.0
        assert validated.entrances[0].y == 0.0
        assert validated.entrances[0].width == 10.0
    finally:
        _cleanup_user(email)


def test_blueprint_json_camelcase_naming_contract():
    client, token, email = _register_and_login()
    headers = {"Authorization": f"Bearer {token}"}
    try:
        project, _, layouts = _setup_full_project_with_run(client, headers)
        layout_id = layouts[0]["id"]

        resp = client.get(f"/api/layouts/{layout_id}/blueprint", headers=headers)
        assert resp.status_code == 200, resp.text
        body = resp.json()

        # Top-level required camelCase keys
        assert "projectId" in body
        assert "layoutId" in body
        assert "site" in body
        assert "buildings" in body
        assert "roads" in body
        assert "greenAreas" in body
        assert "parkingAreas" in body
        assert "entrances" in body

        # Building required camelCase keys
        first_building = body["buildings"][0]
        assert "floorCount" in first_building
        assert "floor_count" not in first_building
    finally:
        _cleanup_user(email)


def test_blueprint_field_hygiene_no_internal_db_fields():
    client, token, email = _register_and_login()
    headers = {"Authorization": f"Bearer {token}"}
    try:
        project, _, layouts = _setup_full_project_with_run(client, headers)
        layout_id = layouts[0]["id"]

        resp = client.get(f"/api/layouts/{layout_id}/blueprint", headers=headers)
        assert resp.status_code == 200, resp.text
        body = resp.json()

        forbidden_keys = {
            "run_id", "runId",
            "layout_json", "layoutJson",
            "metrics_json", "metricsJson",
            "created_at", "createdAt",
            "updated_at", "updatedAt",
            "selected_by", "selectedBy",
            "selected_at", "selectedAt",
        }

        for key in forbidden_keys:
            assert key not in body, f"Internal DB field '{key}' leaked at blueprint top level!"

        for b in body["buildings"]:
            for key in forbidden_keys:
                assert key not in b, f"Internal DB field '{key}' leaked in blueprint building!"
    finally:
        _cleanup_user(email)


def test_blueprint_retrieval_after_layout_selection():
    client, token, email = _register_and_login()
    headers = {"Authorization": f"Bearer {token}"}
    try:
        project, _, layouts = _setup_full_project_with_run(client, headers)
        layout_id = layouts[0]["id"]

        # Select layout
        sel_resp = client.post(f"/api/layouts/{layout_id}/select", json={}, headers=headers)
        assert sel_resp.status_code == 200

        # Retrieve blueprint for the selected layout
        bp_resp = client.get(f"/api/layouts/{layout_id}/blueprint", headers=headers)
        assert bp_resp.status_code == 200
        body = bp_resp.json()
        assert body["projectId"] == project["id"]
        assert body["layoutId"] == layout_id
        assert len(body["buildings"]) >= 1
    finally:
        _cleanup_user(email)


def _iter_route_pairs(router, prefix=""):
    for route in getattr(router, "routes", []):
        if hasattr(route, "original_router"):
            inc_prefix = getattr(getattr(route, "include_context", None), "prefix", "")
            yield from _iter_route_pairs(route.original_router, prefix=prefix + inc_prefix)
        elif hasattr(route, "routes"):
            yield from _iter_route_pairs(route, prefix=prefix)
        elif getattr(route, "path", None):
            methods = tuple(sorted(getattr(route, "methods", set())))
            if methods:
                for method in methods:
                    yield method, prefix + route.path


def test_phase9_and_previous_routes_uniqueness():
    seen = {}
    for method, path in _iter_route_pairs(app.router):
        seen[(method, path)] = seen.get((method, path), 0) + 1

    # Phase 9 endpoint registered exactly once
    assert seen.get(("GET", "/api/layouts/{layout_id}/blueprint"), 0) == 1

    # Phase 8 endpoint registered exactly once
    assert seen.get(("POST", "/api/layouts/{layout_id}/select"), 0) == 1

    # Phase 7 endpoints registered exactly once
    assert seen.get(("GET", "/api/projects/{project_id}/layouts"), 0) == 1
    assert seen.get(("GET", "/api/layouts/{layout_id}"), 0) == 1

    # Phase 6 endpoint registered exactly once
    assert seen.get(("POST", "/api/projects/{project_id}/layout-runs"), 0) == 1

    # No future/speculative endpoints exist
    for method, path in seen:
        assert not path.startswith("/api/phase10"), f"Unauthorized future endpoint {path} detected!"
