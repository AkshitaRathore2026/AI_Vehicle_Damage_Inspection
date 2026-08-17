"""Register ORM models for metadata discovery.

This module imports models so SQLAlchemy and future Alembic migrations can see
their table metadata. Importing it does not create, alter, or drop tables.
"""

from app.db.database import Base
from app.models.audit_log import AuditLog
from app.models.damage_detection import DamageDetection
from app.models.inspection import Inspection
from app.models.inspection_image import InspectionImage
from app.models.report import Report
from app.models.user import User
from app.models.vehicle import Vehicle

__all__ = [
    "AuditLog",
    "Base",
    "DamageDetection",
    "Inspection",
    "InspectionImage",
    "Report",
    "User",
    "Vehicle",
]
