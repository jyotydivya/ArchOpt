from typing import Optional, List
from pydantic import Field
from backend.schemas.base import BaseSchema


class ConstraintCreateRequest(BaseSchema):
    type: str = Field(..., alias="type")
    source_id: Optional[int] = Field(None, alias="sourceId")
    target_id: Optional[int] = Field(None, alias="targetId")
    value: Optional[float] = Field(None, alias="value")
    operator: Optional[str] = Field(None, alias="operator")
    priority: Optional[str] = Field(None, alias="priority")


class ConstraintResponse(BaseSchema):
    id: int
    type: str = Field(..., alias="type")
    source_id: Optional[int] = Field(None, alias="sourceId")
    target_id: Optional[int] = Field(None, alias="targetId")
    value: Optional[float] = Field(None, alias="value")
    operator: Optional[str] = Field(None, alias="operator")
    priority: Optional[str] = Field(None, alias="priority")


class ConstraintListResponse(BaseSchema):
    constraints: List[ConstraintResponse]
