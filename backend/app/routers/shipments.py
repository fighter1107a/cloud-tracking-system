from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.auth import get_current_admin
from backend.app.database import get_db
from backend.app.models import AdminUser, Shipment, TrackingEvent
from backend.app.schemas import (
    ShipmentCreate,
    ShipmentAdminResponse,
    TrackingEventCreate
)
from backend.app.state_machine import validate_status_transition, STATUS_CREATED

router = APIRouter(prefix="/api/shipments", tags=["Admin Shipments"])

def generate_tracking_id(db: Session) -> str:
    """Generates a standardized unique tracking ID, e.g. TRK-2026-10001"""
    year = datetime.now(timezone.utc).year
    total = db.query(Shipment).count()
    candidate_num = 10001 + total
    candidate = f"TRK-{year}-{candidate_num}"
    
    # Guarantee uniqueness in case of deletions
    while db.query(Shipment).filter(Shipment.tracking_id == candidate).first():
        candidate_num += 1
        candidate = f"TRK-{year}-{candidate_num}"
    return candidate

@router.post("", response_model=ShipmentAdminResponse, status_code=status.HTTP_201_CREATED)
def create_shipment(
    shipment_in: ShipmentCreate,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """
    Administrator endpoint: Creates a new shipment record, generates a unique tracking ID,
    and records the initial CREATED tracking event in a single atomic database transaction.
    """
    tracking_id = generate_tracking_id(db)
    
    shipment = Shipment(
        tracking_id=tracking_id,
        product_name=shipment_in.product_name,
        recipient_name=shipment_in.recipient_name,
        recipient_phone=shipment_in.recipient_phone,
        destination_address=shipment_in.destination_address,
        destination_city=shipment_in.destination_city,
        current_status=STATUS_CREATED
    )
    db.add(shipment)
    db.flush()  # Flush to acquire shipment.id for the foreign key
    
    # Record initial lifecycle checkpoint event
    initial_event = TrackingEvent(
        shipment_id=shipment.id,
        status=STATUS_CREATED,
        checkpoint_location=shipment_in.initial_location or "Origin Logistics Facility",
        remarks="Shipment record created in system; dispatch pending."
    )
    db.add(initial_event)
    
    db.commit()
    db.refresh(shipment)
    return shipment

@router.get("", response_model=List[ShipmentAdminResponse])
def list_shipments(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    search: Optional[str] = Query(None, description="Search by tracking ID, recipient, or product"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """
    Administrator endpoint: Lists shipments with optional status filtering and pagination.
    """
    query = db.query(Shipment)
    if status_filter:
        query = query.filter(Shipment.current_status == status_filter.upper())
    if search:
        pattern = f"%{search}%"
        query = query.filter(
            (Shipment.tracking_id.ilike(pattern)) |
            (Shipment.recipient_name.ilike(pattern)) |
            (Shipment.product_name.ilike(pattern))
        )
    
    shipments = query.order_by(Shipment.created_at.desc()).offset(skip).limit(limit).all()
    return shipments

@router.get("/{id}", response_model=ShipmentAdminResponse)
def get_shipment_by_id(
    id: int,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """
    Administrator endpoint: Retrieves complete shipment information including recipient details.
    """
    shipment = db.query(Shipment).filter(Shipment.id == id).first()
    if not shipment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipment not found")
    return shipment

@router.post("/{id}/events", response_model=ShipmentAdminResponse)
def add_tracking_event(
    id: int,
    event_in: TrackingEventCreate,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """
    Administrator endpoint: Appends a new checkpoint event and updates the shipment status.
    Enforces state-machine transition guardrails within an atomic database transaction.
    """
    shipment = db.query(Shipment).filter(Shipment.id == id).first()
    if not shipment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipment not found")
        
    target_status = event_in.status.upper().strip()
    
    # Validate lifecycle transition rules
    validate_status_transition(shipment.current_status, target_status)
    
    # Record the checkpoint event
    event = TrackingEvent(
        shipment_id=shipment.id,
        status=target_status,
        checkpoint_location=event_in.checkpoint_location.strip(),
        remarks=event_in.remarks
    )
    db.add(event)
    
    # Update current shipment status and timestamp
    shipment.current_status = target_status
    shipment.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(shipment)
    return shipment

@router.delete("/{identifier}", status_code=status.HTTP_200_OK)
def delete_shipment(
    identifier: str,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """
    Administrator endpoint: Deletes a shipment and its associated tracking events.
    Accepts either database numeric ID (e.g. 1) or tracking ID (e.g. TRK-2026-10001).
    """
    query = db.query(Shipment)
    clean_id = identifier.strip().upper()
    
    if identifier.isdigit():
        shipment = query.filter((Shipment.id == int(identifier)) | (Shipment.tracking_id == clean_id)).first()
    else:
        shipment = query.filter(Shipment.tracking_id == clean_id).first()
        
    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shipment with identifier '{identifier}' not found."
        )
        
    deleted_tracking_id = shipment.tracking_id
    db.delete(shipment)
    db.commit()
    
    return {
        "status": "success",
        "message": f"Shipment '{deleted_tracking_id}' and its tracking history were permanently deleted.",
        "tracking_id": deleted_tracking_id
    }

