from decimal import Decimal
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.ai.model_loader import get_damage_detector
from app.ai.visualization import draw_detections
from app.core.config import get_settings
from app.models.damage_detection import DamageDetection
from app.models.inspection_image import InspectionImage
from app.models.user import User
from app.services.inspection_service import get_inspection_or_404

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _analysis_error(message: str, error: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail={
            "success": False,
            "message": message,
            "error": error,
        },
    )


def _resolve_project_path(path_value: str) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def _processed_relative_path(inspection_id: int, stored_filename: str) -> Path:
    settings = get_settings()
    processed_root = Path(settings.processed_dir)
    if not processed_root.is_absolute():
        processed_root = PROJECT_ROOT / processed_root
    return processed_root / str(inspection_id) / stored_filename


def run_ai_analysis(
    db: Session,
    inspection_id: int,
    current_user: User,
) -> tuple[list[DamageDetection], int]:
    inspection = get_inspection_or_404(db, inspection_id, current_user)
    if inspection.status not in {"draft", "ai_processing"}:
        raise _analysis_error(
            "AI analysis can only run for draft or ai_processing inspections.",
            "invalid_inspection_state",
        )

    images = list(
        db.scalars(
            select(InspectionImage)
            .where(InspectionImage.inspection_id == inspection.id)
            .order_by(InspectionImage.uploaded_at.asc(), InspectionImage.id.asc())
        ).all()
    )
    if not images:
        raise _analysis_error(
            "At least one uploaded image is required before AI analysis.",
            "inspection_images_required",
        )

    detector = get_damage_detector()
    inspection.status = "ai_processing"
    db.flush()

    processed_paths: list[Path] = []
    detections_to_create: list[DamageDetection] = []

    try:
        db.execute(
            delete(DamageDetection).where(DamageDetection.inspection_id == inspection.id)
        )

        for image in images:
            original_path = _resolve_project_path(image.original_path)
            if not original_path.exists():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "success": False,
                        "message": "Original image file was not found on disk.",
                        "error": "original_image_missing",
                    },
                )

            try:
                detection_results = detector.detect(original_path)
            except FileNotFoundError as exc:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail={
                        "success": False,
                        "message": "AI model file was not found.",
                        "error": "ai_model_missing",
                    },
                ) from exc
            processed_path = _processed_relative_path(
                inspection_id=inspection.id,
                stored_filename=image.stored_filename,
            )
            draw_detections(original_path, detection_results, processed_path)
            processed_paths.append(processed_path)
            image.processed_path = str(processed_path.relative_to(PROJECT_ROOT).as_posix())

            for result in detection_results:
                detections_to_create.append(
                    DamageDetection(
                        inspection_id=inspection.id,
                        image_id=image.id,
                        damage_type=result.damage_type,
                        confidence=Decimal(str(result.confidence)),
                        bbox_x1=Decimal(str(result.bbox_x1)),
                        bbox_y1=Decimal(str(result.bbox_y1)),
                        bbox_x2=Decimal(str(result.bbox_x2)),
                        bbox_y2=Decimal(str(result.bbox_y2)),
                        severity=result.severity,
                        review_status="pending",
                        detected_by_model=result.detected_by_model,
                        model_version=result.model_version,
                    )
                )

        db.add_all(detections_to_create)
        inspection.status = "under_review"
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        for path in processed_paths:
            path.unlink(missing_ok=True)
        raise
    except HTTPException:
        db.rollback()
        for path in processed_paths:
            path.unlink(missing_ok=True)
        raise
    except Exception:
        db.rollback()
        for path in processed_paths:
            path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "success": False,
                "message": "AI inference failed.",
                "error": "ai_inference_failure",
            },
        )

    detections = list(
        db.scalars(
            select(DamageDetection)
            .where(DamageDetection.inspection_id == inspection.id)
            .order_by(DamageDetection.created_at.asc(), DamageDetection.id.asc())
        ).all()
    )
    return detections, len(images)


def list_detections_for_inspection(
    db: Session,
    inspection_id: int,
    current_user: User,
) -> list[DamageDetection]:
    inspection = get_inspection_or_404(db, inspection_id, current_user)
    return list(
        db.scalars(
            select(DamageDetection)
            .where(DamageDetection.inspection_id == inspection.id)
            .order_by(DamageDetection.created_at.asc(), DamageDetection.id.asc())
        ).all()
    )
