from datetime import datetime

from pydantic import BaseModel, ConfigDict


IMAGE_VIEWS = {"front", "rear", "left", "right", "closeup_damage"}


class InspectionImageRead(BaseModel):
    id: int
    inspection_id: int
    image_view: str
    original_filename: str
    stored_filename: str
    original_path: str
    processed_path: str | None
    file_type: str
    file_size: int
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ImageUploadData(BaseModel):
    items: list[InspectionImageRead]
    total: int


class ImageUploadResponse(BaseModel):
    success: bool
    message: str
    data: ImageUploadData


class ImageResponse(BaseModel):
    success: bool
    message: str
    data: InspectionImageRead
