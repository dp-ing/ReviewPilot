from __future__ import annotations

from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, Integer, DateTime, Boolean, Float, ForeignKey, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base

if TYPE_CHECKING:
    from app.models.repository import Repository


class RepoConfig(Base):
    __tablename__ = "repo_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    repository_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("repositories.id"), unique=True, nullable=False
    )
    auto_review: Mapped[bool] = mapped_column(Boolean, default=True)
    enabled_categories: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)
    ignore_patterns: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)
    ignore_rule_ids: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)
    review_language: Mapped[str] = mapped_column(String(16), default="zh-CN")
    max_files_per_review: Mapped[int] = mapped_column(Integer, default=50)
    confidence_threshold: Mapped[float] = mapped_column(Float, default=0.6)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    repository: Mapped["Repository"] = relationship("Repository")
