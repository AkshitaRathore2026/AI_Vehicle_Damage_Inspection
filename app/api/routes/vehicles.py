from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_inspector_or_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.vehicle import (
    VehicleCreate,
    VehicleDeleteResponse,
    VehicleHistoryResponse,
    VehicleListResponse,
    VehicleResponse,
    VehicleUpdate,
)
from app.services.vehicle_service import (
    create_vehicle,
    delete_vehicle,
    get_vehicle_history,
    get_vehicle_or_404,
    list_vehicles,
    update_vehicle,
)

router = APIRouter(prefix="/vehicles", tags=["Vehicles"])


@router.get("", response_model=VehicleListResponse)
def read_vehicles(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    search: str | None = Query(default=None, min_length=1, max_length=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_inspector_or_admin),
) -> dict[str, object]:
    vehicles, total = list_vehicles(db, current_user, page, page_size, search)
    return {
        "success": True,
        "message": "Vehicles retrieved successfully.",
        "data": {
            "items": vehicles,
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    }


@router.post(
    "",
    response_model=VehicleResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_vehicle_endpoint(
    payload: VehicleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_inspector_or_admin),
) -> dict[str, object]:
    vehicle = create_vehicle(db, payload, current_user)
    return {
        "success": True,
        "message": "Vehicle created successfully.",
        "data": vehicle,
    }


@router.get("/{vehicle_id}", response_model=VehicleResponse)
def read_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_inspector_or_admin),
) -> dict[str, object]:
    vehicle = get_vehicle_or_404(db, vehicle_id, current_user)
    return {
        "success": True,
        "message": "Vehicle retrieved successfully.",
        "data": vehicle,
    }


@router.put("/{vehicle_id}", response_model=VehicleResponse)
def update_vehicle_endpoint(
    vehicle_id: int,
    payload: VehicleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_inspector_or_admin),
) -> dict[str, object]:
    vehicle = update_vehicle(db, vehicle_id, payload, current_user)
    return {
        "success": True,
        "message": "Vehicle updated successfully.",
        "data": vehicle,
    }


@router.delete("/{vehicle_id}", response_model=VehicleDeleteResponse)
def delete_vehicle_endpoint(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_inspector_or_admin),
) -> dict[str, object]:
    delete_vehicle(db, vehicle_id, current_user)
    return {
        "success": True,
        "message": "Vehicle deleted successfully.",
        "data": {"id": vehicle_id},
    }


@router.get("/{vehicle_id}/history", response_model=VehicleHistoryResponse)
def read_vehicle_history(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_inspector_or_admin),
) -> dict[str, object]:
    vehicle, inspections = get_vehicle_history(db, vehicle_id, current_user)
    return {
        "success": True,
        "message": "Vehicle inspection history retrieved successfully.",
        "data": {
            "vehicle": vehicle,
            "inspections": inspections,
        },
    }
