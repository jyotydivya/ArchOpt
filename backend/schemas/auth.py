from pydantic import Field
from backend.schemas.base import BaseSchema


class UserRegisterRequest(BaseSchema):
    name: str
    email: str
    password: str


class UserRegisterResponse(BaseSchema):
    id: int
    name: str
    email: str
    role: str = "PROJECT_MANAGER"


class UserLoginRequest(BaseSchema):
    email: str
    password: str


class UserAuthSummary(BaseSchema):
    id: int
    name: str
    role: str = "PROJECT_MANAGER"


class UserLoginResponse(BaseSchema):
    access_token: str = Field(..., alias="accessToken")
    token_type: str = Field("Bearer", alias="tokenType")
    user: UserAuthSummary
