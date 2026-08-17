from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Index, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from app.models.inspection import Inspection
    from app.models.inspection_image import InspectionImage


class DamageDetection(Base):
    __tablename__ = "damage_detections"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    inspection_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("inspections.id", ondelete="CASCADE"),
        nullable=False,
    )
    image_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("inspection_images.id", ondelete="CASCADE"),
        nullable=False,
    )
    damage_type: Mapped[str] = mapped_column(String(30), nullable=False)
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    bbox_x1: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    bbox_y1: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    bbox_x2: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    bbox_y2: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    severity: Mapped[str] = mapped_column(String(30), nullable=False)
    review_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending",
    )
    reviewed_damage_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    reviewed_severity: Mapped[str | None] = mapped_column(String(30), nullable=True)
    inspector_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    detected_by_model: Mapped[str] = mapped_column(String(120), nullable=False)
    model_version: Mapped[str] = mapped_column(String(80), nullable=False)
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

    inspection: Mapped["Inspection"] = relationship(
        "Inspection",
        back_populates="damage_detections",
    )
    image: Mapped["InspectionImage"] = relationship(
        "InspectionImage",
        back_populates="damage_detections",
    )

    __table_args__ = (
        CheckConstraint(
            "damage_type IN ('dent', 'scratch', 'broken_glass', 'bumper_damage')",
            name="ck_damage_detections_damage_type",
        ),
        CheckConstraint(
            "reviewed_damage_type IS NULL OR reviewed_damage_type IN "
            "('dent', 'scratch', 'broken_glass', 'bumper_damage')",
            name="ck_damage_detections_reviewed_damage_type",
        ),
        CheckConstraint(
            "confidence >= 0 AND confidence <= 1",
            name="ck_damage_detections_confidence",
        ),
        CheckConstraint(
            "bbox_x1 >= 0 AND bbox_y1 >= 0 AND bbox_x2 >= 0 AND bbox_y2 >= 0",
            name="ck_damage_detections_bbox_non_negative",
        ),
        CheckConstraint(
            "bbox_x2 > bbox_x1 AND bbox_y2 > bbox_y1",
            name="ck_damage_detections_bbox_order",
        ),
        CheckConstraint(
            "severity IN ('low', 'medium', 'high')",
            name="ck_damage_detections_severity",
        ),
        CheckConstraint(
            "reviewed_severity IS NULL OR reviewed_severity IN ('low', 'medium', 'high')",
            name="ck_damage_detections_reviewed_severity",
        ),
        CheckConstraint(
            "review_status IN ('pending', 'approved', 'rejected', 'edited')",
            name="ck_damage_detections_review_status",
        ),
        CheckConstraint(
            "length(trim(detected_by_model)) > 0 AND length(trim(model_version)) > 0",
            name="ck_damage_detections_model_not_blank",
        ),
        Index("ix_damage_detections_inspection_id", "inspection_id"),
        Index("ix_damage_detections_image_id", "image_id"),
        Index("ix_damage_detections_damage_type", "damage_type"),
        Index("ix_damage_detections_severity", "severity"),
        Index("ix_damage_detections_review_status", "review_status"),
    )
