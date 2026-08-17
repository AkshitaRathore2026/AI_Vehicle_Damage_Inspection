from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ReportGenerateRequest(BaseModel):
    inspection_id: int = Field(gt=0)


class DamageCountItem(BaseModel):
    label: str
    count: int


class ReportSummary(BaseModel):
    total_detections: int
    approved_detections: int
    edited_detections: int
    rejected_detections: int
    pending_detections: int
    confirmed_detections: int
    damage_type_counts: list[DamageCountItem]
    severity_counts: list[DamageCountItem]


class ReportRead(BaseModel):
    id: int
    inspection_id: int
    report_number: str
    report_path: str
    generated_by: int | None
    generated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReportData(BaseModel):
    report: ReportRead
    summary: ReportSummary


class ReportResponse(BaseModel):
    success: bool
    message: str
    data: ReportData


class ReportListData(BaseModel):
    items: list[ReportRead]
    total: int
    page: int
    page_size: int


class ReportListResponse(BaseModel):
    success: bool
    message: str
    data: ReportListData
