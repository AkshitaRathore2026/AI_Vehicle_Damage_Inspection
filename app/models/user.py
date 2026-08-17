from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, CheckConstraint, DateTime, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from app.models.audit_log import AuditLog
    from app.models.inspection import Inspection
    from app.models.report import Report
    from app.models.vehicle import Vehicle


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(String(30), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
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

    vehicles_created: Mapped[list["Vehicle"]] = relationship(
        "Vehicle",
        back_populates="creator",
        foreign_keys="Vehicle.created_by",
    )
    inspections: Mapped[list["Inspection"]] = relationship(
        "Inspection",
        back_populates="inspector",
        foreign_keys="Inspection.inspector_id",
    )
    reports_generated: Mapped[list["Report"]] = relationship(
        "Report",
        back_populates="generator",
        foreign_keys="Report.generated_by",
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="user",
        foreign_keys="AuditLog.user_id",
    )

    __table_args__ = (
        CheckConstraint("role IN ('admin', 'inspector')", name="ck_users_role"),
        CheckConstraint(
            "email ~* '^[A-Z0-9._%+-]+@[A-Z0-9.-]+\\.[A-Z]{2,}$'",
            name="ck_users_email_format",
        ),
        CheckConstraint(
            "length(trim(full_name)) > 0",
            name="ck_users_full_name_not_blank",
        ),
        Index("ux_users_email_lower", func.lower(email), unique=True),
        Index("ix_users_role", "role"),
        Index("ix_users_is_active", "is_active"),
    )
