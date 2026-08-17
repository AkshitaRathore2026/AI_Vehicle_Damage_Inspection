from io import BytesIO
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError
from sqlalchemy import and_, select, true
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.inspection import Inspection
from app.models.inspection_image import InspectionImage
from app.models.user import User
from app.schemas.image import IMAGE_VIEWS
from app.services.inspection_service import get_inspection_or_404
from app.utils.file_utils import (
    build_unique_image_filename,
    ensure_directory,
    safe_original_filename,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _invalid_image(message: str, error: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail={
            "success": False,
            "message": message,
            "error": error,
        },
    )


def _image_not_found() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={
            "success": False,
            "message": "Inspection image not found.",
            "error": "image_not_found",
        },
    )


def _image_scope(current_user: User):
    if current_user.role == "admin":
        return true()
    return Inspection.inspector_id == current_user.id


def _validate_image_view(image_view: str) -> str:
    normalized = image_view.strip().lower()
    if normalized not in IMAGE_VIEWS:
        raise _invalid_image(
            "Invalid image view.",
            "invalid_image_view",
        )
    return normalized


def _validate_file_extension(filename: str) -> None:
    extension = Path(filename).suffix.lower()
    if extension not in {".jpg", ".jpeg", ".png"}:
        raise _invalid_image(
            "Only JPG, JPEG, and PNG files are supported.",
            "unsupported_image_extension",
        )


def _validate_content_type(file: UploadFile) -> str:
    settings = get_settings()
    content_type = file.content_type or ""
    if content_type not in settings.allowed_image_type_list:
        raise _invalid_image(
            "Only image/jpeg and image/png uploads are supported.",
            "unsupported_image_type",
        )
    return content_type


def _validate_file_size(content: bytes) -> int:
    settings = get_settings()
    file_size = len(content)
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if file_size == 0:
        raise _invalid_image("Uploaded file is empty.", "empty_upload")
    if file_size > max_bytes:
        raise _invalid_image(
            f"Uploaded file exceeds {settings.max_upload_size_mb} MB.",
            "file_too_large",
        )
    return file_size


def _validate_image_content(content: bytes, content_type: str) -> None:
    try:
        with Image.open(BytesIO(content)) as image:
            image.verify()
            detected_format = image.format
    except (UnidentifiedImageError, OSError) as exc:
        raise _invalid_image(
            "Uploaded file is not a valid image.",
            "corrupted_image",
        ) from exc

    expected_formats = {
        "image/jpeg": {"JPEG"},
        "image/png": {"PNG"},
    }
    if detected_format not in expected_formats[content_type]:
        raise _invalid_image(
            "Uploaded image content does not match its MIME type.",
            "image_type_mismatch",
        )


async def upload_inspection_images(
    db: Session,
    inspection_id: int,
    files: list[UploadFile],
    image_views: list[str],
    current_user: User,
) -> list[InspectionImage]:
    if not files:
        raise _invalid_image("At least one image file is required.", "missing_files")
    if len(image_views) == 1 and len(files) > 1:
        image_views = image_views * len(files)
    if len(files) != len(image_views):
        raise _invalid_image(
            "The number of image views must match the number of uploaded files.",
            "image_view_count_mismatch",
        )

    inspection = get_inspection_or_404(db, inspection_id, current_user)
    if inspection.status != "draft":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "success": False,
                "message": "Images can only be uploaded while the inspection is in draft status.",
                "error": "invalid_inspection_state",
            },
        )

    settings = get_settings()
    upload_root = Path(settings.upload_dir)
    if not upload_root.is_absolute():
        upload_root = PROJECT_ROOT / upload_root
    inspection_upload_dir = upload_root / str(inspection.id)
    ensure_directory(inspection_upload_dir)

    saved_paths: list[Path] = []
    image_records: list[InspectionImage] = []

    try:
        for file, raw_image_view in zip(files, image_views, strict=True):
            original_filename = safe_original_filename(file.filename)
            _validate_file_extension(original_filename)
            image_view = _validate_image_view(raw_image_view)
            content_type = _validate_content_type(file)
            content = await file.read()
            file_size = _validate_file_size(content)
            _validate_image_content(content, content_type)

            stored_filename = build_unique_image_filename(content_type)
            storage_path = inspection_upload_dir / stored_filename
            storage_path.write_bytes(content)
            saved_paths.append(storage_path)

            image_records.append(
                InspectionImage(
                    inspection_id=inspection.id,
                    image_view=image_view,
                    original_filename=original_filename,
                    stored_filename=stored_filename,
                    original_path=str(storage_path.relative_to(PROJECT_ROOT).as_posix()),
                    processed_path=None,
                    file_type=content_type,
                    file_size=file_size,
                )
            )

        db.add_all(image_records)
        db.commit()
    except HTTPException:
        for path in saved_paths:
            path.unlink(missing_ok=True)
        raise
    except SQLAlchemyError:
        db.rollback()
        for path in saved_paths:
            path.unlink(missing_ok=True)
        raise

    for record in image_records:
        db.refresh(record)
    return image_records


def get_image_or_404(
    db: Session,
    image_id: int,
    current_user: User,
) -> InspectionImage:
    statement = (
        select(InspectionImage)
        .join(Inspection, Inspection.id == InspectionImage.inspection_id)
        .where(and_(InspectionImage.id == image_id, _image_scope(current_user)))
    )
    image = db.scalar(statement)
    if image is None:
        raise _image_not_found()
    return image
