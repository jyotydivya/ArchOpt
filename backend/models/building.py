from typing import Optional, Any
from sqlalchemy import String, Integer, Float, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database import Base


class Building(Base):
    __tablename__ = "buildings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(100), nullable=False)
    zone: Mapped[str] = mapped_column(String(100), nullable=False)
    width: Mapped[float] = mapped_column(Float, nullable=False)
    depth: Mapped[float] = mapped_column(Float, nullable=False)
    height: Mapped[float] = mapped_column(Float, nullable=False)
    floor_count: Mapped[int] = mapped_column(Integer, nullable=False)
    required_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    metadata_: Mapped[Optional[Any]] = mapped_column("metadata", JSONB, nullable=True, default=dict)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="buildings")
