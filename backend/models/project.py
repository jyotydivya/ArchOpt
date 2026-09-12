from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="DRAFT")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="projects")
    requirements: Mapped[Optional["CampusRequirement"]] = relationship("CampusRequirement", back_populates="project", uselist=False, cascade="all, delete-orphan")
    buildings: Mapped[list["Building"]] = relationship("Building", back_populates="project", cascade="all, delete-orphan")
    constraints: Mapped[list["Constraint"]] = relationship("Constraint", back_populates="project", cascade="all, delete-orphan")
    layout_runs: Mapped[list["LayoutRun"]] = relationship("LayoutRun", back_populates="project", cascade="all, delete-orphan")
    selected_plans: Mapped[list["SelectedPlan"]] = relationship("SelectedPlan", back_populates="project", cascade="all, delete-orphan")
