from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import get_current_inspector_or_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.review import DetectionReviewResponse, DetectionReviewUpdate
from app.services.review_service import review_detection

router = APIRouter(prefix="/reviews", tags=["Human Review"])


@router.put("/{detection_id}", response_model=DetectionReviewResponse)
def review_damage_detection(
    detection_id: int,
    payload: DetectionReviewUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_inspector_or_admin),
) -> dict[str, object]:
    ip_address = request.client.host if request.client else None
    detection = review_detection(db, detection_id, payload, current_user, ip_address)
    return {
        "success": True,
        "message": "Detection review saved successfully.",
        "data": detection,
    }
