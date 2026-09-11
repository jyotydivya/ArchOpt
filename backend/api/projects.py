from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.building import Building
from backend.models.constraint import Constraint
from backend.models.project import Project
from backend.models.requirement import CampusRequirement
from backend.models.user import User
from backend.repositories.project_repository import get_project_for_user
from backend.schemas.building import BuildingCreateRequest, BuildingListResponse, BuildingResponse
from backend.schemas.constraint import ConstraintCreateRequest, ConstraintListResponse, ConstraintResponse
from backend.schemas.project import ProjectCreateRequest, ProjectResponse, ProjectUpdateRequest
from backend.schemas.requirement import EntranceSchema, RequirementsResponse, RequirementsSaveRequest
from backend.security import get_current_user

router = APIRouter(prefix="/api", tags=["projects"])


@router.post("/projects", status_code=status.HTTP_201_CREATED, response_model=ProjectResponse)
def create_project(
    payload: ProjectCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = Project(
        user_id=current_user.id,
        name=payload.name,
        description=payload.description,
        status="DRAFT",
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        status=project.status,
    )


@router.get("/projects/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = get_project_for_user(db, current_user, project_id)
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        status=project.status,
    )


@router.put("/projects/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    payload: ProjectUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = get_project_for_user(db, current_user, project_id)
    project.name = payload.name
    project.description = payload.description
    db.commit()
    db.refresh(project)

    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        status=project.status,
    )


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = get_project_for_user(db, current_user, project_id)
    db.delete(project)
    db.commit()
    return None


@router.post("/projects/{project_id}/requirements", status_code=status.HTTP_201_CREATED, response_model=RequirementsResponse)
def create_requirements(
    project_id: int,
    payload: RequirementsSaveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = get_project_for_user(db, current_user, project_id)

    requirement = db.query(CampusRequirement).filter(CampusRequirement.project_id == project.id).first()
    if requirement is not None:
        # update existing requirement record
        requirement.site_width = payload.site_width
        requirement.site_height = payload.site_height
        requirement.min_green_percent = payload.min_green_percent
        requirement.min_parking_percent = payload.min_parking_percent
        requirement.min_road_width = payload.min_road_width
        requirement.min_building_gap = payload.min_building_gap
        requirement.entrance_data = [item.model_dump() for item in payload.entrances]
        db.commit()
        db.refresh(requirement)
        requirement_obj = requirement
    else:
        requirement_obj = CampusRequirement(
            project_id=project.id,
            site_width=payload.site_width,
            site_height=payload.site_height,
            min_green_percent=payload.min_green_percent,
            min_parking_percent=payload.min_parking_percent,
            min_road_width=payload.min_road_width,
            min_building_gap=payload.min_building_gap,
            entrance_data=[item.model_dump() for item in payload.entrances],
            road_data=[],
        )
        db.add(requirement_obj)
        db.commit()
        db.refresh(requirement_obj)

    return RequirementsResponse(
        id=requirement_obj.id,
        projectId=requirement_obj.project_id,
        siteWidth=requirement_obj.site_width,
        siteHeight=requirement_obj.site_height,
        minGreenPercent=requirement_obj.min_green_percent,
        minParkingPercent=requirement_obj.min_parking_percent,
        minRoadWidth=requirement_obj.min_road_width,
        minBuildingGap=requirement_obj.min_building_gap,
        entrances=[EntranceSchema(**item) for item in requirement_obj.entrance_data],
    )


@router.get("/projects/{project_id}/requirements", response_model=RequirementsResponse)
def get_requirements(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = get_project_for_user(db, current_user, project_id)
    requirement = db.query(CampusRequirement).filter(CampusRequirement.project_id == project.id).first()
    if requirement is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PROJECT_NOT_FOUND")

    return RequirementsResponse(
        projectId=requirement.project_id,
        siteWidth=requirement.site_width,
        siteHeight=requirement.site_height,
        minGreenPercent=requirement.min_green_percent,
        minParkingPercent=requirement.min_parking_percent,
        minRoadWidth=requirement.min_road_width,
        minBuildingGap=requirement.min_building_gap,
        entrances=[EntranceSchema(**item) for item in requirement.entrance_data],
    )


@router.post("/projects/{project_id}/buildings", status_code=status.HTTP_201_CREATED, response_model=BuildingResponse)
def create_building(
    project_id: int,
    payload: BuildingCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = get_project_for_user(db, current_user, project_id)
    building = Building(
        project_id=project.id,
        name=payload.name,
        type=payload.type,
        zone=payload.zone,
        width=payload.width,
        depth=payload.depth,
        height=payload.height,
        floor_count=payload.floor_count,
        required_count=payload.required_count,
    )
    db.add(building)
    db.commit()
    db.refresh(building)

    return BuildingResponse(
        id=building.id,
        projectId=building.project_id,
        name=building.name,
        type=building.type,
        zone=building.zone,
        width=building.width,
        depth=building.depth,
        height=building.height,
        floorCount=building.floor_count,
        requiredCount=building.required_count,
    )


@router.get("/projects/{project_id}/buildings", response_model=BuildingListResponse)
def get_buildings(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = get_project_for_user(db, current_user, project_id)
    buildings = db.query(Building).filter(Building.project_id == project.id).all()
    items = [
        BuildingResponse(
            id=item.id,
            projectId=item.project_id,
            name=item.name,
            type=item.type,
            zone=item.zone,
            width=item.width,
            depth=item.depth,
            height=item.height,
            floorCount=item.floor_count,
            requiredCount=item.required_count,
        )
        for item in buildings
    ]
    return BuildingListResponse(buildings=items)


@router.post("/projects/{project_id}/constraints", status_code=status.HTTP_201_CREATED, response_model=ConstraintResponse)
def create_constraint(
    project_id: int,
    payload: ConstraintCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = get_project_for_user(db, current_user, project_id)
    constraint = Constraint(
        project_id=project.id,
        constraint_type=payload.type,
        source_id=payload.source_id,
        target_id=payload.target_id,
        value=payload.value,
        operator=payload.operator,
        priority=payload.priority,
    )
    db.add(constraint)
    db.commit()
    db.refresh(constraint)

    return ConstraintResponse(
        id=constraint.id,
        type=constraint.constraint_type,
        sourceId=constraint.source_id,
        targetId=constraint.target_id,
        value=constraint.value,
        operator=constraint.operator,
        priority=constraint.priority,
    )


@router.get("/projects/{project_id}/constraints", response_model=ConstraintListResponse)
def get_constraints(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = get_project_for_user(db, current_user, project_id)
    constraints = db.query(Constraint).filter(Constraint.project_id == project.id).all()
    items = [
        ConstraintResponse(
            id=item.id,
            type=item.constraint_type,
            sourceId=item.source_id,
            targetId=item.target_id,
            value=item.value,
            operator=item.operator,
            priority=item.priority,
        )
        for item in constraints
    ]
    return ConstraintListResponse(constraints=items)
