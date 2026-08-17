from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


VIN_PATTERN = r"^[A-HJ-NPR-Z0-9]{17}$"


class VehicleBase(BaseModel):
    vehicle_number: str = Field(min_length=1, max_length=50)
    make: str = Field(min_length=1, max_length=100)
    model: str = Field(min_length=1, max_length=100)
    year: int = Field(ge=1886, le=2100)
    customer_name: str = Field(min_length=2, max_length=150)
    vin: str | None = Field(default=None, pattern=VIN_PATTERN)

    @field_validator("vehicle_number", "make", "model", "customer_name")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Field cannot be blank.")
        return stripped

    @field_validator("vin", mode="before")
    @classmethod
    def normalize_vin(cls, value: Any) -> str | None:
        if value is None:
            return None
        stripped = str(value).strip().upper()
        return stripped or None


class VehicleCreate(VehicleBase):
    pass


class VehicleUpdate(BaseModel):
    vehicle_number: str | None = Field(default=None, min_length=1, max_length=50)
    make: str | None = Field(default=None, min_length=1, max_length=100)
    model: str | None = Field(default=None, min_length=1, max_length=100)
    year: int | None = Field(default=None, ge=1886, le=2100)
    customer_name: str | None = Field(default=None, min_length=2, max_length=150)
    vin: str | None = Field(default=None, pattern=VIN_PATTERN)

    @field_validator("vehicle_number", "make", "model", "customer_name")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("Field cannot be blank.")
        return stripped

    @field_validator("vin", mode="before")
    @classmethod
    def normalize_vin(cls, value: Any) -> str | None:
        if value is None:
            return None
        stripped = str(value).strip().upper()
        return stripped or None


class VehicleRead(BaseModel):
    id: int
    vehicle_number: str
    make: str
    model: str
    year: int
    customer_name: str
    vin: str | None
    created_by: int | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VehicleListData(BaseModel):
    items: list[VehicleRead]
    total: int
    page: int
    page_size: int


class VehicleResponse(BaseModel):
    success: bool
    message: str
    data: VehicleRead


class VehicleListResponse(BaseModel):
    success: bool
    message: str
    data: VehicleListData


class VehicleHistoryItem(BaseModel):
    id: int
    status: str
    overall_condition: str | None
    inspector_notes: str | None
    inspection_date: datetime
    completed_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VehicleHistoryData(BaseModel):
    vehicle: VehicleRead
    inspections: list[VehicleHistoryItem]


class VehicleHistoryResponse(BaseModel):
    success: bool
    message: str
    data: VehicleHistoryData


class VehicleDeleteResponse(BaseModel):
    success: bool
    message: str
    data: dict[str, int]
