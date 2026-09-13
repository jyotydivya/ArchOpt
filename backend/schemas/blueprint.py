from typing import List, Any
from pydantic import Field
from backend.schemas.base import BaseSchema
from backend.schemas.requirement import EntranceSchema
from backend.schemas.layout import SiteDimensionSchema


class BlueprintBuildingSchema(BaseSchema):
    id: int
    name: str
    type: str
    zone: str
    x: float
    y: float
    width: float
    depth: float
    height: float
    rotation: float = 0.0
    floor_count: int = Field(..., alias="floorCount")


class BlueprintResponse(BaseSchema):
    project_id: int = Field(..., alias="projectId")
    layout_id: int = Field(..., alias="layoutId")
    site: SiteDimensionSchema
    buildings: List[BlueprintBuildingSchema] = Field(default_factory=list)
    roads: List[Any] = Field(default_factory=list)
    green_areas: List[Any] = Field(default_factory=list, alias="greenAreas")
    parking_areas: List[Any] = Field(default_factory=list, alias="parkingAreas")
    entrances: List[EntranceSchema] = Field(default_factory=list)
