from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_inspector_or_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.inspection import (
    InspectionCreate,
    InspectionListResponse,
    InspectionResponse,
    InspectionUpdate,
)
from app.services.inspection_service import (
    create_inspection,
    get_inspection_or_404,
    list_inspections,
    update_inspection,
)

router = APIRouter(prefix="/inspections", tags=["Inspections"])


@router.get("", response_model=InspectionListResponse)
def read_inspections(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    status_filter: str | None = Query(
        default=None,
        alias="status",
        pattern="^(draft|ai_processing|under_review|completed)$",
    ),
    vehicle_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_inspector_or_admin),
) -> dict[str, object]:
    inspections, total = list_inspections(
        db,
        current_user,
        page,
        page_size,
        status_filter,
        vehicle_id,
    )
    return {
        "success": True,
        "message": "Inspections retrieved successfully.",
        "data": {
            "items": inspections,
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    }


@router.post(
    "",
    response_model=InspectionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_inspection_endpoint(
    payload: InspectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_inspector_or_admin),
) -> dict[str, object]:
    inspection = create_inspection(db, payload, current_user)
    return {
        "success": True,
        "message": "Inspection created successfully.",
        "data": inspection,
    }


@router.get("/{inspection_id}", response_model=InspectionResponse)
def read_inspection(
    inspection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_inspector_or_admin),
) -> dict[str, object]:
    inspection = get_inspection_or_404(db, inspection_id, current_user)
    return {
        "success": True,
        "message": "Inspection retrieved successfully.",
        "data": inspection,
    }


@router.put("/{inspection_id}", response_model=InspectionResponse)
def update_inspection_endpoint(
    inspection_id: int,
    payload: InspectionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_inspector_or_admin),
) -> dict[str, object]:
    inspection = update_inspection(db, inspection_id, payload, current_user)
    return {
        "success": True,
        "message": "Inspection updated successfully.",
        "data": inspection,
    }
