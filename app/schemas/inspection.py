from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


INSPECTION_STATUSES = {"draft", "ai_processing", "under_review", "completed"}
OVERALL_CONDITIONS = {"low", "medium", "high"}


class InspectionCreate(BaseModel):
    vehicle_id: int = Field(gt=0)
    inspector_id: int | None = Field(default=None, gt=0)
    overall_condition: str | None = None
    inspector_notes: str | None = Field(default=None, max_length=5000)
    inspection_date: datetime | None = None

    @field_validator("overall_condition")
    @classmethod
    def validate_overall_condition(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().lower()
        if normalized not in OVERALL_CONDITIONS:
            raise ValueError("overall_condition must be low, medium, or high.")
        return normalized

    @field_validator("inspector_notes")
    @classmethod
    def strip_notes(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class InspectionUpdate(BaseModel):
    status: str | None = None
    overall_condition: str | None = None
    inspector_notes: str | None = Field(default=None, max_length=5000)
    inspection_date: datetime | None = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().lower()
        if normalized not in INSPECTION_STATUSES:
            raise ValueError(
                "status must be draft, ai_processing, under_review, or completed."
            )
        return normalized

    @field_validator("overall_condition")
    @classmethod
    def validate_overall_condition(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().lower()
        if normalized not in OVERALL_CONDITIONS:
            raise ValueError("overall_condition must be low, medium, or high.")
        return normalized

    @field_validator("inspector_notes")
    @classmethod
    def strip_notes(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class InspectionRead(BaseModel):
    id: int
    vehicle_id: int
    inspector_id: int
    status: str
    overall_condition: str | None
    inspector_notes: str | None
    inspection_date: datetime
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InspectionListData(BaseModel):
    items: list[InspectionRead]
    total: int
    page: int
    page_size: int


class InspectionResponse(BaseModel):
    success: bool
    message: str
    data: InspectionRead


class InspectionListResponse(BaseModel):
    success: bool
    message: str
    data: InspectionListData
