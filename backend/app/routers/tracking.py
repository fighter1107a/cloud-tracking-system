import re
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import Shipment
from backend.app.schemas import CustomerTrackingResponse

router = APIRouter(prefix="/api/track", tags=["Customer Tracking"])

TRACKING_ID_PATTERN = re.compile(r"^TRK-\d{4}-\d{5}$")

@router.get("/{tracking_id}", response_model=CustomerTrackingResponse)
def track_shipment(
    tracking_id: str,
    db: Session = Depends(get_db)
):
    """
    Public Customer Tracking Endpoint:
    Allows customers to view delivery checkpoints, current stage, and update history.
    
    Validation & Security:
    1. Validates tracking ID structure (TRK-YYYY-NNNNN).
    2. Exposes ONLY public tracking telemetry (zero PII: recipient phone, address, and name are protected).
    """
    cleaned_id = tracking_id.strip().upper()
    
    # 1. Format Validation Guardrail
    if not TRACKING_ID_PATTERN.match(cleaned_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid tracking ID format '{cleaned_id}'. Expected standard format: TRK-YYYY-NNNNN (e.g. TRK-2026-10001)."
        )
    
    # 2. Database Lookup
    shipment = db.query(Shipment).filter(Shipment.tracking_id == cleaned_id).first()
    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tracking ID '{cleaned_id}' not found. Please verify the code on your delivery receipt."
        )
        
    return shipment
