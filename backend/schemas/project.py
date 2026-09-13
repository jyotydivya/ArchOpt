from typing import Optional
from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class ProjectCreateRequest(BaseSchema):
    name: str
    description: Optional[str] = None


class ProjectUpdateRequest(BaseSchema):
    name: str
    description: Optional[str] = None


class ProjectResponse(BaseSchema):
    id: int
    name: str
    description: Optional[str] = None
    status: str = "DRAFT"
