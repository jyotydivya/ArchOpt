from backend.schemas import (
    UserRegisterRequest,
    UserRegisterResponse,
    UserLoginRequest,
    UserLoginResponse,
    ProjectCreateRequest,
    ProjectResponse,
    RequirementsSaveRequest,
    RequirementsResponse,
    BuildingCreateRequest,
    BuildingResponse,
    BuildingListResponse,
    ConstraintCreateRequest,
    ConstraintResponse,
    ConstraintListResponse,
    LayoutRunCreateRequest,
    LayoutRunCreateResponse,
    LayoutListResponse,
    LayoutDetailResponse,
    LayoutSelectResponse,
    BlueprintResponse,
)


def test_auth_schemas():
    reg_req = UserRegisterRequest(name="Student", email="student@example.com", password="password123")
    assert reg_req.email == "student@example.com"

    reg_res = UserRegisterResponse(id=1, name="Student", email="student@example.com", role="PROJECT_MANAGER")
    assert reg_res.role == "PROJECT_MANAGER"

    login_req = UserLoginRequest(email="student@example.com", password="password123")
    assert login_req.password == "password123"

    login_res = UserLoginResponse.model_validate({
        "accessToken": "JWT_TOKEN",
        "tokenType": "Bearer",
        "user": {"id": 1, "name": "Student", "role": "PROJECT_MANAGER"}
    })
    dump = login_res.model_dump(by_alias=True)
    assert dump["accessToken"] == "JWT_TOKEN"
    assert dump["tokenType"] == "Bearer"


def test_project_schemas():
    create_req = ProjectCreateRequest(name="VIT Campus Expansion", description="Campus planning case study")
    assert create_req.name == "VIT Campus Expansion"

    res = ProjectResponse(id=1, name="VIT Campus Expansion", description="Campus planning case study", status="DRAFT")
    dump = res.model_dump(by_alias=True)
    assert dump["id"] == 1
    assert dump["status"] == "DRAFT"


def test_requirements_schemas():
    req_data = {
        "siteWidth": 300.0,
        "siteHeight": 300.0,
        "minGreenPercent": 25.0,
        "minParkingPercent": 10.0,
        "minRoadWidth": 8.0,
        "minBuildingGap": 10.0,
        "entrances": [{"x": 150.0, "y": 0.0, "width": 10.0}]
    }
    save_req = RequirementsSaveRequest.model_validate(req_data)
    assert save_req.site_width == 300.0
    assert len(save_req.entrances) == 1

    resp_data = {"id": 1, "projectId": 1, **req_data}
    req_res = RequirementsResponse.model_validate(resp_data)
    dump = req_res.model_dump(by_alias=True)
    assert dump["projectId"] == 1
    assert dump["siteWidth"] == 300.0
    assert "road_data" not in dump
    assert "roadData" not in dump


def test_building_schemas():
    b_data = {
        "name": "Academic Block A",
        "type": "academic",
        "zone": "academic",
        "width": 60.0,
        "depth": 40.0,
        "height": 18.0,
        "floorCount": 4,
        "requiredCount": 1
    }
    b_req = BuildingCreateRequest.model_validate(b_data)
    assert b_req.floor_count == 4

    b_res = BuildingResponse.model_validate({"id": 1, "projectId": 1, **b_data})
    dump = b_res.model_dump(by_alias=True)
    assert dump["id"] == 1
    assert dump["projectId"] == 1
    assert dump["floorCount"] == 4

    list_res = BuildingListResponse(buildings=[b_res])
    assert len(list_res.buildings) == 1


def test_constraint_schemas():
    c_data = {
        "type": "MIN_DISTANCE",
        "sourceId": 1,
        "targetId": 5,
        "value": 100.0,
        "operator": ">=",
        "priority": "hard"
    }
    c_req = ConstraintCreateRequest.model_validate(c_data)
    assert c_req.source_id == 1

    c_res = ConstraintResponse.model_validate({"id": 1, **c_data})
    dump = c_res.model_dump(by_alias=True)
    assert dump["id"] == 1
    assert dump["sourceId"] == 1

    list_res = ConstraintListResponse(constraints=[c_res])
    assert len(list_res.constraints) == 1


def test_layout_schemas():
    run_req = LayoutRunCreateRequest.model_validate({"candidateCount": 100, "topK": 5, "algorithm": "GNN_NSGA2"})
    assert run_req.candidate_count == 100

    run_res = LayoutRunCreateResponse.model_validate({"runId": 12, "status": "COMPLETED", "layoutCount": 5})
    dump = run_res.model_dump(by_alias=True)
    assert dump["runId"] == 12

    list_res = LayoutListResponse.model_validate({
        "layouts": [
            {
                "id": 101,
                "rank": 1,
                "feasible": True,
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
    })
    assert len(list_res.layouts) == 1
    assert list_res.layouts[0].metrics.land_utilization == 0.72

    detail_res = LayoutDetailResponse.model_validate({
        "id": 101,
        "rank": 1,
        "feasible": True,
        "site": {"width": 300.0, "height": 300.0},
        "buildings": [],
        "roads": [],
        "greenAreas": [],
        "parkingAreas": [],
        "entrances": [],
        "metrics": {}
    })
    assert detail_res.id == 101

    select_res = LayoutSelectResponse.model_validate({"projectId": 1, "layoutId": 101, "status": "SELECTED"})
    dump_select = select_res.model_dump(by_alias=True)
    assert dump_select["projectId"] == 1
    assert dump_select["layoutId"] == 101


def test_blueprint_schema():
    bp_data = {
        "projectId": 1,
        "layoutId": 101,
        "site": {"width": 300.0, "height": 300.0},
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
        "entrances": []
    }
    bp = BlueprintResponse.model_validate(bp_data)
    dump = bp.model_dump(by_alias=True)
    assert dump["projectId"] == 1
    assert dump["layoutId"] == 101
    assert dump["buildings"][0]["floorCount"] == 4


if __name__ == "__main__":
    test_auth_schemas()
    test_project_schemas()
    test_requirements_schemas()
    test_building_schemas()
    test_constraint_schemas()
    test_layout_schemas()
    test_blueprint_schema()
    print("ALL PHASE 3 PYDANTIC SCHEMA TESTS PASSED SUCCESSFULLY!")
