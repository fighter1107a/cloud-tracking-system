from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.app.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class AdminUser(Base):
    __tablename__ = "admin_users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

class Shipment(Base):
    __tablename__ = "shipments"
    
    id = Column(Integer, primary_key=True, index=True)
    tracking_id = Column(String(64), unique=True, index=True, nullable=False)
    product_name = Column(String(255), nullable=False)
    
    # Private recipient details (Protected - accessible ONLY to authorized Admin)
    recipient_name = Column(String(255), nullable=False)
    recipient_phone = Column(String(50), nullable=False)
    destination_address = Column(Text, nullable=False)
    destination_city = Column(String(100), nullable=False)
    
    # Current status
    current_status = Column(String(50), default="CREATED", nullable=False)
    
    # Audit timestamps
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    
    # Relationship to immutable checkpoint tracking events
    events = relationship(
        "TrackingEvent",
        back_populates="shipment",
        cascade="all, delete-orphan",
        order_by="TrackingEvent.event_timestamp.desc()"
    )

class TrackingEvent(Base):
    __tablename__ = "tracking_events"
    
    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id", ondelete="CASCADE"), index=True, nullable=False)
    status = Column(String(50), nullable=False)
    checkpoint_location = Column(String(255), nullable=False)
    remarks = Column(Text, nullable=True)
    event_timestamp = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    
    shipment = relationship("Shipment", back_populates="events")
