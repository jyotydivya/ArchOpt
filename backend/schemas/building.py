from typing import List
from pydantic import BaseModel, ConfigDict, Field


class BaseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class BuildingCreateRequest(BaseSchema):
    name: str
    type: str
    zone: str
    width: float
    depth: float
    height: float
    floor_count: int = Field(..., alias="floorCount")
    required_count: int = Field(1, alias="requiredCount")


class BuildingResponse(BaseSchema):
    id: int
    project_id: int = Field(..., alias="projectId")
    name: str
    type: str
    zone: str
    width: float
    depth: float
    height: float
    floor_count: int = Field(..., alias="floorCount")
    required_count: int = Field(1, alias="requiredCount")


class BuildingListResponse(BaseSchema):
    buildings: List[BuildingResponse]
