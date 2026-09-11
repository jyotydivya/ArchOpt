from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    APP_NAME: str = "AI Campus Planner Backend"
    DEBUG: bool = True

    # PostgreSQL Database Configuration (Port 5433 for dedicated archopt-postgres container)
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5433/campus_planner"

    # Security & Token Settings (Implementation decisions - configurable defaults)
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # Pipeline mode: "mock" (default) or "real" (requires P1/P2/P3 modules)
    PIPELINE_MODE: str = "mock"

    # CORS Settings for Frontend Development
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]


settings = Settings()
