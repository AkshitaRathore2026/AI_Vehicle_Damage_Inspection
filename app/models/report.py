from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from app.models.inspection import Inspection
    from app.models.user import User


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    inspection_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("inspections.id", ondelete="CASCADE"),
        nullable=False,
    )
    report_number: Mapped[str] = mapped_column(String(80), nullable=False)
    report_path: Mapped[str] = mapped_column(Text, nullable=False)
    generated_by: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    inspection: Mapped["Inspection"] = relationship(
        "Inspection",
        back_populates="report",
    )
    generator: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="reports_generated",
        foreign_keys=[generated_by],
    )

    __table_args__ = (
        CheckConstraint(
            "length(trim(report_number)) > 0",
            name="ck_reports_report_number_not_blank",
        ),
        CheckConstraint(
            "length(trim(report_path)) > 0",
            name="ck_reports_report_path_not_blank",
        ),
        Index("ux_reports_inspection_id", "inspection_id", unique=True),
        Index("ux_reports_report_number", "report_number", unique=True),
        Index("ix_reports_generated_by", "generated_by"),
        Index("ix_reports_generated_at", generated_at.desc()),
    )
