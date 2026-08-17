from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_inspector_or_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.image import ImageResponse, ImageUploadResponse
from app.services.image_service import get_image_or_404, upload_inspection_images

router = APIRouter(prefix="/images", tags=["Images"])


@router.post(
    "/upload",
    response_model=ImageUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_images(
    inspection_id: int = Form(..., gt=0),
    image_views: list[str] = Form(...),
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_inspector_or_admin),
) -> dict[str, object]:
    images = await upload_inspection_images(
        db=db,
        inspection_id=inspection_id,
        files=files,
        image_views=image_views,
        current_user=current_user,
    )
    return {
        "success": True,
        "message": "Images uploaded successfully.",
        "data": {
            "items": images,
            "total": len(images),
        },
    }


@router.post(
    "/upload-one",
    response_model=ImageUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_one_image(
    inspection_id: int = Form(..., gt=0),
    image_view: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_inspector_or_admin),
) -> dict[str, object]:
    images = await upload_inspection_images(
        db=db,
        inspection_id=inspection_id,
        files=[file],
        image_views=[image_view],
        current_user=current_user,
    )
    return {
        "success": True,
        "message": "Image uploaded successfully.",
        "data": {
            "items": images,
            "total": len(images),
        },
    }


@router.get("/{image_id}", response_model=ImageResponse)
def read_image(
    image_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_inspector_or_admin),
) -> dict[str, object]:
    image = get_image_or_404(db, image_id, current_user)
    return {
        "success": True,
        "message": "Inspection image retrieved successfully.",
        "data": image,
    }
