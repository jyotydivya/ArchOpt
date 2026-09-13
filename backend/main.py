from fastapi import FastAPI, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api.auth import router as auth_router
from backend.api.layouts import router as layouts_router
from backend.api.projects import router as projects_router
from backend.config import settings

from fastapi.openapi.utils import get_openapi

app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API for AI Campus Planner",
    version="1.0.0",
)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    components = openapi_schema.setdefault("components", {})
    schemas = components.setdefault("schemas", {})
    schemas["ValidationErrorResponse"] = {
        "title": "ValidationErrorResponse",
        "type": "object",
        "properties": {
            "detail": {
                "title": "Detail",
                "type": "string",
                "example": "VALIDATION_ERROR",
            }
        },
        "required": ["detail"],
    }
    schemas["GenerationFailedResponse"] = {
        "title": "GenerationFailedResponse",
        "type": "object",
        "properties": {
            "detail": {
                "title": "Detail",
                "type": "string",
                "example": "GENERATION_FAILED",
            }
        },
        "required": ["detail"],
    }

    for path, path_item in openapi_schema.get("paths", {}).items():
        for method, operation in path_item.items():
            if not isinstance(operation, dict):
                continue
            responses = operation.get("responses", {})
            if "422" in responses:
                resp_422 = responses["422"]
                if resp_422.get("description") == "Validation Error":
                    del responses["422"]
                    if "400" not in responses:
                        responses["400"] = {
                            "description": "Validation Error",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/ValidationErrorResponse"
                                    }
                                }
                            },
                        }
            if path == "/api/projects/{project_id}/layout-runs" and method.lower() == "post":
                responses["422"] = {
                    "description": "Generation Failed",
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/GenerationFailedResponse"
                            }
                        }
                    },
                }

    schemas.pop("HTTPValidationError", None)
    schemas.pop("ValidationError", None)

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": "VALIDATION_ERROR"},
    )

app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(layouts_router)

# CORS Configuration for local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health_check():
    """Optional development health check endpoint (Not one of the 17 master APIs)."""
    return {
        "status": "ok",
        "app": settings.APP_NAME
    }
