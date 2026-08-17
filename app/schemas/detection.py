from datetime import datetime

from pydantic import BaseModel, ConfigDict
from pydantic import Field


class AIAnalyzeRequest(BaseModel):
    inspection_id: int = Field(gt=0)


class DamageDetectionRead(BaseModel):
    id: int
    inspection_id: int
    image_id: int
    damage_type: str
    confidence: float
    bbox_x1: float
    bbox_y1: float
    bbox_x2: float
    bbox_y2: float
    severity: str
    review_status: str
    reviewed_damage_type: str | None
    reviewed_severity: str | None
    inspector_notes: str | None
    detected_by_model: str
    model_version: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AIAnalysisData(BaseModel):
    inspection_id: int
    processed_images: int
    detections_created: int
    detections: list[DamageDetectionRead]


class AIAnalysisResponse(BaseModel):
    success: bool
    message: str
    data: AIAnalysisData


class DetectionListData(BaseModel):
    inspection_id: int
    items: list[DamageDetectionRead]
    total: int


class DetectionListResponse(BaseModel):
    success: bool
    message: str
    data: DetectionListData
