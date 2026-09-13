import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from backend.config import settings
from backend.main import app
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
    # Register & Login unique test user
    email = f"p10_user_{id(client)}@example.com"
    client.post(
        "/api/auth/register",
        json={"name": "P10 Auditor", "email": email, "password": "password123"},
    )
    login_res = client.post(
        "/api/auth/login",
        json={"email": email, "password": "password123"},
    )
    token = login_res.json()["accessToken"]
    client.headers = {"Authorization": f"Bearer {token}"}
    return client


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
    auth_client.post(
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

    # Constraint
    auth_client.post(
        f"/api/projects/{project_id}/constraints",
        json={
            "type": "MIN_DISTANCE",
            "sourceId": 1,
            "targetId": 1,
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


def test_real_mode_malformed_p3_output_surfaces_422_generation_failed(
    auth_client, configured_project, monkeypatch
):
    """Verifies that malformed RankedLayout output from P3 is rejected with 422 GENERATION_FAILED."""
    monkeypatch.setattr(settings, "PIPELINE_MODE", "real")
    # Missing required 'rank' and 'metrics' fields
    malformed_output = [{"candidateId": "cand-001", "buildings": []}]
    with patch("backend.services.ml_bridge.invoke_p1_build_graph", return_value={"mock": "graph"}):
        with patch("backend.services.ml_bridge.invoke_p2_generate_candidates", return_value=[{"cand": 1}]):
            with patch("backend.services.ml_bridge.invoke_p3_optimize_layouts", return_value=malformed_output):
                res = auth_client.post(
                    f"/api/projects/{configured_project}/layout-runs",
                    json={"candidateCount": 100, "topK": 5, "algorithm": "GNN_NSGA2"},
                )
                assert res.status_code == 422
                assert res.json()["detail"] == "GENERATION_FAILED"


def test_real_mode_valid_pipeline_execution(auth_client, configured_project, monkeypatch):
    """Verifies that when upstream P1/P2/P3 return valid contract data, REAL mode persists and completes."""
    monkeypatch.setattr(settings, "PIPELINE_MODE", "real")

    mock_ranked_layouts = [
        {
            "candidateId": "real-cand-001",
            "rank": 1,
            "feasible": True,
            "buildings": [
                {
                    "buildingId": 1,
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
    list_res = auth_client.get(f"/api/projects/{configured_project}/layouts")
    assert list_res.status_code == 200
    layouts = list_res.json()["layouts"]
    assert len(layouts) >= 1
    assert layouts[-1]["metrics"]["landUtilization"] == 0.75
