from datetime import datetime
from typing import Optional
from sqlalchemy import Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database import Base


class SelectedPlan(Base):
    __tablename__ = "selected_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    layout_id: Mapped[int] = mapped_column(Integer, ForeignKey("layouts.id", ondelete="CASCADE"), nullable=False)
    selected_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    selected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="selected_plans")
    layout: Mapped["Layout"] = relationship("Layout", back_populates="selected_plans")
    selected_by_user: Mapped[Optional["User"]] = relationship("User", back_populates="selected_plans")
