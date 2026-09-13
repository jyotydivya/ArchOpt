from typing import Optional, List, Dict, Any
from pydantic import Field
from backend.schemas.base import BaseSchema
from backend.schemas.requirement import EntranceSchema


class LayoutRunCreateRequest(BaseSchema):
    candidate_count: int = Field(100, alias="candidateCount")
    top_k: int = Field(5, alias="topK")
    algorithm: str = Field("GNN_NSGA2", alias="algorithm")


class LayoutRunCreateResponse(BaseSchema):
    run_id: int = Field(..., alias="runId")
    status: str = Field("COMPLETED", alias="status")
    layout_count: int = Field(..., alias="layoutCount")


class LayoutMetricsSchema(BaseSchema):
    land_utilization: float = Field(..., alias="landUtilization")
    green_ratio: float = Field(..., alias="greenRatio")
    parking_ratio: float = Field(0.0, alias="parkingRatio")
    accessibility_score: float = Field(0.0, alias="accessibilityScore")
    road_efficiency: float = Field(0.0, alias="roadEfficiency")
    constraint_score: float = Field(1.0, alias="constraintScore")


class LayoutSummarySchema(BaseSchema):
    id: int
    rank: int
    feasible: bool = True
    metrics: LayoutMetricsSchema


class LayoutListResponse(BaseSchema):
    layouts: List[LayoutSummarySchema]


class SiteDimensionSchema(BaseSchema):
    width: float
    height: float


class CandidateBuildingPosition(BaseSchema):
    building_id: int = Field(..., alias="buildingId")
    x: float
    y: float
    rotation: float = 0.0


class LayoutDetailResponse(BaseSchema):
    id: int
    rank: int
    feasible: bool = True
    site: SiteDimensionSchema
    buildings: List[CandidateBuildingPosition] = Field(default_factory=list)
    roads: List[Any] = Field(default_factory=list)
    green_areas: List[Any] = Field(default_factory=list, alias="greenAreas")
    parking_areas: List[Any] = Field(default_factory=list, alias="parkingAreas")
    entrances: List[EntranceSchema] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)


class LayoutSelectResponse(BaseSchema):
    project_id: int = Field(..., alias="projectId")
    layout_id: int = Field(..., alias="layoutId")
    status: str = Field("SELECTED", alias="status")
