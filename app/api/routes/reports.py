from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_inspector_or_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.report import ReportGenerateRequest, ReportListResponse, ReportResponse
from app.services.report_service import (
    generate_report,
    get_report_file_path,
    get_report_for_inspection,
    list_reports,
)

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("", response_model=ReportListResponse)
def read_reports(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_inspector_or_admin),
) -> dict[str, object]:
    reports, total = list_reports(db, current_user, page, page_size)
    return {
        "success": True,
        "message": "Reports retrieved successfully.",
        "data": {
            "items": reports,
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    }


@router.post("/generate", response_model=ReportResponse)
def generate_inspection_report(
    payload: ReportGenerateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_inspector_or_admin),
) -> dict[str, object]:
    ip_address = request.client.host if request.client else None
    report, summary = generate_report(
        db,
        payload.inspection_id,
        current_user,
        ip_address,
    )
    return {
        "success": True,
        "message": "Report generated successfully.",
        "data": {
            "report": report,
            "summary": summary,
        },
    }


@router.get("/{inspection_id}", response_model=ReportResponse)
def read_report_for_inspection(
    inspection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_inspector_or_admin),
) -> dict[str, object]:
    report, summary = get_report_for_inspection(db, inspection_id, current_user)
    return {
        "success": True,
        "message": "Report retrieved successfully.",
        "data": {
            "report": report,
            "summary": summary,
        },
    }


@router.get("/{inspection_id}/download", response_class=FileResponse)
def download_report_for_inspection(
    inspection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_inspector_or_admin),
) -> FileResponse:
    path = get_report_file_path(db, inspection_id, current_user)
    return FileResponse(
        path=path,
        media_type="application/pdf",
        filename=path.name,
    )
