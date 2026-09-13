from typing import Optional, Any
from sqlalchemy import Float, Integer, ForeignKey, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database import Base


class CampusRequirement(Base):
    __tablename__ = "campus_requirements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, unique=True)
    site_width: Mapped[float] = mapped_column(Float, nullable=False)
    site_height: Mapped[float] = mapped_column(Float, nullable=False)
    total_area: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    min_green_percent: Mapped[float] = mapped_column(Float, nullable=False)
    min_parking_percent: Mapped[float] = mapped_column(Float, nullable=False)
    min_road_width: Mapped[float] = mapped_column(Float, nullable=False)
    min_building_gap: Mapped[float] = mapped_column(Float, nullable=False)
    entrance_data: Mapped[Any] = mapped_column(JSONB, nullable=False, default=list)
    road_data: Mapped[Any] = mapped_column(JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb"))

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="requirements")
