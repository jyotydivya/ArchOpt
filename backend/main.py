from fastapi import FastAPI, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api.auth import router as auth_router
from backend.api.layouts import router as layouts_router
from backend.api.projects import router as projects_router
from backend.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API for AI Campus Planner",
    version="1.0.0",
)


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
