from datetime import datetime
from typing import Any
from sqlalchemy import Integer, Boolean, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database import Base


class Layout(Base):
    __tablename__ = "layouts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    run_id: Mapped[int] = mapped_column(Integer, ForeignKey("layout_runs.id", ondelete="CASCADE"), nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    feasible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    layout_json: Mapped[Any] = mapped_column(JSONB, nullable=False)
    metrics_json: Mapped[Any] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    layout_run: Mapped["LayoutRun"] = relationship("LayoutRun", back_populates="layouts")
    selected_plans: Mapped[list["SelectedPlan"]] = relationship("SelectedPlan", back_populates="layout", cascade="all, delete-orphan")
