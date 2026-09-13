import uuid
from fastapi.testclient import TestClient

from backend.database import SessionLocal
from backend.main import app
from backend.models.project import Project
from backend.models.selected_plan import SelectedPlan
from backend.models.user import User
from backend.schemas.layout import LayoutSelectResponse


def _unique_email(prefix: str = "phase8") -> str:
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
        json={"name": "Campus Phase 8", "description": "Phase 8 test project"},
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
    client.post(f"/api/projects/{project['id']}/buildings", json=b1_payload, headers=headers)

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

    return project, layouts


def test_select_layout_requires_authentication():
    client = TestClient(app)
    resp = client.post("/api/layouts/1/select", json={})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Not authenticated"


def test_select_layout_missing_layout_returns_404():
    client, token, email = _register_and_login()
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = client.post("/api/layouts/999999/select", json={}, headers=headers)
        assert resp.status_code == 404, resp.text
        assert resp.json()["detail"] == "LAYOUT_NOT_FOUND"
    finally:
        _cleanup_user(email)


def test_select_layout_cross_user_forbidden_403():
    client_a, token_a, email_a = _register_and_login()
    client_b, token_b, email_b = _register_and_login()
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    try:
        project_a, layouts_a = _setup_full_project_with_run(client_a, headers_a)
        layout_id = layouts_a[0]["id"]

        # User B attempts to select User A's layout
        resp = client_b.post(f"/api/layouts/{layout_id}/select", json={}, headers=headers_b)
        assert resp.status_code == 403, resp.text
        assert resp.json()["detail"] == "FORBIDDEN"

        # Verify no SelectedPlan record was created
        with SessionLocal() as db:
            selected_count = (
                db.query(SelectedPlan)
                .filter(SelectedPlan.project_id == project_a["id"])
                .count()
            )
            assert selected_count == 0

            # Verify project status unchanged
            proj = db.query(Project).filter(Project.id == project_a["id"]).first()
            assert proj.status != "SELECTED"
    finally:
        _cleanup_user(email_a)
        _cleanup_user(email_b)


def test_successful_layout_selection_and_persistence():
    client, token, email = _register_and_login()
    headers = {"Authorization": f"Bearer {token}"}
    try:
        project, layouts = _setup_full_project_with_run(client, headers)
        layout_id = layouts[0]["id"]

        # Initial project status is DRAFT
        with SessionLocal() as db:
            p_initial = db.query(Project).filter(Project.id == project["id"]).first()
            assert p_initial.status == "DRAFT"

        # Select layout with empty body
        resp = client.post(f"/api/layouts/{layout_id}/select", json={}, headers=headers)
        assert resp.status_code == 200, resp.text
        body = resp.json()

        # Validate response schema
        validated = LayoutSelectResponse.model_validate(body)
        assert validated.project_id == project["id"]
        assert validated.layout_id == layout_id
        assert validated.status == "SELECTED"

        # Check raw serialized keys
        assert body == {
            "projectId": project["id"],
            "layoutId": layout_id,
            "status": "SELECTED",
        }

        # Check DB persistence
        with SessionLocal() as db:
            selected = (
                db.query(SelectedPlan)
                .filter(SelectedPlan.project_id == project["id"])
                .all()
            )
            assert len(selected) == 1
            assert selected[0].layout_id == layout_id
            assert selected[0].selected_at is not None

            # Check project status updated
            p_updated = db.query(Project).filter(Project.id == project["id"]).first()
            assert p_updated.status == "SELECTED"
    finally:
        _cleanup_user(email)


def test_select_layout_with_no_body():
    client, token, email = _register_and_login()
    headers = {"Authorization": f"Bearer {token}"}
    try:
        project, layouts = _setup_full_project_with_run(client, headers)
        layout_id = layouts[0]["id"]

        # Call without body
        resp = client.post(f"/api/layouts/{layout_id}/select", headers=headers)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["projectId"] == project["id"]
        assert body["layoutId"] == layout_id
        assert body["status"] == "SELECTED"
    finally:
        _cleanup_user(email)


def test_reselection_idempotency_and_switching():
    client, token, email = _register_and_login()
    headers = {"Authorization": f"Bearer {token}"}
    try:
        project, layouts = _setup_full_project_with_run(client, headers, top_k=3)
        layout_1 = layouts[0]["id"]
        layout_2 = layouts[1]["id"]

        # 1. Select layout 1
        resp1 = client.post(f"/api/layouts/{layout_1}/select", json={}, headers=headers)
        assert resp1.status_code == 200

        with SessionLocal() as db:
            plans = db.query(SelectedPlan).filter(SelectedPlan.project_id == project["id"]).all()
            assert len(plans) == 1
            assert plans[0].layout_id == layout_1
            first_selected_at = plans[0].selected_at

        # 2. Select layout 1 again (duplicate/idempotent selection)
        resp2 = client.post(f"/api/layouts/{layout_1}/select", json={}, headers=headers)
        assert resp2.status_code == 200
        assert resp2.json()["layoutId"] == layout_1

        with SessionLocal() as db:
            plans = db.query(SelectedPlan).filter(SelectedPlan.project_id == project["id"]).all()
            assert len(plans) == 1, "Duplicate selection should not create multiple rows"
            assert plans[0].layout_id == layout_1

        # 3. Switch selection to layout 2
        resp3 = client.post(f"/api/layouts/{layout_2}/select", json={}, headers=headers)
        assert resp3.status_code == 200
        assert resp3.json()["layoutId"] == layout_2

        with SessionLocal() as db:
            plans = db.query(SelectedPlan).filter(SelectedPlan.project_id == project["id"]).all()
            assert len(plans) == 1, "Replacing selection must keep exactly 1 active selected plan"
            assert plans[0].layout_id == layout_2

            p = db.query(Project).filter(Project.id == project["id"]).first()
            assert p.status == "SELECTED"
    finally:
        _cleanup_user(email)


def test_field_hygiene_no_internal_db_fields_leaked():
    client, token, email = _register_and_login()
    headers = {"Authorization": f"Bearer {token}"}
    try:
        project, layouts = _setup_full_project_with_run(client, headers)
        layout_id = layouts[0]["id"]

        resp = client.post(f"/api/layouts/{layout_id}/select", json={}, headers=headers)
        assert resp.status_code == 200
        body = resp.json()

        # Strict whitelist: response must only contain projectId, layoutId, status
        expected_keys = {"projectId", "layoutId", "status"}
        assert set(body.keys()) == expected_keys

        # Explicit blacklist
        forbidden_keys = {
            "id", "selected_by", "selectedBy", "selected_at", "selectedAt",
            "created_at", "createdAt", "updated_at", "updatedAt",
            "user_id", "userId", "run_id", "runId",
        }
        for key in forbidden_keys:
            assert key not in body, f"Internal DB field '{key}' leaked in select response!"
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


def test_phase8_route_registered_once():
    seen = {}
    for method, path in _iter_route_pairs(app.router):
        seen[(method, path)] = seen.get((method, path), 0) + 1

    # Phase 8 endpoint registered exactly once
    assert seen.get(("POST", "/api/layouts/{layout_id}/select"), 0) == 1

