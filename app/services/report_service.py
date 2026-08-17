from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from fastapi import HTTPException, status
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import and_, func, select, true
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.models.damage_detection import DamageDetection
from app.models.inspection import Inspection
from app.models.report import Report
from app.models.user import User
from app.schemas.report import ReportSummary
from app.services.audit_service import add_audit_log
from app.utils.file_utils import ensure_directory

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _report_error(
    status_code: int,
    message: str,
    error: str,
) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={
            "success": False,
            "message": message,
            "error": error,
        },
    )


def _inspection_scope(current_user: User):
    if current_user.role == "admin":
        return true()
    return Inspection.inspector_id == current_user.id


def _resolve_project_path(path_value: str) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def _report_output_path(report_number: str) -> Path:
    settings = get_settings()
    report_root = Path(settings.report_dir)
    if not report_root.is_absolute():
        report_root = PROJECT_ROOT / report_root
    ensure_directory(report_root)
    return report_root / f"{report_number}.pdf"


def _effective_damage_type(detection: DamageDetection) -> str | None:
    if detection.review_status == "rejected":
        return None
    if detection.review_status == "edited" and detection.reviewed_damage_type:
        return detection.reviewed_damage_type
    return detection.damage_type


def _effective_severity(detection: DamageDetection) -> str | None:
    if detection.review_status == "rejected":
        return None
    if detection.review_status == "edited" and detection.reviewed_severity:
        return detection.reviewed_severity
    return detection.severity


def build_report_summary(detections: list[DamageDetection]) -> ReportSummary:
    damage_counts: Counter[str] = Counter()
    severity_counts: Counter[str] = Counter()
    review_counts = Counter(detection.review_status for detection in detections)

    for detection in detections:
        damage_type = _effective_damage_type(detection)
        severity = _effective_severity(detection)
        if damage_type:
            damage_counts[damage_type] += 1
        if severity:
            severity_counts[severity] += 1

    return ReportSummary(
        total_detections=len(detections),
        approved_detections=review_counts["approved"],
        edited_detections=review_counts["edited"],
        rejected_detections=review_counts["rejected"],
        pending_detections=review_counts["pending"],
        confirmed_detections=sum(damage_counts.values()),
        damage_type_counts=[
            {"label": label, "count": count}
            for label, count in sorted(damage_counts.items())
        ],
        severity_counts=[
            {"label": label, "count": count}
            for label, count in sorted(severity_counts.items())
        ],
    )


def _get_inspection_for_reports_or_404(
    db: Session,
    inspection_id: int,
    current_user: User,
) -> Inspection:
    statement = (
        select(Inspection)
        .where(and_(Inspection.id == inspection_id, _inspection_scope(current_user)))
        .options(
            selectinload(Inspection.vehicle),
            selectinload(Inspection.inspector),
            selectinload(Inspection.damage_detections),
            selectinload(Inspection.images),
            selectinload(Inspection.report),
        )
    )
    inspection = db.scalar(statement)
    if inspection is None:
        raise _report_error(
            status.HTTP_404_NOT_FOUND,
            "Inspection not found.",
            "inspection_not_found",
        )
    return inspection


def _ensure_report_ready(inspection: Inspection) -> None:
    if inspection.status != "completed":
        raise _report_error(
            status.HTTP_409_CONFLICT,
            "Reports can only be generated for completed inspections.",
            "inspection_not_completed",
        )
    if not inspection.damage_detections:
        raise _report_error(
            status.HTTP_409_CONFLICT,
            "At least one reviewed detection is required before report generation.",
            "detections_required",
        )
    if any(detection.review_status == "pending" for detection in inspection.damage_detections):
        raise _report_error(
            status.HTTP_409_CONFLICT,
            "Reports cannot be generated while detections are pending review.",
            "pending_detection_reviews",
        )


def _build_pdf(
    path: Path,
    report_number: str,
    inspection: Inspection,
    summary: ReportSummary,
) -> None:
    ensure_directory(path.parent)
    styles = getSampleStyleSheet()
    document = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    story = [
        Paragraph("AI Vehicle Damage Inspection Report", styles["Title"]),
        Spacer(1, 14),
        Paragraph(f"Report Number: {report_number}", styles["Normal"]),
        Paragraph(f"Generated At: {datetime.now(UTC).isoformat()}", styles["Normal"]),
        Spacer(1, 14),
        Paragraph("Inspection", styles["Heading2"]),
    ]

    vehicle = inspection.vehicle
    inspection_rows = [
        ["Inspection ID", str(inspection.id)],
        ["Status", inspection.status],
        ["Inspection Date", inspection.inspection_date.isoformat()],
        ["Completed At", inspection.completed_at.isoformat() if inspection.completed_at else "-"],
        ["Inspector", inspection.inspector.full_name],
        ["Vehicle Number", vehicle.vehicle_number],
        ["Vehicle", f"{vehicle.year} {vehicle.make} {vehicle.model}"],
        ["Customer", vehicle.customer_name],
        ["VIN", vehicle.vin or "-"],
    ]
    story.append(_table(inspection_rows, [140, 340]))
    story.extend([Spacer(1, 14), Paragraph("Damage Summary", styles["Heading2"])])
    story.append(
        _table(
            [
                ["Total AI Detections", str(summary.total_detections)],
                ["Confirmed Detections", str(summary.confirmed_detections)],
                ["Approved", str(summary.approved_detections)],
                ["Edited", str(summary.edited_detections)],
                ["Rejected", str(summary.rejected_detections)],
            ],
            [180, 300],
        )
    )

    story.extend([Spacer(1, 14), Paragraph("Reviewed Detections", styles["Heading2"])])
    detection_rows = [
        [
            "ID",
            "AI Type",
            "Final Type",
            "AI Severity",
            "Final Severity",
            "Status",
            "Confidence",
        ]
    ]
    for detection in sorted(inspection.damage_detections, key=lambda item: item.id):
        detection_rows.append(
            [
                str(detection.id),
                detection.damage_type,
                _effective_damage_type(detection) or "-",
                detection.severity,
                _effective_severity(detection) or "-",
                detection.review_status,
                f"{float(detection.confidence):.2f}",
            ]
        )
    story.append(_table(detection_rows, [42, 72, 82, 76, 88, 70, 58], has_header=True))

    report_notes: list[str] = []
    if inspection.inspector_notes:
        report_notes.append(f"Inspection: {inspection.inspector_notes}")

    for detection in sorted(inspection.damage_detections, key=lambda item: item.id):
        detection_note = (detection.inspector_notes or "").strip()
        if detection_note:
            damage_label = _effective_damage_type(detection) or detection.damage_type
            report_notes.append(
                f"Detection {detection.id} ({damage_label}): {detection_note}"
            )

    if report_notes:
        story.extend([Spacer(1, 14), Paragraph("Inspector Notes", styles["Heading2"])])
        for note in report_notes:
            story.append(Paragraph(note, styles["Normal"]))
            story.append(Spacer(1, 8))

    document.build(story)


def _table(rows: list[list[object]], column_widths: list[int], has_header: bool = False) -> Table:
    table = Table(rows, colWidths=column_widths)
    style = [
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    if has_header:
        style.extend(
            [
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ]
        )
    table.setStyle(TableStyle(style))
    return table


def generate_report(
    db: Session,
    inspection_id: int,
    current_user: User,
    ip_address: str | None = None,
) -> tuple[Report, ReportSummary]:
    inspection = _get_inspection_for_reports_or_404(db, inspection_id, current_user)
    _ensure_report_ready(inspection)
    summary = build_report_summary(list(inspection.damage_detections))

    if inspection.report is not None:
        report_path = _resolve_project_path(inspection.report.report_path)
        if not report_path.exists():
            _build_pdf(report_path, inspection.report.report_number, inspection, summary)
        return inspection.report, summary

    report_number = f"VDR-{inspection.id}-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"
    report_path = _report_output_path(report_number)
    _build_pdf(report_path, report_number, inspection, summary)

    report = Report(
        inspection_id=inspection.id,
        report_number=report_number,
        report_path=str(report_path.relative_to(PROJECT_ROOT).as_posix()),
        generated_by=current_user.id,
    )
    db.add(report)
    add_audit_log(
        db=db,
        current_user=current_user,
        action="report_generated",
        entity_type="inspection",
        entity_id=inspection.id,
        description=f"Generated report {report_number}.",
        ip_address=ip_address,
    )

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        report_path.unlink(missing_ok=True)
        raise _report_error(
            status.HTTP_409_CONFLICT,
            "A report already exists for this inspection.",
            "report_already_exists",
        ) from exc
    except SQLAlchemyError:
        db.rollback()
        report_path.unlink(missing_ok=True)
        raise

    db.refresh(report)
    return report, summary


def get_report_for_inspection(
    db: Session,
    inspection_id: int,
    current_user: User,
) -> tuple[Report, ReportSummary]:
    inspection = _get_inspection_for_reports_or_404(db, inspection_id, current_user)
    if inspection.report is None:
        raise _report_error(
            status.HTTP_404_NOT_FOUND,
            "Report not found for this inspection.",
            "report_not_found",
        )
    summary = build_report_summary(list(inspection.damage_detections))
    return inspection.report, summary


def get_report_file_path(
    db: Session,
    inspection_id: int,
    current_user: User,
) -> Path:
    report, _summary = get_report_for_inspection(db, inspection_id, current_user)
    path = _resolve_project_path(report.report_path)
    if not path.exists():
        raise _report_error(
            status.HTTP_404_NOT_FOUND,
            "Report file is missing from disk.",
            "report_file_missing",
        )
    return path


def list_reports(
    db: Session,
    current_user: User,
    page: int,
    page_size: int,
) -> tuple[list[Report], int]:
    where_clause = _inspection_scope(current_user)
    total = (
        db.scalar(
            select(func.count())
            .select_from(Report)
            .join(Inspection, Report.inspection_id == Inspection.id)
            .where(where_clause)
        )
        or 0
    )
    offset = (page - 1) * page_size
    statement = (
        select(Report)
        .join(Inspection, Report.inspection_id == Inspection.id)
        .where(where_clause)
        .order_by(Report.generated_at.desc(), Report.id.desc())
        .offset(offset)
        .limit(page_size)
    )
    return list(db.scalars(statement).all()), total
