from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.ai.constants import DAMAGE_TYPE_TO_CLASS_ID
from app.schemas.inspection import OVERALL_CONDITIONS

REVIEW_STATUSES = {"approved", "rejected", "edited"}


class DetectionReviewUpdate(BaseModel):
    review_status: str
    reviewed_damage_type: str | None = None
    reviewed_severity: str | None = None
    inspector_notes: str | None = Field(default=None, max_length=5000)

    @field_validator("review_status")
    @classmethod
    def validate_review_status(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in REVIEW_STATUSES:
            raise ValueError("review_status must be approved, rejected, or edited.")
        return normalized

    @field_validator("reviewed_damage_type")
    @classmethod
    def validate_reviewed_damage_type(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().lower()
        if normalized not in DAMAGE_TYPE_TO_CLASS_ID:
            raise ValueError(
                "reviewed_damage_type must be dent, scratch, broken_glass, or bumper_damage."
            )
        return normalized

    @field_validator("reviewed_severity")
    @classmethod
    def validate_reviewed_severity(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().lower()
        if normalized not in OVERALL_CONDITIONS:
            raise ValueError("reviewed_severity must be low, medium, or high.")
        return normalized

    @field_validator("inspector_notes")
    @classmethod
    def strip_notes(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    @model_validator(mode="after")
    def validate_review_fields(self) -> "DetectionReviewUpdate":
        has_edit = self.reviewed_damage_type is not None or self.reviewed_severity is not None
        if self.review_status == "edited" and not has_edit:
            raise ValueError(
                "edited reviews require reviewed_damage_type or reviewed_severity."
            )
        if self.review_status != "edited" and has_edit:
            raise ValueError(
                "reviewed_damage_type and reviewed_severity are only allowed for edited reviews."
            )
        return self


class DetectionReviewRead(BaseModel):
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


class DetectionReviewResponse(BaseModel):
    success: bool
    message: str
    data: DetectionReviewRead
