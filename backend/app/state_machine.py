from typing import Set, Dict
from fastapi import HTTPException, status

# Ordered delivery lifecycle stages
STATUS_CREATED = "CREATED"
STATUS_PACKED = "PACKED"
STATUS_DISPATCHED = "DISPATCHED"
STATUS_IN_TRANSIT = "IN_TRANSIT"
STATUS_OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
STATUS_DELIVERED = "DELIVERED"
STATUS_CANCELLED = "CANCELLED"

VALID_STATUSES = {
    STATUS_CREATED,
    STATUS_PACKED,
    STATUS_DISPATCHED,
    STATUS_IN_TRANSIT,
    STATUS_OUT_FOR_DELIVERY,
    STATUS_DELIVERED,
    STATUS_CANCELLED
}

# Permitted state transitions to enforce strict business rules
ALLOWED_TRANSITIONS: Dict[str, Set[str]] = {
    STATUS_CREATED: {STATUS_PACKED, STATUS_CANCELLED},
    STATUS_PACKED: {STATUS_DISPATCHED, STATUS_CANCELLED},
    STATUS_DISPATCHED: {STATUS_IN_TRANSIT, STATUS_CANCELLED},
    STATUS_IN_TRANSIT: {STATUS_IN_TRANSIT, STATUS_OUT_FOR_DELIVERY, STATUS_CANCELLED},
    STATUS_OUT_FOR_DELIVERY: {STATUS_DELIVERED, STATUS_IN_TRANSIT, STATUS_CANCELLED},
    STATUS_DELIVERED: set(),  # Terminal state
    STATUS_CANCELLED: set()   # Terminal state
}

def validate_status_transition(current_status: str, new_status: str) -> None:
    """
    Validates whether the transition from current_status to new_status is allowed.
    Raises HTTPException(400) if transition is invalid.
    """
    if new_status not in VALID_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status '{new_status}'. Allowed statuses are: {sorted(list(VALID_STATUSES))}"
        )
    
    allowed_next = ALLOWED_TRANSITIONS.get(current_status, set())
    if new_status not in allowed_next:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Illegal status transition: Cannot move from '{current_status}' to '{new_status}'. Allowed transitions: {sorted(list(allowed_next)) if allowed_next else 'None (terminal state)'}"
        )
