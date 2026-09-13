from typing import Optional, List
from pydantic import Field
from backend.schemas.base import BaseSchema


class EntranceSchema(BaseSchema):
    x: float
    y: float
    width: float


class RequirementsSaveRequest(BaseSchema):
    site_width: float = Field(..., alias="siteWidth")
    site_height: float = Field(..., alias="siteHeight")
    min_green_percent: float = Field(..., alias="minGreenPercent")
    min_parking_percent: float = Field(..., alias="minParkingPercent")
    min_road_width: float = Field(..., alias="minRoadWidth")
    min_building_gap: float = Field(..., alias="minBuildingGap")
    entrances: List[EntranceSchema] = Field(default_factory=list)


class RequirementsResponse(BaseSchema):
    id: Optional[int] = None
    project_id: int = Field(..., alias="projectId")
    site_width: float = Field(..., alias="siteWidth")
    site_height: float = Field(..., alias="siteHeight")
    min_green_percent: float = Field(..., alias="minGreenPercent")
    min_parking_percent: float = Field(..., alias="minParkingPercent")
    min_road_width: float = Field(..., alias="minRoadWidth")
    min_building_gap: float = Field(..., alias="minBuildingGap")
    entrances: List[EntranceSchema] = Field(default_factory=list)
