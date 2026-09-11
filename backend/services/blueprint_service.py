from typing import Any
from sqlalchemy.orm import Session

from backend.models.building import Building
from backend.models.layout import Layout
from backend.models.project import Project
from backend.models.requirement import CampusRequirement
from backend.schemas.blueprint import BlueprintBuildingSchema, BlueprintResponse
from backend.schemas.layout import SiteDimensionSchema
from backend.schemas.requirement import EntranceSchema


def generate_blueprint(db: Session, layout: Layout, project: Project) -> BlueprintResponse:
    """
    Constructs a 3D Blender Blueprint JSON matching Contract 9 and Section 3.17.
    Merges layout candidate building placements (x, y, rotation) with
    project building metadata (name, type, zone, width, depth, height, floorCount)
    and campus requirement site boundaries & entrances.
    """
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
    buildings_list: list[BlueprintBuildingSchema] = []

    for b_pos in candidate_buildings:
        b_id = b_pos.get("buildingId") or b_pos.get("id")
        b_meta = buildings_by_id.get(b_id)
        if b_meta:
            buildings_list.append(
                BlueprintBuildingSchema(
                    id=b_meta.id,
                    name=b_meta.name,
                    type=b_meta.type,
                    zone=b_meta.zone,
                    x=float(b_pos.get("x", 0.0)),
                    y=float(b_pos.get("y", 0.0)),
                    width=float(b_meta.width),
                    depth=float(b_meta.depth),
                    height=float(b_meta.height),
                    rotation=float(b_pos.get("rotation", 0.0)),
                    floorCount=int(b_meta.floor_count),
                )
            )
        else:
            buildings_list.append(
                BlueprintBuildingSchema(
                    id=int(b_id) if b_id is not None else 1,
                    name=f"Building {b_id}",
                    type="generic",
                    zone="general",
                    x=float(b_pos.get("x", 0.0)),
                    y=float(b_pos.get("y", 0.0)),
                    width=60.0,
                    depth=40.0,
                    height=18.0,
                    rotation=float(b_pos.get("rotation", 0.0)),
                    floorCount=4,
                )
            )

    return BlueprintResponse(
        projectId=project.id,
        layoutId=layout.id,
        site=SiteDimensionSchema(width=site_width, height=site_height),
        buildings=buildings_list,
        roads=[],
        greenAreas=[],
        parkingAreas=[],
        entrances=entrances_list,
    )
