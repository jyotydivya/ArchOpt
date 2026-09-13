import uuid
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from backend.config import settings
from backend.database import SessionLocal
from backend.main import app
from backend.models.requirement import CampusRequirement
from backend.models.user import User
from backend.services.ml_bridge import (
    invoke_p1_build_graph,
    invoke_p2_generate_candidates,
    invoke_p3_optimize_layouts,
    run_real_pipeline,
)
from fastapi import HTTPException


@pytest.fixture
def auth_client():
    client = TestClient(app)
    email = f"p10_user_{uuid.uuid4().hex[:8]}@example.com"
    reg = client.post(
        "/api/auth/register",
        json={"name": "P10 Auditor", "email": email, "password": "password123"},
    )
    assert reg.status_code == 201
    login_res = client.post(
        "/api/auth/login",
        json={"email": email, "password": "password123"},
    )
    assert login_res.status_code == 200
    token = login_res.json()["accessToken"]
    client.headers = {"Authorization": f"Bearer {token}"}
    client.user_email = email
    try:
        yield client
    finally:
        with SessionLocal() as db:
            user = db.query(User).filter(User.email == email).first()
            if user:
                db.delete(user)
                db.commit()


@pytest.fixture
def configured_project(auth_client):
    proj_res = auth_client.post(
        "/api/projects",
        json={"name": "P10 Integration Project", "description": "Testing P1/P2/P3 boundary"},
    )
    project_id = proj_res.json()["id"]

    # Requirements
    auth_client.post(
        f"/api/projects/{project_id}/requirements",
        json={
            "siteWidth": 300.0,
            "siteHeight": 300.0,
            "minGreenPercent": 25.0,
            "minParkingPercent": 10.0,
            "minRoadWidth": 8.0,
            "minBuildingGap": 10.0,
            "entrances": [{"x": 150.0, "y": 0.0, "width": 10.0}],
        },
    )

    # Building
    b_res = auth_client.post(
        f"/api/projects/{project_id}/buildings",
        json={
            "name": "Engineering Block",
            "type": "academic",
            "zone": "academic",
            "width": 60.0,
            "depth": 40.0,
            "height": 18.0,
            "floorCount": 4,
            "requiredCount": 1,
        },
    )
    building_id = b_res.json()["id"]

    # Constraint
    auth_client.post(
        f"/api/projects/{project_id}/constraints",
        json={
            "type": "MIN_DISTANCE",
            "sourceId": building_id,
            "targetId": building_id,
            "value": 20.0,
            "operator": ">=",
            "priority": "hard",
        },
    )

    return project_id


def test_mock_mode_default_behavior_preserved(auth_client, configured_project, monkeypatch):
    """Verifies that MOCK mode is preserved and operational."""
    monkeypatch.setattr(settings, "PIPELINE_MODE", "mock")
    res = auth_client.post(
        f"/api/projects/{configured_project}/layout-runs",
        json={"candidateCount": 50, "topK": 3, "algorithm": "GNN_NSGA2"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "COMPLETED"
    assert data["layoutCount"] == 3


def test_strict_pipeline_mode_validation_rejects_typo(auth_client, configured_project, monkeypatch):
    """Verifies that invalid PIPELINE_MODE values raise 500 INVALID_PIPELINE_MODE."""
    monkeypatch.setattr(settings, "PIPELINE_MODE", "reall")
    res = auth_client.post(
        f"/api/projects/{configured_project}/layout-runs",
        json={"candidateCount": 50, "topK": 3, "algorithm": "GNN_NSGA2"},
    )
    assert res.status_code == 500
    assert res.json()["detail"] == "INVALID_PIPELINE_MODE"


def test_real_mode_missing_modules_surfaces_422_generation_failed(
    auth_client, configured_project, monkeypatch
):
    """
    Contract Rule: In REAL mode, when P1/P2/P3 modules are missing,
    the API must return HTTP 422 GENERATION_FAILED and never fall back to mock.
    """
    monkeypatch.setattr(settings, "PIPELINE_MODE", "real")
    res = auth_client.post(
        f"/api/projects/{configured_project}/layout-runs",
        json={"candidateCount": 100, "topK": 5, "algorithm": "GNN_NSGA2"},
    )
    assert res.status_code == 422
    assert res.json()["detail"] == "GENERATION_FAILED"


def test_real_mode_p1_failure_surfaces_422_generation_failed(
    auth_client, configured_project, monkeypatch
):
    """Verifies that an exception in P1 raises 422 GENERATION_FAILED."""
    monkeypatch.setattr(settings, "PIPELINE_MODE", "real")
    with patch("backend.services.ml_bridge.invoke_p1_build_graph", side_effect=Exception("P1 graph build crashed")):
        res = auth_client.post(
            f"/api/projects/{configured_project}/layout-runs",
            json={"candidateCount": 100, "topK": 5, "algorithm": "GNN_NSGA2"},
        )
        assert res.status_code == 422
        assert res.json()["detail"] == "GENERATION_FAILED"


def test_real_mode_p1_malformed_graph_surfaces_422_generation_failed(
    auth_client, configured_project, monkeypatch
):
    """Verifies that P1 returning a graph missing Contract 5 fields raises 422 GENERATION_FAILED."""
    monkeypatch.setattr(settings, "PIPELINE_MODE", "real")
    invalid_graph = {"nodeFeatures": [[1.0, 2.0]]}
    with patch.dict("sys.modules", {"ml": MagicMock(), "ml.dataset": MagicMock(), "ml.dataset.graph_builder": MagicMock()}):
        import sys
        sys.modules["ml.dataset.graph_builder"].build_graph.return_value = invalid_graph
        res = auth_client.post(
            f"/api/projects/{configured_project}/layout-runs",
            json={"candidateCount": 100, "topK": 5, "algorithm": "GNN_NSGA2"},
        )
        assert res.status_code == 422
        assert res.json()["detail"] == "GENERATION_FAILED"


def test_real_mode_p2_failure_surfaces_422_generation_failed(
    auth_client, configured_project, monkeypatch
):
    """Verifies that an exception in P2 raises 422 GENERATION_FAILED."""
    monkeypatch.setattr(settings, "PIPELINE_MODE", "real")
    with patch("backend.services.ml_bridge.invoke_p1_build_graph", return_value={"mock": "graph"}):
        with patch("backend.services.ml_bridge.invoke_p2_generate_candidates", side_effect=RuntimeError("GNN OOM")):
            res = auth_client.post(
                f"/api/projects/{configured_project}/layout-runs",
                json={"candidateCount": 100, "topK": 5, "algorithm": "GNN_NSGA2"},
            )
            assert res.status_code == 422
            assert res.json()["detail"] == "GENERATION_FAILED"


def test_real_mode_p3_failure_surfaces_422_generation_failed(
    auth_client, configured_project, monkeypatch
):
    """Verifies that an exception in P3 raises 422 GENERATION_FAILED."""
    monkeypatch.setattr(settings, "PIPELINE_MODE", "real")
    with patch("backend.services.ml_bridge.invoke_p1_build_graph", return_value={"mock": "graph"}):
        with patch("backend.services.ml_bridge.invoke_p2_generate_candidates", return_value=[{"cand": 1}]):
            with patch("backend.services.ml_bridge.invoke_p3_optimize_layouts", side_effect=ValueError("Optimizer error")):
                res = auth_client.post(
                    f"/api/projects/{configured_project}/layout-runs",
                    json={"candidateCount": 100, "topK": 5, "algorithm": "GNN_NSGA2"},
                )
                assert res.status_code == 422
                assert res.json()["detail"] == "GENERATION_FAILED"


def test_real_mode_p3_wrong_top_k_count_surfaces_422_generation_failed(
    auth_client, configured_project, monkeypatch
):
    """Verifies that if P3 returns fewer or more than top_k items, 422 GENERATION_FAILED is raised."""
    monkeypatch.setattr(settings, "PIPELINE_MODE", "real")
    with patch("backend.services.ml_bridge.invoke_p1_build_graph", return_value={"mock": "graph"}):
        with patch("backend.services.ml_bridge.invoke_p2_generate_candidates", return_value=[{"cand": 1}]):
            with patch.dict("sys.modules", {"optimization": MagicMock(), "optimization.optimizer": MagicMock()}):
                import sys
                sys.modules["optimization.optimizer"].optimize_layouts.return_value = [{"cand": 1}]  # 1 when top_k=3
                res = auth_client.post(
                    f"/api/projects/{configured_project}/layout-runs",
                    json={"candidateCount": 100, "topK": 3, "algorithm": "GNN_NSGA2"},
                )
                assert res.status_code == 422
                assert res.json()["detail"] == "GENERATION_FAILED"


def test_real_mode_malformed_p3_output_surfaces_422_generation_failed(
    auth_client, configured_project, monkeypatch
):
    """Verifies that malformed RankedLayout output from P3 is rejected with 422 GENERATION_FAILED."""
    monkeypatch.setattr(settings, "PIPELINE_MODE", "real")
    malformed_output = [{"candidateId": "cand-001", "buildings": []}]
    with patch("backend.services.ml_bridge.invoke_p1_build_graph", return_value={"mock": "graph"}):
        with patch("backend.services.ml_bridge.invoke_p2_generate_candidates", return_value=[{"cand": 1}]):
            with patch("backend.services.ml_bridge.invoke_p3_optimize_layouts", return_value=malformed_output):
                res = auth_client.post(
                    f"/api/projects/{configured_project}/layout-runs",
                    json={"candidateCount": 100, "topK": 1, "algorithm": "GNN_NSGA2"},
                )
                assert res.status_code == 422
                assert res.json()["detail"] == "GENERATION_FAILED"


def test_real_mode_foreign_building_id_surfaces_422_generation_failed(
    auth_client, configured_project, monkeypatch
):
    """Verifies that candidate layouts containing invalid/foreign building IDs raise 422 GENERATION_FAILED."""
    monkeypatch.setattr(settings, "PIPELINE_MODE", "real")
    # Candidate layout references buildingId=99999 which is not in the project
    foreign_layout = [
        {
            "candidateId": "cand-foreign",
            "rank": 1,
            "feasible": True,
            "buildings": [{"buildingId": 99999, "x": 10.0, "y": 10.0, "rotation": 0.0}],
            "metrics": {
                "landUtilization": 0.7,
                "greenRatio": 0.2,
                "parkingRatio": 0.1,
                "accessibilityScore": 0.8,
                "roadEfficiency": 0.8,
                "constraintScore": 1.0,
            },
        }
    ]
    with patch("backend.services.ml_bridge.invoke_p1_build_graph", return_value={"mock": "graph"}):
        with patch("backend.services.ml_bridge.invoke_p2_generate_candidates", return_value=[{"cand": 1}]):
            with patch("backend.services.ml_bridge.invoke_p3_optimize_layouts", return_value=foreign_layout):
                res = auth_client.post(
                    f"/api/projects/{configured_project}/layout-runs",
                    json={"candidateCount": 100, "topK": 1, "algorithm": "GNN_NSGA2"},
                )
                assert res.status_code == 422
                assert res.json()["detail"] == "GENERATION_FAILED"


def test_real_mode_valid_pipeline_execution(auth_client, configured_project, monkeypatch):
    """Verifies that when upstream P1/P2/P3 return valid contract data, REAL mode persists and completes."""
    monkeypatch.setattr(settings, "PIPELINE_MODE", "real")

    b_list = auth_client.get(f"/api/projects/{configured_project}/buildings").json()["buildings"]
    actual_building_id = b_list[0]["id"]

    mock_ranked_layouts = [
        {
            "candidateId": "real-cand-001",
            "rank": 1,
            "feasible": True,
            "buildings": [
                {
                    "buildingId": actual_building_id,
                    "x": 60.0,
                    "y": 80.0,
                    "rotation": 0.0,
                }
            ],
            "metrics": {
                "landUtilization": 0.75,
                "greenRatio": 0.25,
                "parkingRatio": 0.12,
                "accessibilityScore": 0.90,
                "roadEfficiency": 0.85,
                "constraintScore": 1.0,
            },
        }
    ]

    with patch("backend.services.ml_bridge.invoke_p1_build_graph", return_value={"graph": "valid"}):
        with patch("backend.services.ml_bridge.invoke_p2_generate_candidates", return_value=[{"cand": "valid"}]):
            with patch("backend.services.ml_bridge.invoke_p3_optimize_layouts", return_value=mock_ranked_layouts):
                res = auth_client.post(
                    f"/api/projects/{configured_project}/layout-runs",
                    json={"candidateCount": 100, "topK": 1, "algorithm": "GNN_NSGA2"},
                )
                assert res.status_code == 200
                data = res.json()
                assert data["status"] == "COMPLETED"
                assert data["layoutCount"] == 1

    # Verify retrieval of the generated layout
    list_resp = auth_client.get(f"/api/projects/{configured_project}/layouts")
    assert list_resp.status_code == 200
    layouts = list_resp.json()["layouts"]
    assert len(layouts) >= 1
    assert layouts[-1]["metrics"]["landUtilization"] == 0.75


def test_requirements_total_area_calculated_on_create_and_update(auth_client, configured_project):
    """Verifies that total_area is computed as siteWidth * siteHeight on create and update."""
    # Read initial requirement total_area from DB
    with SessionLocal() as db:
        req = db.query(CampusRequirement).filter(CampusRequirement.project_id == configured_project).first()
        assert req is not None
        assert float(req.total_area) == 300.0 * 300.0

    # Update requirements with new dimensions
    update_res = auth_client.post(
        f"/api/projects/{configured_project}/requirements",
        json={
            "siteWidth": 450.0,
            "siteHeight": 200.0,
            "minGreenPercent": 30.0,
            "minParkingPercent": 15.0,
            "minRoadWidth": 10.0,
            "minBuildingGap": 12.0,
            "entrances": [{"x": 200.0, "y": 0.0, "width": 12.0}],
        },
    )
    assert update_res.status_code == 201

    with SessionLocal() as db:
        req_updated = db.query(CampusRequirement).filter(CampusRequirement.project_id == configured_project).first()
        assert float(req_updated.total_area) == 450.0 * 200.0


def test_extra_fields_in_payload_returns_400_validation_error(auth_client):
    """Verifies that schemas reject extra fields with 400 VALIDATION_ERROR (extra='forbid')."""
    res = auth_client.post(
        "/api/projects",
        json={
            "name": "Invalid Project",
            "description": "Extra field test",
            "unexpected_field": "disallowed",
        },
    )
    assert res.status_code == 400
    assert res.json()["detail"] == "VALIDATION_ERROR"


def test_register_duplicate_email_returns_409(auth_client):
    """Verifies that attempting to register an existing email returns 409 EMAIL_ALREADY_EXISTS."""
    res = auth_client.post(
        "/api/auth/register",
        json={"name": "Duplicate User", "email": auth_client.user_email, "password": "password123"},
    )
    assert res.status_code == 409
    assert res.json()["detail"] == "EMAIL_ALREADY_EXISTS"


def test_layout_detail_data_integrity_error(auth_client, configured_project):
    """Verifies that if a layout references an invalid buildingId, get_layout_detail raises 500 DATA_INTEGRITY_ERROR."""
    from backend.models.layout import Layout

    # Generate a run first
    res = auth_client.post(
        f"/api/projects/{configured_project}/layout-runs",
        json={"candidateCount": 50, "topK": 1, "algorithm": "GNN_NSGA2"},
    )
    assert res.status_code == 200

    list_resp = auth_client.get(f"/api/projects/{configured_project}/layouts")
    layout_id = list_resp.json()["layouts"][0]["id"]

    # Corrupt layout in DB by giving it a foreign buildingId
    with SessionLocal() as db:
        layout = db.query(Layout).filter(Layout.id == layout_id).first()
        layout.layout_json = {
            "candidateId": "corrupt",
            "buildings": [{"buildingId": 999999, "x": 10.0, "y": 10.0, "rotation": 0.0}],
        }
        db.commit()

    detail_res = auth_client.get(f"/api/layouts/{layout_id}")
    assert detail_res.status_code == 500
    assert detail_res.json()["detail"] == "DATA_INTEGRITY_ERROR"
