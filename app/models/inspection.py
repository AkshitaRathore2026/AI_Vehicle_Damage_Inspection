from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from app.models.damage_detection import DamageDetection
    from app.models.inspection_image import InspectionImage
    from app.models.report import Report
    from app.models.user import User
    from app.models.vehicle import Vehicle


class Inspection(Base):
    __tablename__ = "inspections"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("vehicles.id", ondelete="RESTRICT"),
        nullable=False,
    )
    inspector_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="draft")
    overall_condition: Mapped[str | None] = mapped_column(String(30), nullable=True)
    inspector_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    inspection_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    vehicle: Mapped["Vehicle"] = relationship("Vehicle", back_populates="inspections")
    inspector: Mapped["User"] = relationship(
        "User",
        back_populates="inspections",
        foreign_keys=[inspector_id],
    )
    images: Mapped[list["InspectionImage"]] = relationship(
        "InspectionImage",
        back_populates="inspection",
        cascade="all, delete-orphan",
    )
    damage_detections: Mapped[list["DamageDetection"]] = relationship(
        "DamageDetection",
        back_populates="inspection",
        cascade="all, delete-orphan",
    )
    report: Mapped[Optional["Report"]] = relationship(
        "Report",
        back_populates="inspection",
        cascade="all, delete-orphan",
        uselist=False,
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'ai_processing', 'under_review', 'completed')",
            name="ck_inspections_status",
        ),
        CheckConstraint(
            "overall_condition IS NULL OR overall_condition IN ('low', 'medium', 'high')",
            name="ck_inspections_overall_condition",
        ),
        CheckConstraint(
            "(status = 'completed' AND completed_at IS NOT NULL) OR "
            "(status <> 'completed')",
            name="ck_inspections_completed_at",
        ),
        Index("ix_inspections_vehicle_id", "vehicle_id"),
        Index("ix_inspections_inspector_id", "inspector_id"),
        Index("ix_inspections_status", "status"),
        Index("ix_inspections_inspection_date", inspection_date.desc()),
    )
