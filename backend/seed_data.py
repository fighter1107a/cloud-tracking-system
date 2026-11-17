"""
Seed script to populate initial sample shipments and checkpoints for demonstration.
"""
from datetime import datetime, timezone, timedelta
from backend.app.database import engine, Base, SessionLocal
from backend.app.models import Shipment, TrackingEvent
from backend.app.auth import seed_default_admin

def seed_sample_data():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        # 1. Seed admin
        seed_default_admin(db)
        
        # 2. Check if shipments already exist
        if db.query(Shipment).count() > 0:
            print("Database already contains shipments. Skipping sample seeding.")
            return

        now = datetime.now(timezone.utc)

        # Shipment 1: In Transit to Bangalore
        s1 = Shipment(
            tracking_id="TRK-2026-10001",
            product_name="Dell UltraSharp 27-inch 4K Monitor",
            recipient_name="Aditya Verma",
            recipient_phone="+91 9820123456",
            destination_city="Bangalore",
            destination_address="Flat 502, Prestige Palms, Whitefield",
            current_status="IN_TRANSIT",
            created_at=now - timedelta(days=2),
            updated_at=now - timedelta(hours=4)
        )
        db.add(s1)
        db.flush()

        e1_1 = TrackingEvent(
            shipment_id=s1.id,
            status="CREATED",
            checkpoint_location="Central Logistics Warehouse - Pune",
            remarks="Shipment electronic manifest created and label attached.",
            event_timestamp=now - timedelta(days=2)
        )
        e1_2 = TrackingEvent(
            shipment_id=s1.id,
            status="PACKED",
            checkpoint_location="Packaging Station 4B - Pune",
            remarks="Package boxed, bubble-wrapped, and weight verified (7.8 kg).",
            event_timestamp=now - timedelta(days=1, hours=18)
        )
        e1_3 = TrackingEvent(
            shipment_id=s1.id,
            status="DISPATCHED",
            checkpoint_location="Outbound Sorting Hub - Pune",
            remarks="Departed facility via linehaul freight truck LH-810.",
            event_timestamp=now - timedelta(days=1, hours=8)
        )
        e1_4 = TrackingEvent(
            shipment_id=s1.id,
            status="IN_TRANSIT",
            checkpoint_location="Regional Transit Hub - Belgaum",
            remarks="Scanned at intermediate transshipment terminal. On schedule.",
            event_timestamp=now - timedelta(hours=4)
        )
        db.add_all([e1_1, e1_2, e1_3, e1_4])

        # Shipment 2: Delivered in Mumbai
        s2 = Shipment(
            tracking_id="TRK-2026-10002",
            product_name="Apple iPad Air 11-inch (M2 Chip)",
            recipient_name="Sneha Kulkarni",
            recipient_phone="+91 9765432100",
            destination_city="Mumbai",
            destination_address="B-14, Sea Breeze Apartments, Bandra West",
            current_status="DELIVERED",
            created_at=now - timedelta(days=3),
            updated_at=now - timedelta(hours=6)
        )
        db.add(s2)
        db.flush()

        e2_1 = TrackingEvent(
            shipment_id=s2.id,
            status="CREATED",
            checkpoint_location="Central Fulfillment Hub - Pune",
            remarks="Order confirmed and package prepared for pickup.",
            event_timestamp=now - timedelta(days=3)
        )
        e2_2 = TrackingEvent(
            shipment_id=s2.id,
            status="PACKED",
            checkpoint_location="Fulfillment Center - Pune",
            remarks="Security tamper-seal verified.",
            event_timestamp=now - timedelta(days=2, hours=20)
        )
        e2_3 = TrackingEvent(
            shipment_id=s2.id,
            status="DISPATCHED",
            checkpoint_location="Express Logistics Terminal - Pune",
            remarks="Dispatched on morning transit express.",
            event_timestamp=now - timedelta(days=2, hours=10)
        )
        e2_4 = TrackingEvent(
            shipment_id=s2.id,
            status="IN_TRANSIT",
            checkpoint_location="Bandra Delivery Hub - Mumbai",
            remarks="Arrived at local distribution branch.",
            event_timestamp=now - timedelta(days=1, hours=5)
        )
        e2_5 = TrackingEvent(
            shipment_id=s2.id,
            status="OUT_FOR_DELIVERY",
            checkpoint_location="Bandra West Area",
            remarks="Out with delivery agent Rohan (Van #12).",
            event_timestamp=now - timedelta(hours=8)
        )
        e2_6 = TrackingEvent(
            shipment_id=s2.id,
            status="DELIVERED",
            checkpoint_location="Customer Residence - Bandra West",
            remarks="Delivered directly to recipient. OTP verified.",
            event_timestamp=now - timedelta(hours=6)
        )
        db.add_all([e2_1, e2_2, e2_3, e2_4, e2_5, e2_6])

        db.commit()
        print("Sample shipments (TRK-2026-10001, TRK-2026-10002) successfully seeded!")

    finally:
        db.close()

if __name__ == "__main__":
    seed_sample_data()
