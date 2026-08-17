from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import and_, select, true
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.damage_detection import DamageDetection
from app.models.inspection import Inspection
from app.models.user import User
from app.schemas.review import DetectionReviewUpdate
from app.services.audit_service import add_audit_log


def _review_error(
    status_code: int,
    message: str,
    error: str,
) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={
            "success": False,
            "message": message,
            "error": error,
        },
    )


def _detection_scope(current_user: User):
    if current_user.role == "admin":
        return true()
    return Inspection.inspector_id == current_user.id


def get_detection_for_review_or_404(
    db: Session,
    detection_id: int,
    current_user: User,
) -> DamageDetection:
    statement = (
        select(DamageDetection)
        .join(Inspection, DamageDetection.inspection_id == Inspection.id)
        .where(and_(DamageDetection.id == detection_id, _detection_scope(current_user)))
    )
    detection = db.scalar(statement)
    if detection is None:
        raise _review_error(
            status.HTTP_404_NOT_FOUND,
            "Damage detection not found.",
            "detection_not_found",
        )
    return detection


def review_detection(
    db: Session,
    detection_id: int,
    payload: DetectionReviewUpdate,
    current_user: User,
    ip_address: str | None = None,
) -> DamageDetection:
    detection = get_detection_for_review_or_404(db, detection_id, current_user)
    if detection.inspection.status != "under_review":
        raise _review_error(
            status.HTTP_409_CONFLICT,
            "Detections can only be reviewed while the inspection is under_review.",
            "invalid_inspection_state",
        )

    previous_status = detection.review_status

    try:
        detection.review_status = payload.review_status
        detection.inspector_notes = payload.inspector_notes
        detection.updated_at = datetime.now(UTC)

        if payload.review_status == "edited":
            detection.reviewed_damage_type = (
                payload.reviewed_damage_type or detection.damage_type
            )
            detection.reviewed_severity = payload.reviewed_severity or detection.severity
        else:
            detection.reviewed_damage_type = None
            detection.reviewed_severity = None

        add_audit_log(
            db=db,
            current_user=current_user,
            action=f"detection_{payload.review_status}",
            entity_type="damage_detection",
            entity_id=detection.id,
            description=(
                f"Detection review changed from {previous_status} "
                f"to {payload.review_status}."
            ),
            ip_address=ip_address,
        )

        db.commit()
        db.refresh(detection)
    except SQLAlchemyError:
        db.rollback()
        raise

    return detection
