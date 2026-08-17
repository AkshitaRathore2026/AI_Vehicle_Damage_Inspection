from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from app.models.damage_detection import DamageDetection
    from app.models.inspection import Inspection


class InspectionImage(Base):
    __tablename__ = "inspection_images"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    inspection_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("inspections.id", ondelete="CASCADE"),
        nullable=False,
    )
    image_view: Mapped[str] = mapped_column(String(30), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_path: Mapped[str] = mapped_column(Text, nullable=False)
    processed_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    inspection: Mapped["Inspection"] = relationship(
        "Inspection",
        back_populates="images",
    )
    damage_detections: Mapped[list["DamageDetection"]] = relationship(
        "DamageDetection",
        back_populates="image",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint(
            "image_view IN ('front', 'rear', 'left', 'right', 'closeup_damage')",
            name="ck_inspection_images_image_view",
        ),
        CheckConstraint(
            "file_type IN ('image/jpeg', 'image/png')",
            name="ck_inspection_images_file_type",
        ),
        CheckConstraint("file_size > 0", name="ck_inspection_images_file_size"),
        CheckConstraint(
            "length(trim(original_filename)) > 0",
            name="ck_inspection_images_original_filename_not_blank",
        ),
        CheckConstraint(
            "length(trim(stored_filename)) > 0",
            name="ck_inspection_images_stored_filename_not_blank",
        ),
        CheckConstraint(
            "length(trim(original_path)) > 0",
            name="ck_inspection_images_original_path_not_blank",
        ),
        Index("ux_inspection_images_stored_filename", "stored_filename", unique=True),
        Index("ix_inspection_images_inspection_id", "inspection_id"),
        Index("ix_inspection_images_image_view", "image_view"),
    )
