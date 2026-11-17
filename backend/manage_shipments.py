"""
CLI utility for managing shipments directly from terminal without adding UI delete buttons.
Usage:
    python -m backend.manage_shipments list
    python -m backend.manage_shipments delete <tracking_id_or_id>
"""
import sys
from backend.app.database import SessionLocal
from backend.app.models import Shipment, TrackingEvent

def list_shipments():
    db = SessionLocal()
    try:
        shipments = db.query(Shipment).order_by(Shipment.created_at.desc()).all()
        if not shipments:
            print("No shipments found in database.")
            return

        print("\n" + "=" * 80)
        print(f"{'ID':<6} {'TRACKING ID':<18} {'STATUS':<18} {'PRODUCT':<25} {'DESTINATION'}")
        print("=" * 80)
        for s in shipments:
            print(f"{s.id:<6} {s.tracking_id:<18} {s.current_status:<18} {s.product_name[:24]:<25} {s.destination_city}")
        print("=" * 80 + "\n")
    finally:
        db.close()

def delete_shipment(identifier: str):
    db = SessionLocal()
    try:
        clean_id = identifier.strip().upper()
        query = db.query(Shipment)
        
        if identifier.isdigit():
            shipment = query.filter((Shipment.id == int(identifier)) | (Shipment.tracking_id == clean_id)).first()
        else:
            shipment = query.filter(Shipment.tracking_id == clean_id).first()

        if not shipment:
            print(f"❌ Error: Shipment '{identifier}' not found in database.")
            return False

        tracking_id = shipment.tracking_id
        db.delete(shipment)
        db.commit()
        print(f"✅ Success: Shipment '{tracking_id}' and all associated tracking checkpoints were deleted.")
        return True
    finally:
        db.close()

def print_help():
    print("""
Shipment Management CLI
-----------------------
Usage:
  python -m backend.manage_shipments list
      List all existing shipments in the database.

  python -m backend.manage_shipments delete <tracking_id_or_id>
      Delete a specific shipment (e.g. TRK-2026-10001 or ID 1).
""")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_help()
        sys.exit(0)

    action = sys.argv[1].lower()
    if action == "list":
        list_shipments()
    elif action == "delete":
        if len(sys.argv) < 3:
            print("❌ Please specify a tracking ID or numeric ID to delete.")
            print("Example: python -m backend.manage_shipments delete TRK-2026-10001")
            sys.exit(1)
        delete_shipment(sys.argv[2])
    else:
        print(f"Unknown command: '{action}'")
        print_help()
