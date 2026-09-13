from typing import List, Any
from pydantic import BaseModel, ConfigDict, Field
from backend.schemas.requirement import EntranceSchema
from backend.schemas.layout import SiteDimensionSchema


class BaseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


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
