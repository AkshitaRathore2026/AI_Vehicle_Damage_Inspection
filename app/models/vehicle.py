from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from app.models.inspection import Inspection
    from app.models.user import User


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    vehicle_number: Mapped[str] = mapped_column(String(50), nullable=False)
    make: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    customer_name: Mapped[str] = mapped_column(String(150), nullable=False)
    vin: Mapped[str | None] = mapped_column(String(17), nullable=True)
    created_by: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
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

    creator: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="vehicles_created",
        foreign_keys=[created_by],
    )
    inspections: Mapped[list["Inspection"]] = relationship(
        "Inspection",
        back_populates="vehicle",
    )

    __table_args__ = (
        CheckConstraint("year BETWEEN 1886 AND 2100", name="ck_vehicles_year"),
        CheckConstraint(
            "length(trim(vehicle_number)) > 0",
            name="ck_vehicles_vehicle_number_not_blank",
        ),
        CheckConstraint("length(trim(make)) > 0", name="ck_vehicles_make_not_blank"),
        CheckConstraint("length(trim(model)) > 0", name="ck_vehicles_model_not_blank"),
        CheckConstraint(
            "length(trim(customer_name)) > 0",
            name="ck_vehicles_customer_name_not_blank",
        ),
        CheckConstraint(
            "vin IS NULL OR vin ~* '^[A-HJ-NPR-Z0-9]{17}$'",
            name="ck_vehicles_vin_format",
        ),
        Index("ux_vehicles_vehicle_number_lower", func.lower(vehicle_number), unique=True),
        Index(
            "ux_vehicles_vin_lower",
            func.lower(vin),
            unique=True,
            postgresql_where=vin.is_not(None),
        ),
        Index("ix_vehicles_created_by", "created_by"),
        Index("ix_vehicles_make_model", "make", "model"),
        Index("ix_vehicles_customer_name", "customer_name"),
    )
