import re
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

# ==========================================
# REGEX PATTERNS FOR VALIDATION
# ==========================================
PHONE_REGEX = re.compile(r"^\+?[0-9\s\-()]{10,20}$")
NAME_REGEX = re.compile(r"^[A-Za-z\s\.\-']+$")
CITY_REGEX = re.compile(r"^[A-Za-z\s\.\-]+$")
TRACKING_ID_REGEX = re.compile(r"^TRK-\d{4}-\d{5}$")

# ==========================================
# AUTH SCHEMAS
# ==========================================
class AdminLoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=4, max_length=100)

    @field_validator("username")
    @classmethod
    def strip_username(cls, v: str) -> str:
        return v.strip()

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: Optional[str] = "ADMIN"

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None

class AdminUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    username: str
    role: str = "ADMIN"
    is_active: bool
    created_at: datetime

# ==========================================
# TRACKING EVENT SCHEMAS
# ==========================================
class TrackingEventCreate(BaseModel):
    status: str = Field(..., description="Target status for the shipment", min_length=3, max_length=50)
    checkpoint_location: str = Field(..., description="City or facility name", min_length=3, max_length=200)
    remarks: Optional[str] = Field(None, description="Optional operational notes", max_length=500)

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        cleaned = v.strip().upper()
        if not cleaned:
            raise ValueError("Status cannot be empty.")
        return cleaned

    @field_validator("checkpoint_location")
    @classmethod
    def validate_location(cls, v: str) -> str:
        cleaned = v.strip()
        if len(cleaned) < 3:
            raise ValueError("Checkpoint location must be at least 3 characters long.")
        return cleaned

    @field_validator("remarks")
    @classmethod
    def validate_remarks(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            cleaned = v.strip()
            return cleaned if cleaned else None
        return None

class TrackingEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    shipment_id: int
    status: str
    checkpoint_location: str
    remarks: Optional[str] = None
    event_timestamp: datetime

# Customer-Facing Event Schema (Clean, sanitized)
class CustomerEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    status: str
    checkpoint_location: str
    remarks: Optional[str] = None
    event_timestamp: datetime

# ==========================================
# SHIPMENT SCHEMAS
# ==========================================
class ShipmentCreate(BaseModel):
    product_name: str = Field(..., min_length=3, max_length=200, description="Product description")
    recipient_name: str = Field(..., min_length=2, max_length=100, description="Recipient full name")
    recipient_phone: str = Field(..., description="Contact phone number (10-15 digits)")
    destination_address: str = Field(..., min_length=10, max_length=500, description="Full delivery address")
    destination_city: str = Field(..., min_length=2, max_length=100, description="Destination city name")
    initial_location: Optional[str] = Field("Central Fulfillment Warehouse", min_length=3, max_length=200)

    @field_validator("product_name")
    @classmethod
    def validate_product(cls, v: str) -> str:
        cleaned = v.strip()
        if len(cleaned) < 3:
            raise ValueError("Product name must be at least 3 characters.")
        return cleaned

    @field_validator("recipient_name")
    @classmethod
    def validate_recipient_name(cls, v: str) -> str:
        cleaned = v.strip()
        if len(cleaned) < 2:
            raise ValueError("Recipient name must be at least 2 characters.")
        if not NAME_REGEX.match(cleaned):
            raise ValueError("Recipient name can only contain letters, spaces, hyphens, and periods.")
        return cleaned

    @field_validator("recipient_phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        cleaned = v.strip()
        if not PHONE_REGEX.match(cleaned):
            raise ValueError("Invalid phone format. Examples: +91 9876543210, (555) 123-4567, or 9876543210.")
        # Check digit count
        digits = re.sub(r"\D", "", cleaned)
        if len(digits) < 10 or len(digits) > 15:
            raise ValueError(f"Phone number must contain between 10 and 15 digits (found {len(digits)} digits).")
        return cleaned

    @field_validator("destination_city")
    @classmethod
    def validate_city(cls, v: str) -> str:
        cleaned = v.strip()
        if len(cleaned) < 2:
            raise ValueError("City name must be at least 2 characters.")
        if not CITY_REGEX.match(cleaned):
            raise ValueError("City name must contain only letters, spaces, and hyphens.")
        return cleaned

    @field_validator("destination_address")
    @classmethod
    def validate_address(cls, v: str) -> str:
        cleaned = v.strip()
        if len(cleaned) < 10:
            raise ValueError("Destination address must be at least 10 characters long with sufficient detail.")
        return cleaned

    @field_validator("initial_location")
    @classmethod
    def validate_initial_hub(cls, v: Optional[str]) -> str:
        if v:
            cleaned = v.strip()
            if len(cleaned) < 3:
                return "Central Fulfillment Warehouse"
            return cleaned
        return "Central Fulfillment Warehouse"

# Full Administrator Shipment Response (Includes private recipient PII)
class ShipmentAdminResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    tracking_id: str
    product_name: str
    recipient_name: str
    recipient_phone: str
    destination_address: str
    destination_city: str
    current_status: str
    created_at: datetime
    updated_at: datetime
    events: List[TrackingEventResponse] = []

# Customer-Facing Response (Zero PII leak: strictly public tracking data)
class CustomerTrackingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    tracking_id: str
    product_name: str
    destination_city: str
    current_status: str
    created_at: datetime
    updated_at: datetime
    events: List[CustomerEventResponse] = []
