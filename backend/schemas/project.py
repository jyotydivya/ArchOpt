from typing import Optional
from backend.schemas.base import BaseSchema


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
