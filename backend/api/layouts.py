from datetime import datetime, timezone
from typing import Any, Optional
from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.building import Building
from backend.models.layout import Layout
from backend.models.layout_run import LayoutRun
from backend.models.requirement import CampusRequirement
from backend.models.selected_plan import SelectedPlan
from backend.models.user import User
from backend.repositories.project_repository import get_project_for_user
from backend.schemas.layout import (
    LayoutDetailResponse,
    LayoutListResponse,
    LayoutMetricsSchema,
    LayoutRunCreateRequest,
    LayoutRunCreateResponse,
    LayoutSelectResponse,
    LayoutSummarySchema,
    SiteDimensionSchema,
)
from backend.schemas.blueprint import BlueprintResponse
from backend.schemas.requirement import EntranceSchema
from backend.security import get_current_user
from backend.services.blueprint_service import generate_blueprint
from backend.services.orchestrator import generate_layout_run

router = APIRouter(prefix="/api", tags=["layouts"])



@router.post(
    "/projects/{project_id}/layout-runs",
    status_code=status.HTTP_200_OK,
    response_model=LayoutRunCreateResponse,
)
def create_layout_run(
    project_id: int,
    payload: LayoutRunCreateRequest = LayoutRunCreateRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = get_project_for_user(db, current_user, project_id)
    layout_run, layouts = generate_layout_run(db, project, payload)
    return LayoutRunCreateResponse(
        runId=layout_run.id,
        status=layout_run.status,
        layoutCount=len(layouts),
    )


@router.get(
    "/projects/{project_id}/layouts",
    status_code=status.HTTP_200_OK,
    response_model=LayoutListResponse,
)
def get_project_layouts(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = get_project_for_user(db, current_user, project_id)
    latest_run = (
        db.query(LayoutRun)
        .filter(LayoutRun.project_id == project.id)
        .order_by(LayoutRun.id.desc())
        .first()
    )
    if not latest_run:
        return LayoutListResponse(layouts=[])

    layouts = (
        db.query(Layout)
        .filter(Layout.run_id == latest_run.id)
        .order_by(Layout.rank.asc())
        .all()
    )
    items = [
        LayoutSummarySchema(
            id=layout.id,
            rank=layout.rank,
            feasible=layout.feasible,
            metrics=LayoutMetricsSchema.model_validate(layout.metrics_json or {}),
        )
        for layout in layouts
    ]
    return LayoutListResponse(layouts=items)


@router.get(
    "/layouts/{layout_id}",
    status_code=status.HTTP_200_OK,
    response_model=LayoutDetailResponse,
)
def get_layout_detail(
    layout_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    layout = db.query(Layout).filter(Layout.id == layout_id).first()
    if layout is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="LAYOUT_NOT_FOUND",
        )

    layout_run = db.query(LayoutRun).filter(LayoutRun.id == layout.run_id).first()
    if layout_run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="LAYOUT_NOT_FOUND",
        )

    # Scoped authorization: layout's project must belong to current user
    project = get_project_for_user(db, current_user, layout_run.project_id)

    requirement = (
        db.query(CampusRequirement)
        .filter(CampusRequirement.project_id == project.id)
        .first()
    )

    layout_data = layout.layout_json if isinstance(layout.layout_json, dict) else {}

    if requirement:
        site_width = float(requirement.site_width)
        site_height = float(requirement.site_height)
        entrances_list = [
            EntranceSchema(**e)
            for e in (requirement.entrance_data if requirement.entrance_data else [])
        ]
    else:
        site_width = float(layout_data.get("siteWidth", 300.0))
        site_height = float(layout_data.get("siteHeight", 300.0))
        entrances_list = []

    project_buildings = (
        db.query(Building)
        .filter(Building.project_id == project.id)
        .all()
    )
    buildings_by_id = {b.id: b for b in project_buildings}

    candidate_buildings = layout_data.get("buildings", [])
    buildings_list: list[dict[str, Any]] = []
    for b_pos in candidate_buildings:
        b_id = b_pos.get("buildingId") or b_pos.get("id")
        if b_id is None or b_id not in buildings_by_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="DATA_INTEGRITY_ERROR",
            )
        buildings_list.append({
            "buildingId": b_id,
            "x": float(b_pos.get("x", 0.0)),
            "y": float(b_pos.get("y", 0.0)),
            "rotation": float(b_pos.get("rotation", 0.0)),
        })

    return LayoutDetailResponse(
        id=layout.id,
        rank=layout.rank,
        feasible=layout.feasible,
        site=SiteDimensionSchema(width=site_width, height=site_height),
        buildings=buildings_list,
        roads=[],
        greenAreas=[],
        parkingAreas=[],
        entrances=entrances_list,
        metrics=layout.metrics_json or {},
    )


@router.post(
    "/layouts/{layout_id}/select",
    status_code=status.HTTP_200_OK,
    response_model=LayoutSelectResponse,
)
def select_layout(
    layout_id: int,
    payload: Optional[dict[str, Any]] = Body(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    layout = db.query(Layout).filter(Layout.id == layout_id).first()
    if layout is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="LAYOUT_NOT_FOUND",
        )

    layout_run = db.query(LayoutRun).filter(LayoutRun.id == layout.run_id).first()
    if layout_run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="LAYOUT_NOT_FOUND",
        )

    # Scoped authorization: layout's project must belong to current user
    project = get_project_for_user(db, current_user, layout_run.project_id)

    # Enforce exactly one active selected plan per project
    selected_plan = (
        db.query(SelectedPlan)
        .filter(SelectedPlan.project_id == project.id)
        .first()
    )

    if selected_plan is not None:
        selected_plan.layout_id = layout.id
        selected_plan.selected_by = current_user.id
        selected_plan.selected_at = datetime.now(timezone.utc)
    else:
        selected_plan = SelectedPlan(
            project_id=project.id,
            layout_id=layout.id,
            selected_by=current_user.id,
            selected_at=datetime.now(timezone.utc),
        )
        db.add(selected_plan)

    # Update project status per Section 3.16 & Phase 8 contract
    project.status = "SELECTED"
    db.commit()

    return LayoutSelectResponse(
        projectId=project.id,
        layoutId=layout.id,
        status="SELECTED",
    )


@router.get(
    "/layouts/{layout_id}/blueprint",
    status_code=status.HTTP_200_OK,
    response_model=BlueprintResponse,
)
def get_blueprint(
    layout_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    layout = db.query(Layout).filter(Layout.id == layout_id).first()
    if layout is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="LAYOUT_NOT_FOUND",
        )

    layout_run = db.query(LayoutRun).filter(LayoutRun.id == layout.run_id).first()
    if layout_run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="LAYOUT_NOT_FOUND",
        )

    # Scoped authorization: layout's project must belong to current user
    project = get_project_for_user(db, current_user, layout_run.project_id)

    return generate_blueprint(db, layout, project)



