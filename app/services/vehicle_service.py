from fastapi import HTTPException, status
from sqlalchemy import and_, func, or_, select, true
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models.inspection import Inspection
from app.models.user import User
from app.models.vehicle import Vehicle
from app.schemas.vehicle import VehicleCreate, VehicleUpdate


def _vehicle_not_found() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={
            "success": False,
            "message": "Vehicle not found.",
            "error": "vehicle_not_found",
        },
    )


def _duplicate_vehicle(field: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail={
            "success": False,
            "message": f"A vehicle with this {field} already exists.",
            "error": f"duplicate_{field}",
        },
    )


def _base_vehicle_scope(current_user: User):
    if current_user.role == "admin":
        return true()
    return Vehicle.created_by == current_user.id


def get_vehicle_or_404(db: Session, vehicle_id: int, current_user: User) -> Vehicle:
    statement = select(Vehicle).where(
        and_(Vehicle.id == vehicle_id, _base_vehicle_scope(current_user))
    )
    vehicle = db.scalar(statement)
    if vehicle is None:
        raise _vehicle_not_found()
    return vehicle


def _ensure_unique_vehicle_number(
    db: Session,
    vehicle_number: str,
    exclude_vehicle_id: int | None = None,
) -> None:
    statement = select(Vehicle.id).where(
        func.lower(Vehicle.vehicle_number) == vehicle_number.lower()
    )
    if exclude_vehicle_id is not None:
        statement = statement.where(Vehicle.id != exclude_vehicle_id)
    if db.scalar(statement) is not None:
        raise _duplicate_vehicle("vehicle_number")


def _ensure_unique_vin(
    db: Session,
    vin: str | None,
    exclude_vehicle_id: int | None = None,
) -> None:
    if vin is None:
        return
    statement = select(Vehicle.id).where(func.lower(Vehicle.vin) == vin.lower())
    if exclude_vehicle_id is not None:
        statement = statement.where(Vehicle.id != exclude_vehicle_id)
    if db.scalar(statement) is not None:
        raise _duplicate_vehicle("vin")


def create_vehicle(db: Session, payload: VehicleCreate, current_user: User) -> Vehicle:
    _ensure_unique_vehicle_number(db, payload.vehicle_number)
    _ensure_unique_vin(db, payload.vin)

    vehicle = Vehicle(
        vehicle_number=payload.vehicle_number,
        make=payload.make,
        model=payload.model,
        year=payload.year,
        customer_name=payload.customer_name,
        vin=payload.vin,
        created_by=current_user.id,
    )
    db.add(vehicle)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise _duplicate_vehicle("vehicle_number_or_vin") from exc

    db.refresh(vehicle)
    return vehicle


def list_vehicles(
    db: Session,
    current_user: User,
    page: int,
    page_size: int,
    search: str | None = None,
) -> tuple[list[Vehicle], int]:
    filters = [_base_vehicle_scope(current_user)]
    if search:
        pattern = f"%{search.strip().lower()}%"
        filters.append(
            or_(
                func.lower(Vehicle.vehicle_number).like(pattern),
                func.lower(Vehicle.make).like(pattern),
                func.lower(Vehicle.model).like(pattern),
                func.lower(Vehicle.customer_name).like(pattern),
                func.lower(Vehicle.vin).like(pattern),
            )
        )

    where_clause = and_(*filters)
    total = db.scalar(select(func.count()).select_from(Vehicle).where(where_clause)) or 0
    offset = (page - 1) * page_size
    statement = (
        select(Vehicle)
        .where(where_clause)
        .order_by(Vehicle.created_at.desc(), Vehicle.id.desc())
        .offset(offset)
        .limit(page_size)
    )
    return list(db.scalars(statement).all()), total


def update_vehicle(
    db: Session,
    vehicle_id: int,
    payload: VehicleUpdate,
    current_user: User,
) -> Vehicle:
    vehicle = get_vehicle_or_404(db, vehicle_id, current_user)
    update_data = payload.model_dump(exclude_unset=True)

    if "vehicle_number" in update_data:
        _ensure_unique_vehicle_number(
            db,
            update_data["vehicle_number"],
            exclude_vehicle_id=vehicle.id,
        )
    if "vin" in update_data:
        _ensure_unique_vin(db, update_data["vin"], exclude_vehicle_id=vehicle.id)

    for field, value in update_data.items():
        setattr(vehicle, field, value)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise _duplicate_vehicle("vehicle_number_or_vin") from exc

    db.refresh(vehicle)
    return vehicle


def delete_vehicle(db: Session, vehicle_id: int, current_user: User) -> None:
    vehicle = get_vehicle_or_404(db, vehicle_id, current_user)
    inspection_exists = db.scalar(
        select(Inspection.id).where(Inspection.vehicle_id == vehicle.id).limit(1)
    )
    if inspection_exists is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "success": False,
                "message": "Vehicle cannot be deleted because inspection history exists.",
                "error": "vehicle_has_inspections",
            },
        )

    db.delete(vehicle)
    db.commit()


def get_vehicle_history(
    db: Session,
    vehicle_id: int,
    current_user: User,
) -> tuple[Vehicle, list[Inspection]]:
    vehicle = get_vehicle_or_404(db, vehicle_id, current_user)
    statement = (
        select(Inspection)
        .where(Inspection.vehicle_id == vehicle.id)
        .options(selectinload(Inspection.inspector))
        .order_by(Inspection.inspection_date.desc(), Inspection.id.desc())
    )
    return vehicle, list(db.scalars(statement).all())
