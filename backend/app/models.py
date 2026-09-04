"""ORM models — universal metric/event schema (см. ТЗ §4)."""
from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db import Base

# JSONB is Postgres-only; fall back to generic JSON for sqlite (used in tests).
JSONType = JSONB().with_variant(JSON(), "sqlite")


class Metric(Base):
    __tablename__ = "metrics"
    __table_args__ = (
        CheckConstraint("unit IN ('count','duration','boolean')", name="ck_metrics_unit"),
        CheckConstraint("aggregation IN ('sum','max','last')", name="ck_metrics_aggregation"),
        CheckConstraint("source_type IN ('github','webhook','manual')", name="ck_metrics_source_type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    icon: Mapped[str] = mapped_column(String(16), default="📊")
    color: Mapped[str] = mapped_column(String(16), default="#3fb950")
    unit: Mapped[str] = mapped_column(String(16), default="count")
    aggregation: Mapped[str] = mapped_column(String(16), default="sum")
    source_type: Mapped[str] = mapped_column(String(16), default="manual")
    meta: Mapped[dict] = mapped_column(JSONType, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    events: Mapped[list["MetricEvent"]] = relationship(
        back_populates="metric", cascade="all, delete-orphan"
    )


class MetricEvent(Base):
    __tablename__ = "metric_events"
    __table_args__ = (UniqueConstraint("metric_id", "date", name="uq_metric_event_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    metric_id: Mapped[int] = mapped_column(ForeignKey("metrics.id", ondelete="CASCADE"))
    date: Mapped[date] = mapped_column(Date)
    value: Mapped[float] = mapped_column(Numeric)
    meta: Mapped[dict] = mapped_column(JSONType, default=dict)

    metric: Mapped["Metric"] = relationship(back_populates="events")
