import uuid
from fastapi.testclient import TestClient

from backend.database import SessionLocal
from backend.main import app
from backend.models.user import User
from backend.schemas.layout import LayoutDetailResponse, LayoutListResponse, LayoutSummarySchema


def _unique_email(prefix: str = "phase7") -> str:
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


def _setup_full_project_with_run(client, headers, top_k: int = 5):
    # 1. Project
    project = client.post(
        "/api/projects",
        json={"name": "Campus Phase 7", "description": "Phase 7 test project"},
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
    run_data = run_resp.json()

    return project, [b1, b2], run_data


def test_layout_endpoints_require_authentication():
    client = TestClient(app)
    # List endpoint
    resp1 = client.get("/api/projects/1/layouts")
    assert resp1.status_code == 401
    assert resp1.json()["detail"] == "Not authenticated"

    # Detail endpoint
    resp2 = client.get("/api/layouts/1")
    assert resp2.status_code == 401
    assert resp2.json()["detail"] == "Not authenticated"


def test_get_project_layouts_missing_project_returns_404():
    client, token, email = _register_and_login()
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = client.get("/api/projects/999999/layouts", headers=headers)
        assert resp.status_code == 404, resp.text
        assert resp.json()["detail"] == "PROJECT_NOT_FOUND"
    finally:
        _cleanup_user(email)


def test_get_layout_detail_missing_layout_returns_404():
    client, token, email = _register_and_login()
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = client.get("/api/layouts/999999", headers=headers)
        assert resp.status_code == 404, resp.text
        assert resp.json()["detail"] == "LAYOUT_NOT_FOUND"
    finally:
        _cleanup_user(email)


def test_get_project_layouts_cross_user_forbidden_403():
    client_a, token_a, email_a = _register_and_login()
    client_b, token_b, email_b = _register_and_login()
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    try:
        project_a, _, _ = _setup_full_project_with_run(client_a, headers_a, top_k=2)

        # User B attempts to access User A's project layouts
        resp = client_b.get(f"/api/projects/{project_a['id']}/layouts", headers=headers_b)
        assert resp.status_code == 403, resp.text
        assert resp.json()["detail"] == "FORBIDDEN"
    finally:
        _cleanup_user(email_a)
        _cleanup_user(email_b)


def test_get_layout_detail_cross_user_forbidden_403():
    client_a, token_a, email_a = _register_and_login()
    client_b, token_b, email_b = _register_and_login()
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    try:
        project_a, _, _ = _setup_full_project_with_run(client_a, headers_a, top_k=2)

        # Get layouts for User A to find valid layout ID
        list_resp = client_a.get(f"/api/projects/{project_a['id']}/layouts", headers=headers_a)
        assert list_resp.status_code == 200
        layout_id = list_resp.json()["layouts"][0]["id"]

        # User B attempts to access User A's layout detail
        resp = client_b.get(f"/api/layouts/{layout_id}", headers=headers_b)
        assert resp.status_code == 403, resp.text
        assert resp.json()["detail"] == "FORBIDDEN"
    finally:
        _cleanup_user(email_a)
        _cleanup_user(email_b)


def test_get_project_layouts_empty_when_no_runs():
    client, token, email = _register_and_login()
    headers = {"Authorization": f"Bearer {token}"}
    try:
        project = client.post(
            "/api/projects",
            json={"name": "Empty Project", "description": "No runs yet"},
            headers=headers,
        ).json()

        resp = client.get(f"/api/projects/{project['id']}/layouts", headers=headers)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body == {"layouts": []}
    finally:
        _cleanup_user(email)


def test_successful_project_layout_retrieval_and_schema():
    client, token, email = _register_and_login()
    headers = {"Authorization": f"Bearer {token}"}
    try:
        project, _, run_data = _setup_full_project_with_run(client, headers, top_k=5)

        resp = client.get(f"/api/projects/{project['id']}/layouts", headers=headers)
        assert resp.status_code == 200, resp.text
        body = resp.json()

        # Validate with Pydantic model
        validated = LayoutListResponse.model_validate(body)
        assert len(validated.layouts) == 5

        # Check ranking and structure
        for idx, l in enumerate(validated.layouts):
            assert l.rank == idx + 1
            assert l.feasible is True
            assert isinstance(l.id, int)
            assert l.metrics.land_utilization > 0
            assert l.metrics.green_ratio >= 0
            assert l.metrics.constraint_score == 1.0

        # Check camelCase serialized representation in raw dict
        first_layout = body["layouts"][0]
        assert "landUtilization" in first_layout["metrics"]
        assert "greenRatio" in first_layout["metrics"]
        assert "parkingRatio" in first_layout["metrics"]
        assert "accessibilityScore" in first_layout["metrics"]
        assert "roadEfficiency" in first_layout["metrics"]
        assert "constraintScore" in first_layout["metrics"]
    finally:
        _cleanup_user(email)


def test_successful_layout_detail_retrieval_and_schema():
    client, token, email = _register_and_login()
    headers = {"Authorization": f"Bearer {token}"}
    try:
        project, buildings, run_data = _setup_full_project_with_run(client, headers, top_k=3)

        list_resp = client.get(f"/api/projects/{project['id']}/layouts", headers=headers)
        layout_id = list_resp.json()["layouts"][0]["id"]

        resp = client.get(f"/api/layouts/{layout_id}", headers=headers)
        assert resp.status_code == 200, resp.text
        body = resp.json()

        # Validate with Pydantic schema
        validated = LayoutDetailResponse.model_validate(body)
        assert validated.id == layout_id
        assert validated.rank == 1
        assert validated.feasible is True

        # Site dimensions
        assert body["site"]["width"] == 300.0
        assert body["site"]["height"] == 300.0

        # Buildings list (Contract 6/7 candidate positions only)
        assert len(body["buildings"]) == len(buildings)
        for b in body["buildings"]:
            assert "buildingId" in b
            assert "x" in b
            assert "y" in b
            assert "rotation" in b
            assert "name" not in b
            assert "type" not in b
            assert "zone" not in b
            assert "width" not in b
            assert "depth" not in b
            assert "height" not in b
            assert "floorCount" not in b

        # Contract arrays
        assert body["roads"] == []
        assert body["greenAreas"] == []
        assert body["parkingAreas"] == []

        # Entrances
        assert len(body["entrances"]) == 1
        assert body["entrances"][0]["x"] == 150.0
        assert body["entrances"][0]["y"] == 0.0
        assert body["entrances"][0]["width"] == 10.0

        # Metrics
        assert "landUtilization" in body["metrics"]
        assert "greenRatio" in body["metrics"]
    finally:
        _cleanup_user(email)


def test_field_hygiene_no_internal_db_fields_leaked():
    client, token, email = _register_and_login()
    headers = {"Authorization": f"Bearer {token}"}
    try:
        project, _, _ = _setup_full_project_with_run(client, headers, top_k=2)

        # 1. Inspect list endpoint
        list_resp = client.get(f"/api/projects/{project['id']}/layouts", headers=headers)
        list_body = list_resp.json()

        forbidden_db_keys = {
            "run_id", "runId",
            "project_id", "projectId",
            "layout_json", "layoutJson",
            "metrics_json", "metricsJson",
            "created_at", "createdAt",
        }

        for item in list_body["layouts"]:
            for key in forbidden_db_keys:
                assert key not in item, f"Internal DB field '{key}' leaked in layout summary!"

        # 2. Inspect detail endpoint
        layout_id = list_body["layouts"][0]["id"]
        detail_resp = client.get(f"/api/layouts/{layout_id}", headers=headers)
        detail_body = detail_resp.json()

        for key in forbidden_db_keys:
            assert key not in detail_body, f"Internal DB field '{key}' leaked in layout detail!"
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


def test_phase7_routes_registered_once():
    seen = {}
    for method, path in _iter_route_pairs(app.router):
        seen[(method, path)] = seen.get((method, path), 0) + 1

    # Phase 7 endpoints registered exactly once
    assert seen.get(("GET", "/api/projects/{project_id}/layouts"), 0) == 1
    assert seen.get(("GET", "/api/layouts/{layout_id}"), 0) == 1


