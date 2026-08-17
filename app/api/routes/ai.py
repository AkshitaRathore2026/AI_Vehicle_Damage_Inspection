from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_inspector_or_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.detection import AIAnalysisResponse, AIAnalyzeRequest, DetectionListResponse
from app.services.detection_service import (
    list_detections_for_inspection,
    run_ai_analysis,
)

router = APIRouter(prefix="/ai", tags=["AI Analysis"])


@router.post(
    "/analyze",
    response_model=AIAnalysisResponse,
    status_code=status.HTTP_201_CREATED,
)
def analyze_inspection(
    payload: AIAnalyzeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_inspector_or_admin),
) -> dict[str, object]:
    detections, processed_images = run_ai_analysis(db, payload.inspection_id, current_user)
    return {
        "success": True,
        "message": "AI analysis completed successfully.",
        "data": {
            "inspection_id": payload.inspection_id,
            "processed_images": processed_images,
            "detections_created": len(detections),
            "detections": detections,
        },
    }


@router.get(
    "/detections/{inspection_id}",
    response_model=DetectionListResponse,
)
def read_detections(
    inspection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_inspector_or_admin),
) -> dict[str, object]:
    detections = list_detections_for_inspection(db, inspection_id, current_user)
    return {
        "success": True,
        "message": "Detections retrieved successfully.",
        "data": {
            "inspection_id": inspection_id,
            "items": detections,
            "total": len(detections),
        },
    }
