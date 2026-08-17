from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.user import User


def add_audit_log(
    db: Session,
    current_user: User,
    action: str,
    entity_type: str,
    entity_id: int | None,
    description: str | None = None,
    ip_address: str | None = None,
) -> AuditLog:
    audit_log = AuditLog(
        user_id=current_user.id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        description=description,
        ip_address=ip_address,
    )
    db.add(audit_log)
    return audit_log
