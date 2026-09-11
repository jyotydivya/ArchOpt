import uuid
from fastapi.testclient import TestClient

from backend.database import SessionLocal
from backend.main import app
from backend.models.layout import Layout
from backend.models.layout_run import LayoutRun
from backend.models.user import User


def _unique_email(prefix: str = "phase6") -> str:
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


def _setup_full_project(client, headers):
    # 1. Project
    project = client.post(
        "/api/projects",
        json={"name": "VIT Expansion", "description": "Phase 6 test project"},
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

    return project, [b1, b2]


def test_layout_run_requires_authentication():
    client = TestClient(app)
    resp = client.post("/api/projects/1/layout-runs", json={"candidateCount": 100, "topK": 5})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Not authenticated"


def test_layout_run_for_missing_project_returns_404():
    client, token, email = _register_and_login()
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = client.post(
            "/api/projects/999999/layout-runs",
            json={"candidateCount": 100, "topK": 5},
            headers=headers,
        )
        assert resp.status_code == 404, resp.text
        assert resp.json()["detail"] == "PROJECT_NOT_FOUND"
    finally:
        _cleanup_user(email)


def test_layout_run_for_other_user_project_returns_403_forbidden():
    owner_client, owner_token, owner_email = _register_and_login("owner")
    other_client, other_token, other_email = _register_and_login("other")
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    other_headers = {"Authorization": f"Bearer {other_token}"}

    try:
        project, _ = _setup_full_project(owner_client, owner_headers)

        resp = other_client.post(
            f"/api/projects/{project['id']}/layout-runs",
            json={"candidateCount": 100, "topK": 5},
            headers=other_headers,
        )
        assert resp.status_code == 403, resp.text
        assert resp.json()["detail"] == "FORBIDDEN"
    finally:
        _cleanup_user(owner_email)
        _cleanup_user(other_email)


def test_layout_run_without_requirements_returns_400_invalid_requirements():
    client, token, email = _register_and_login()
    headers = {"Authorization": f"Bearer {token}"}

    try:
        # Create project only, without requirements
        project = client.post(
            "/api/projects",
            json={"name": "No Reqs Project", "description": "Testing missing reqs"},
            headers=headers,
        ).json()

        resp = client.post(
            f"/api/projects/{project['id']}/layout-runs",
            json={"candidateCount": 100, "topK": 5},
            headers=headers,
        )
        assert resp.status_code == 400, resp.text
        assert resp.json()["detail"] == "INVALID_REQUIREMENTS"
    finally:
        _cleanup_user(email)


def test_layout_run_without_buildings_returns_400_invalid_requirements():
    client, token, email = _register_and_login()
    headers = {"Authorization": f"Bearer {token}"}

    try:
        # Create project and requirements, but no buildings
        project = client.post(
            "/api/projects",
            json={"name": "No Buildings Project", "description": "Testing missing buildings"},
            headers=headers,
        ).json()

        req_payload = {
            "siteWidth": 300.0,
            "siteHeight": 300.0,
            "minGreenPercent": 25.0,
            "minParkingPercent": 10.0,
            "minRoadWidth": 8.0,
            "minBuildingGap": 10.0,
            "entrances": [],
        }
        client.post(f"/api/projects/{project['id']}/requirements", json=req_payload, headers=headers)

        resp = client.post(
            f"/api/projects/{project['id']}/layout-runs",
            json={"candidateCount": 100, "topK": 5},
            headers=headers,
        )
        assert resp.status_code == 400, resp.text
        assert resp.json()["detail"] == "INVALID_REQUIREMENTS"
    finally:
        _cleanup_user(email)


def test_successful_mock_layout_run_and_database_persistence():
    client, token, email = _register_and_login()
    headers = {"Authorization": f"Bearer {token}"}

    try:
        project, buildings = _setup_full_project(client, headers)

        payload = {
            "candidateCount": 100,
            "topK": 5,
            "algorithm": "GNN_NSGA2",
        }
        resp = client.post(
            f"/api/projects/{project['id']}/layout-runs",
            json=payload,
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()

        # Contract assertion (Section 3.13)
        assert "runId" in body
        assert isinstance(body["runId"], int)
        assert body["status"] == "COMPLETED"
        assert body["layoutCount"] == 5

        # Hygiene check: no internal snake_case fields leaked
        assert "run_id" not in body
        assert "layout_count" not in body

        # Database verification
        with SessionLocal() as db:
            run_row = db.query(LayoutRun).filter(LayoutRun.id == body["runId"]).first()
            assert run_row is not None
            assert run_row.project_id == project["id"]
            assert run_row.algorithm == "GNN_NSGA2"
            assert run_row.population_size == 100
            assert run_row.generation_count == 5
            assert run_row.status == "COMPLETED"
            assert run_row.completed_at is not None

            layout_rows = (
                db.query(Layout)
                .filter(Layout.run_id == body["runId"])
                .order_by(Layout.rank.asc())
                .all()
            )
            assert len(layout_rows) == 5

            for i, l in enumerate(layout_rows):
                rank = i + 1
                assert l.rank == rank
                assert l.feasible is True

                # layout_json check
                assert "candidateId" in l.layout_json
                assert l.layout_json["siteWidth"] == 300.0
                assert l.layout_json["siteHeight"] == 300.0
                placed_buildings = l.layout_json["buildings"]
                assert len(placed_buildings) == 2
                placed_ids = {pb["buildingId"] for pb in placed_buildings}
                expected_ids = {b["id"] for b in buildings}
                assert placed_ids == expected_ids

                # metrics_json check
                metrics = l.metrics_json
                assert "landUtilization" in metrics
                assert "greenRatio" in metrics
                assert "parkingRatio" in metrics
                assert "accessibilityScore" in metrics
                assert "roadEfficiency" in metrics
                assert metrics["constraintScore"] == 1.0
    finally:
        _cleanup_user(email)


def test_layout_run_with_custom_top_k():
    client, token, email = _register_and_login()
    headers = {"Authorization": f"Bearer {token}"}

    try:
        project, _ = _setup_full_project(client, headers)

        payload = {"candidateCount": 50, "topK": 3, "algorithm": "GNN_NSGA2"}
        resp = client.post(
            f"/api/projects/{project['id']}/layout-runs",
            json=payload,
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["layoutCount"] == 3

        with SessionLocal() as db:
            layout_rows = db.query(Layout).filter(Layout.run_id == body["runId"]).all()
            assert len(layout_rows) == 3
    finally:
        _cleanup_user(email)


def test_layout_run_with_malformed_payload_returns_400_validation_error():
    client, token, email = _register_and_login()
    headers = {"Authorization": f"Bearer {token}"}

    try:
        project, _ = _setup_full_project(client, headers)

        resp = client.post(
            f"/api/projects/{project['id']}/layout-runs",
            json={"candidateCount": "not-an-integer"},
            headers=headers,
        )
        assert resp.status_code == 400, resp.text
        assert resp.json()["detail"] == "VALIDATION_ERROR"
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


def test_phase6_route_is_registered_once():
    seen = {}
    for method, path in _iter_route_pairs(app.router):
        seen[(method, path)] = seen.get((method, path), 0) + 1

    # Phase 6 endpoint must be registered exactly once
    assert seen.get(("POST", "/api/projects/{project_id}/layout-runs"), 0) == 1



