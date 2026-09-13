from typing import List
from pydantic import Field
from backend.schemas.base import BaseSchema


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
