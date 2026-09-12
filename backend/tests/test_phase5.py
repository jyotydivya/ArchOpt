import uuid

from fastapi.testclient import TestClient

from backend.database import SessionLocal
from backend.main import app
from backend.models.building import Building
from backend.models.constraint import Constraint
from backend.models.project import Project
from backend.models.requirement import CampusRequirement
from backend.models.user import User


def _unique_email(prefix: str = "phase5") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}@example.com"


def _cleanup_user(email: str) -> None:
    with SessionLocal() as db:
        other = db.query(User).filter(User.email == email).first()
        if other:
            db.delete(other)
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


def test_create_get_update_delete_project():
    client, token, email = _register_and_login()
    headers = {"Authorization": f"Bearer {token}"}
    try:
        create = client.post("/api/projects", json={"name": "Campus A", "description": "Alpha"}, headers=headers)
        assert create.status_code == 201, create.text
        project = create.json()
        assert project["name"] == "Campus A"
        assert project["status"] == "DRAFT"

        detail = client.get(f"/api/projects/{project['id']}", headers=headers)
        assert detail.status_code == 200, detail.text
        assert detail.json()["description"] == "Alpha"

        update = client.put(f"/api/projects/{project['id']}", json={"name": "Campus A Updated", "description": "Beta"}, headers=headers)
        assert update.status_code == 200, update.text
        assert update.json()["name"] == "Campus A Updated"

        delete = client.delete(f"/api/projects/{project['id']}", headers=headers)
        assert delete.status_code == 204, delete.text
    finally:
        _cleanup_user(email)


def test_requirements_create_and_get_are_contract_compliant():
    client, token, email = _register_and_login()
    headers = {"Authorization": f"Bearer {token}"}
    try:
        project = client.post("/api/projects", json={"name": "Camp Req", "description": "Reqs"}, headers=headers).json()
        req_payload = {
            "siteWidth": 300.0,
            "siteHeight": 300.0,
            "minGreenPercent": 25.0,
            "minParkingPercent": 10.0,
            "minRoadWidth": 8.0,
            "minBuildingGap": 10.0,
            "entrances": [{"x": 150.0, "y": 0.0, "width": 10.0}],
        }
        create = client.post(f"/api/projects/{project['id']}/requirements", json=req_payload, headers=headers)
        assert create.status_code == 201, create.text
        body = create.json()
        assert body["projectId"] == project["id"]
        assert body["siteWidth"] == 300.0
        assert "road_data" not in body
        assert "roadData" not in body

        get_req = client.get(f"/api/projects/{project['id']}/requirements", headers=headers)
        assert get_req.status_code == 200, get_req.text
        assert get_req.json()["projectId"] == project["id"]
    finally:
        _cleanup_user(email)


def test_buildings_create_and_list():
    client, token, email = _register_and_login()
    headers = {"Authorization": f"Bearer {token}"}
    try:
        project = client.post("/api/projects", json={"name": "Builds", "description": "Test"}, headers=headers).json()
        payload = {
            "name": "Academic Block A",
            "type": "academic",
            "zone": "academic",
            "width": 60.0,
            "depth": 40.0,
            "height": 18.0,
            "floorCount": 4,
            "requiredCount": 1,
        }
        create = client.post(f"/api/projects/{project['id']}/buildings", json=payload, headers=headers)
        assert create.status_code == 201, create.text
        created = create.json()
        assert created["projectId"] == project["id"]
        assert created["floorCount"] == 4

        list_resp = client.get(f"/api/projects/{project['id']}/buildings", headers=headers)
        assert list_resp.status_code == 200, list_resp.text
        assert len(list_resp.json()["buildings"]) == 1
    finally:
        _cleanup_user(email)


def test_constraints_create_and_list():
    client, token, email = _register_and_login()
    headers = {"Authorization": f"Bearer {token}"}
    try:
        project = client.post("/api/projects", json={"name": "Constraints", "description": "Test"}, headers=headers).json()
        payload = {
            "type": "MIN_DISTANCE",
            "sourceId": 1,
            "targetId": 5,
            "value": 100.0,
            "operator": ">=",
            "priority": "hard",
        }
        create = client.post(f"/api/projects/{project['id']}/constraints", json=payload, headers=headers)
        assert create.status_code == 201, create.text
        body = create.json()
        assert body["sourceId"] == 1
        assert body["priority"] == "hard"

        list_resp = client.get(f"/api/projects/{project['id']}/constraints", headers=headers)
        assert list_resp.status_code == 200, list_resp.text
        assert len(list_resp.json()["constraints"]) == 1
    finally:
        _cleanup_user(email)


def test_missing_project_and_forbidden_project_access():
    owner_client, owner_token, owner_email = _register_and_login("owner_project")
    other_client, other_token, other_email = _register_and_login("other_project")
    headers_owner = {"Authorization": f"Bearer {owner_token}"}
    headers_other = {"Authorization": f"Bearer {other_token}"}
    try:
        created = owner_client.post("/api/projects", json={"name": "Owner Project", "description": "Owned"}, headers=headers_owner).json()
        missing = owner_client.get("/api/projects/999999", headers=headers_owner)
        assert missing.status_code == 404
        assert missing.json()["detail"] == "PROJECT_NOT_FOUND"

        forbidden = other_client.get(f"/api/projects/{created['id']}", headers=headers_other)
        assert forbidden.status_code == 403
        assert forbidden.json()["detail"] == "FORBIDDEN"
    finally:
        _cleanup_user(owner_email)
        _cleanup_user(other_email)


def test_validation_error_returns_400_for_bad_project_payload():
    client, token, email = _register_and_login()
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = client.post("/api/projects", json={"description": "missing name"}, headers=headers)
        assert response.status_code == 400, response.text
        assert response.json()["detail"] == "VALIDATION_ERROR"
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


def test_phase5_routes_are_registered_once_only():
    required = {
        ("POST", "/api/projects"),
        ("GET", "/api/projects/{project_id}"),
        ("PUT", "/api/projects/{project_id}"),
        ("DELETE", "/api/projects/{project_id}"),
        ("POST", "/api/projects/{project_id}/requirements"),
        ("GET", "/api/projects/{project_id}/requirements"),
        ("POST", "/api/projects/{project_id}/buildings"),
        ("GET", "/api/projects/{project_id}/buildings"),
        ("POST", "/api/projects/{project_id}/constraints"),
        ("GET", "/api/projects/{project_id}/constraints"),
    }

    seen = {}
    for method, path in _iter_route_pairs(app.router):
        seen[(method, path)] = seen.get((method, path), 0) + 1

    for endpoint in required:
        assert seen.get(endpoint, 0) == 1, f"Endpoint missing or duplicated: {endpoint} -> {seen.get(endpoint, 0)}"


def test_public_requirements_and_entity_responses_do_not_expose_internal_db_fields():
    client, token, email = _register_and_login()
    headers = {"Authorization": f"Bearer {token}"}
    try:
        project = client.post("/api/projects", json={"name": "Sanitized", "description": "check fields"}, headers=headers).json()

        req_body = {
            "siteWidth": 300.0,
            "siteHeight": 300.0,
            "minGreenPercent": 25.0,
            "minParkingPercent": 10.0,
            "minRoadWidth": 8.0,
            "minBuildingGap": 10.0,
            "entrances": [{"x": 150.0, "y": 0.0, "width": 10.0}],
        }
        req_response = client.post(f"/api/projects/{project['id']}/requirements", json=req_body, headers=headers)
        assert req_response.status_code == 201, req_response.text
        payload = req_response.json()
        assert "road_data" not in payload
        assert "roadData" not in payload
        assert "total_area" not in payload
        assert "totalArea" not in payload

        building_payload = {
            "name": "Academic Block A",
            "type": "academic",
            "zone": "academic",
            "width": 60.0,
            "depth": 40.0,
            "height": 18.0,
            "floorCount": 4,
            "requiredCount": 1,
        }
        building_response = client.post(f"/api/projects/{project['id']}/buildings", json=building_payload, headers=headers)
        assert building_response.status_code == 201, building_response.text
        building_json = building_response.json()
        assert "metadata" not in building_json
        assert "metadata_" not in building_json

        constraint_payload = {
            "type": "MIN_DISTANCE",
            "sourceId": 1,
            "targetId": 5,
            "value": 100.0,
            "operator": ">=",
            "priority": "hard",
        }
        constraint_response = client.post(f"/api/projects/{project['id']}/constraints", json=constraint_payload, headers=headers)
        assert constraint_response.status_code == 201, constraint_response.text
        constraint_json = constraint_response.json()
        assert "metadata" not in constraint_json
        assert "metadata_" not in constraint_json
    finally:
        _cleanup_user(email)
