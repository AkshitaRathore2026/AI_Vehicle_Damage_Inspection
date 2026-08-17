from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import and_, func, or_, select, true
from sqlalchemy.orm import Session

from app.models.damage_detection import DamageDetection
from app.models.inspection import Inspection
from app.models.user import User
from app.schemas.inspection import InspectionCreate, InspectionUpdate
from app.services.vehicle_service import get_vehicle_or_404

STATUS_FLOW = {
    "draft": "ai_processing",
    "ai_processing": "under_review",
    "under_review": "completed",
}


def _inspection_not_found() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={
            "success": False,
            "message": "Inspection not found.",
            "error": "inspection_not_found",
        },
    )


def _invalid_transition(current_status: str, next_status: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail={
            "success": False,
            "message": f"Cannot move inspection from {current_status} to {next_status}.",
            "error": "invalid_inspection_state",
        },
    )


def _inspection_scope(current_user: User):
    if current_user.role == "admin":
        return true()
    return Inspection.inspector_id == current_user.id


def _resolve_inspector_id(
    db: Session,
    payload_inspector_id: int | None,
    current_user: User,
) -> int:
    if current_user.role != "admin":
        return current_user.id

    inspector_id = payload_inspector_id or current_user.id
    inspector = db.get(User, inspector_id)
    if inspector is None or not inspector.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "message": "Assigned inspector not found or inactive.",
                "error": "inspector_not_found",
            },
        )
    if inspector.role not in {"admin", "inspector"}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "success": False,
                "message": "Assigned user cannot inspect vehicles.",
                "error": "invalid_inspector_role",
            },
        )
    return inspector.id


def _ensure_can_complete(db: Session, inspection: Inspection) -> None:
    total_detections = (
        db.scalar(
            select(func.count())
            .select_from(DamageDetection)
            .where(DamageDetection.inspection_id == inspection.id)
        )
        or 0
    )
    pending_detections = (
        db.scalar(
            select(func.count())
            .select_from(DamageDetection)
            .where(
                and_(
                    DamageDetection.inspection_id == inspection.id,
                    DamageDetection.review_status == "pending",
                )
            )
        )
        or 0
    )

    if not inspection.inspector_notes or not inspection.inspector_notes.strip():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "success": False,
                "message": "Inspection notes are required before completion.",
                "error": "inspection_notes_required",
            },
        )
    if total_detections == 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "success": False,
                "message": "Inspection cannot be completed before AI detections are reviewed.",
                "error": "inspection_review_required",
            },
        )
    if pending_detections > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "success": False,
                "message": "Inspection cannot be completed while detections are pending review.",
                "error": "pending_detection_reviews",
            },
        )


def _apply_status_transition(
    db: Session,
    inspection: Inspection,
    next_status: str,
) -> None:
    current_status = inspection.status
    if next_status == current_status:
        return
    if STATUS_FLOW.get(current_status) != next_status:
        raise _invalid_transition(current_status, next_status)
    if next_status == "completed":
        _ensure_can_complete(db, inspection)
        inspection.completed_at = datetime.now(UTC)
    inspection.status = next_status


def create_inspection(
    db: Session,
    payload: InspectionCreate,
    current_user: User,
) -> Inspection:
    get_vehicle_or_404(db, payload.vehicle_id, current_user)
    inspector_id = _resolve_inspector_id(db, payload.inspector_id, current_user)

    inspection = Inspection(
        vehicle_id=payload.vehicle_id,
        inspector_id=inspector_id,
        status="draft",
        overall_condition=payload.overall_condition,
        inspector_notes=payload.inspector_notes,
    )
    if payload.inspection_date is not None:
        inspection.inspection_date = payload.inspection_date

    db.add(inspection)
    db.commit()
    db.refresh(inspection)
    return inspection


def get_inspection_or_404(
    db: Session,
    inspection_id: int,
    current_user: User,
) -> Inspection:
    statement = select(Inspection).where(
        and_(Inspection.id == inspection_id, _inspection_scope(current_user))
    )
    inspection = db.scalar(statement)
    if inspection is None:
        raise _inspection_not_found()
    return inspection


def list_inspections(
    db: Session,
    current_user: User,
    page: int,
    page_size: int,
    status_filter: str | None = None,
    vehicle_id: int | None = None,
) -> tuple[list[Inspection], int]:
    filters = [_inspection_scope(current_user)]
    if status_filter:
        filters.append(Inspection.status == status_filter)
    if vehicle_id is not None:
        filters.append(Inspection.vehicle_id == vehicle_id)

    where_clause = and_(*filters)
    total = db.scalar(select(func.count()).select_from(Inspection).where(where_clause)) or 0
    offset = (page - 1) * page_size
    statement = (
        select(Inspection)
        .where(where_clause)
        .order_by(Inspection.inspection_date.desc(), Inspection.id.desc())
        .offset(offset)
        .limit(page_size)
    )
    return list(db.scalars(statement).all()), total


def update_inspection(
    db: Session,
    inspection_id: int,
    payload: InspectionUpdate,
    current_user: User,
) -> Inspection:
    inspection = get_inspection_or_404(db, inspection_id, current_user)
    update_data = payload.model_dump(exclude_unset=True)

    if "status" in update_data and update_data["status"] is not None:
        _apply_status_transition(db, inspection, update_data.pop("status"))

    for field, value in update_data.items():
        setattr(inspection, field, value)

    db.commit()
    db.refresh(inspection)
    return inspection
