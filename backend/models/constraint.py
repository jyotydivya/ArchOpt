from typing import Optional, Any
from sqlalchemy import String, Integer, Float, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database import Base


class Constraint(Base):
    __tablename__ = "constraints"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    constraint_type: Mapped[str] = mapped_column(String(100), nullable=False)
    source_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    target_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    operator: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    priority: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    metadata_: Mapped[Optional[Any]] = mapped_column("metadata", JSONB, nullable=True, default=dict)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="constraints")
