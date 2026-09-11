from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.config import settings
from backend.models.building import Building
from backend.models.constraint import Constraint
from backend.models.layout import Layout
from backend.models.layout_run import LayoutRun
from backend.models.project import Project
from backend.models.requirement import CampusRequirement
from backend.schemas.layout import LayoutRunCreateRequest
from backend.services.ml_bridge import run_real_pipeline


def mock_generate(
    site_width: float = 300.0,
    site_height: float = 300.0,
    buildings: Optional[list[Any]] = None,
    top_k: int = 5,
) -> list[dict[str, Any]]:
    """
    Deterministic contract-compliant mock candidate layout generator.
    Generates top_k mock layouts without ML or optimization algorithms.
    Conforms to Data Contract 6 (CandidateLayout) and Contract 8 (RankedLayout).
    """
    placed_buildings_base = []
    if buildings:
        for i, b in enumerate(buildings):
            b_id = getattr(b, "id", None) or (b.get("id", i + 1) if isinstance(b, dict) else i + 1)
            x_pos = round(50.0 + (i * 60.0) % max(1.0, site_width - 80.0), 1)
            y_pos = round(50.0 + (i * 40.0) % max(1.0, site_height - 60.0), 1)
            placed_buildings_base.append({
                "buildingId": b_id,
                "x": x_pos,
                "y": y_pos,
                "rotation": 0.0,
            })
    else:
        placed_buildings_base = [
            {
                "buildingId": 1,
                "x": 50.0,
                "y": 80.0,
                "rotation": 0.0,
            }
        ]

    mock_layouts: list[dict[str, Any]] = []
    for rank in range(1, top_k + 1):
        candidate_buildings = [
            {
                "buildingId": pb["buildingId"],
                "x": round((pb["x"] + (rank - 1) * 5.0) % max(1.0, site_width - 20.0), 1),
                "y": round((pb["y"] + (rank - 1) * 5.0) % max(1.0, site_height - 20.0), 1),
                "rotation": 0.0,
            }
            for pb in placed_buildings_base
        ]

        layout_dict = {
            "candidateId": f"mock-{rank:03d}",
            "rank": rank,
            "feasible": True,
            "layout": {
                "candidateId": f"mock-{rank:03d}",
                "siteWidth": site_width,
                "siteHeight": site_height,
                "buildings": candidate_buildings,
            },
            "metrics": {
                "landUtilization": round(0.70 + 0.01 * rank, 2),
                "greenRatio": round(0.25 - 0.01 * rank, 2),
                "parkingRatio": 0.12,
                "accessibilityScore": round(0.85 - 0.01 * rank, 2),
                "roadEfficiency": round(0.80 - 0.01 * rank, 2),
                "constraintScore": 1.0,
            },
        }
        mock_layouts.append(layout_dict)

    return mock_layouts


def generate_layout_run(
    db: Session,
    project: Project,
    payload: LayoutRunCreateRequest,
) -> tuple[LayoutRun, list[Layout]]:
    """
    Orchestrates layout generation for a project using the mock pipeline.
    Validates requirements and buildings, creates a LayoutRun record,
    generates top_k mock layouts, and persists Layout records.
    """
    requirements = (
        db.query(CampusRequirement)
        .filter(CampusRequirement.project_id == project.id)
        .first()
    )
    if requirements is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="INVALID_REQUIREMENTS",
        )

    buildings = (
        db.query(Building)
        .filter(Building.project_id == project.id)
        .all()
    )
    if not buildings:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="INVALID_REQUIREMENTS",
        )

    pipeline_mode = getattr(settings, "PIPELINE_MODE", "mock").lower()

    if pipeline_mode == "real":
        constraints = (
            db.query(Constraint)
            .filter(Constraint.project_id == project.id)
            .all()
        )
        campus_data = {
            "projectId": project.id,
            "siteWidth": requirements.site_width,
            "siteHeight": requirements.site_height,
            "minGreenPercent": requirements.min_green_percent,
            "minParkingPercent": requirements.min_parking_percent,
            "minRoadWidth": requirements.min_road_width,
            "minBuildingGap": requirements.min_building_gap,
            "entrances": requirements.entrance_data or [],
            "buildings": [
                {
                    "id": b.id,
                    "name": b.name,
                    "type": b.type,
                    "zone": b.zone,
                    "width": b.width,
                    "depth": b.depth,
                    "height": b.height,
                    "floorCount": b.floor_count,
                    "requiredCount": b.required_count,
                }
                for b in buildings
            ],
            "constraints": [
                {
                    "id": c.id,
                    "type": c.constraint_type,
                    "sourceId": c.source_id,
                    "targetId": c.target_id,
                    "value": c.value,
                    "operator": c.operator,
                    "priority": c.priority,
                }
                for c in constraints
            ],
        }
        requirements_dict = {
            "projectId": project.id,
            "siteWidth": requirements.site_width,
            "siteHeight": requirements.site_height,
            "minGreenPercent": requirements.min_green_percent,
            "minParkingPercent": requirements.min_parking_percent,
            "minRoadWidth": requirements.min_road_width,
            "minBuildingGap": requirements.min_building_gap,
            "entrances": requirements.entrance_data or [],
        }
        constraints_list = campus_data["constraints"]

        # If run_real_pipeline fails, it raises HTTPException(422, "GENERATION_FAILED")
        ranked_candidates = run_real_pipeline(
            campus_data=campus_data,
            requirements_dict=requirements_dict,
            constraints_list=constraints_list,
            candidate_count=payload.candidate_count,
            top_k=payload.top_k,
        )

        layout_run = LayoutRun(
            project_id=project.id,
            algorithm=payload.algorithm,
            population_size=payload.candidate_count,
            generation_count=payload.top_k,
            status="COMPLETED",
            completed_at=datetime.now(timezone.utc),
        )
        db.add(layout_run)
        db.commit()
        db.refresh(layout_run)

        layout_records: list[Layout] = []
        for item in ranked_candidates:
            layout_json_data = item.get("layout") or {
                "candidateId": item["candidateId"],
                "siteWidth": requirements.site_width,
                "siteHeight": requirements.site_height,
                "buildings": item["buildings"],
            }
            layout_record = Layout(
                run_id=layout_run.id,
                rank=item["rank"],
                feasible=item["feasible"],
                layout_json=layout_json_data,
                metrics_json=item["metrics"],
            )
            db.add(layout_record)
            layout_records.append(layout_record)

        db.commit()
        return layout_run, layout_records

    layout_run = LayoutRun(
        project_id=project.id,
        algorithm=payload.algorithm,
        population_size=payload.candidate_count,
        generation_count=payload.top_k,
        status="COMPLETED",
        completed_at=datetime.now(timezone.utc),
    )
    db.add(layout_run)
    db.commit()
    db.refresh(layout_run)

    mock_candidates = mock_generate(
        site_width=requirements.site_width,
        site_height=requirements.site_height,
        buildings=buildings,
        top_k=payload.top_k,
    )

    layout_records: list[Layout] = []
    for item in mock_candidates:
        layout_record = Layout(
            run_id=layout_run.id,
            rank=item["rank"],
            feasible=item["feasible"],
            layout_json=item["layout"],
            metrics_json=item["metrics"],
        )
        db.add(layout_record)
        layout_records.append(layout_record)

    db.commit()
    return layout_run, layout_records
