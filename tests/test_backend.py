import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.main import app
from backend.app.database import Base, get_db
from backend.app.auth import seed_default_admin

# Use isolated SQLite test database
TEST_DATABASE_URL = "sqlite:///./test_tracking.db"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    seed_default_admin(db)
    db.close()
    yield
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def admin_token(client):
    response = client.post("/api/auth/login-json", json={
        "username": "admin",
        "password": "Admin@2026"
    })
    assert response.status_code == 200
    return response.json()["access_token"]

def test_health_check(client):
    """Test backend compute availability probe and database connectivity."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "UP"
    assert data["database"] == "healthy"
    assert "uptime_seconds" in data

def test_admin_authentication_failure(client):
    """Test that unauthorized users are rejected."""
    response = client.post("/api/auth/login-json", json={
        "username": "admin",
        "password": "WrongPassword123"
    })
    assert response.status_code == 401

def test_create_shipment_and_tracking_id_generation(client, admin_token):
    """Test shipment creation, atomic event generation, and tracking ID format."""
    payload = {
        "product_name": "Course Project Prototype Sensors",
        "recipient_name": "Test Customer",
        "recipient_phone": "+91 9999888877",
        "destination_address": "Block B, Room 304, Campus Hostel",
        "destination_city": "Pune",
        "initial_location": "University Logistics Center"
    }
    response = client.post(
        "/api/shipments",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=payload
    )
    assert response.status_code == 201
    data = response.json()
    assert data["tracking_id"].startswith("TRK-")
    assert data["current_status"] == "CREATED"
    assert data["product_name"] == payload["product_name"]
    assert len(data["events"]) == 1
    assert data["events"][0]["status"] == "CREATED"

def test_customer_tracking_and_data_privacy(client, admin_token):
    """
    CRITICAL COURSE REQUIREMENT: Verify customer tracking data minimization.
    Customer must see checkpoint events, but NEVER private recipient PII.
    """
    # 1. Create shipment
    create_res = client.post(
        "/api/shipments",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "product_name": "Encrypted Cloud Hardware Key",
            "recipient_name": "Dr. Confidential",
            "recipient_phone": "+91 9123456789",
            "destination_address": "Top Secret Research Lab, Wing 4",
            "destination_city": "Mumbai",
            "initial_location": "Secure Dispatch Hub"
        }
    )
    assert create_res.status_code == 201
    tracking_id = create_res.json()["tracking_id"]

    # 2. Query public customer tracking endpoint
    track_res = client.get(f"/api/track/{tracking_id}")
    assert track_res.status_code == 200
    track_data = track_res.json()

    # Public tracking telemetry is present
    assert track_data["tracking_id"] == tracking_id
    assert track_data["product_name"] == "Encrypted Cloud Hardware Key"
    assert track_data["destination_city"] == "Mumbai"
    assert track_data["current_status"] == "CREATED"
    assert len(track_data["events"]) == 1

    # Personal Identifiable Information (PII) is STRICTLY ABSENT
    assert "recipient_phone" not in track_data
    assert "destination_address" not in track_data
    assert "recipient_name" not in track_data

def test_invalid_status_transition_rejection(client, admin_token):
    """
    Test delivery state-machine transition guardrails.
    Direct jump from CREATED to DELIVERED must be rejected with 400 Bad Request.
    """
    # Create shipment
    create_res = client.post(
        "/api/shipments",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "product_name": "State Machine Test Package",
            "recipient_name": "Alice Smith",
            "recipient_phone": "+91 9876543210",
            "destination_address": "123 Main Street",
            "destination_city": "Delhi",
            "initial_location": "Delhi Sorting Hub"
        }
    )
    shipment_id = create_res.json()["id"]

    # Attempt illegal transition: CREATED -> DELIVERED
    illegal_res = client.post(
        f"/api/shipments/{shipment_id}/events",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "status": "DELIVERED",
            "checkpoint_location": "Delhi Terminal",
            "remarks": "Bypassing intermediate checkpoints"
        }
    )
    assert illegal_res.status_code == 400
    assert "Illegal status transition" in illegal_res.json()["detail"]

def test_valid_sequential_delivery_lifecycle(client, admin_token):
    """
    Simulate full practical delivery lifecycle:
    CREATED -> PACKED -> DISPATCHED -> IN_TRANSIT -> OUT_FOR_DELIVERY -> DELIVERED.
    """
    # 1. Create
    create_res = client.post(
        "/api/shipments",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "product_name": "Robotics Development Kit",
            "recipient_name": "Bob Martin",
            "recipient_phone": "+91 9444332211",
            "destination_address": "Sector 62, Tech Zone",
            "destination_city": "Noida",
            "initial_location": "Central Warehouse"
        }
    )
    shipment_id = create_res.json()["id"]
    tracking_id = create_res.json()["tracking_id"]

    stages = [
        ("PACKED", "Packaging Station 2", "Boxed and sealed with tamper-evident tape"),
        ("DISPATCHED", "Gateway Outbound Dock", "Loaded onto line-haul truck LH-402"),
        ("IN_TRANSIT", "Mid-way Hub Agra", "Scanned at transit facility"),
        ("OUT_FOR_DELIVERY", "Noida Delivery Center", "Assigned to courier van"),
        ("DELIVERED", "Customer Doorstep", "Handed over to recipient with signature confirmation")
    ]

    for status, location, remarks in stages:
        step_res = client.post(
            f"/api/shipments/{shipment_id}/events",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "status": status,
                "checkpoint_location": location,
                "remarks": remarks
            }
        )
        assert step_res.status_code == 200
        assert step_res.json()["current_status"] == status

    # Final public verification
    final_track = client.get(f"/api/track/{tracking_id}").json()
    assert final_track["current_status"] == "DELIVERED"
    # 1 initial CREATED + 5 sequential steps = 6 immutable events
    assert len(final_track["events"]) == 6

def test_invalid_phone_number_rejection(client, admin_token):
    """Test that malformed phone numbers are rejected with 422 Unprocessable Entity."""
    response = client.post(
        "/api/shipments",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "product_name": "Validation Test Item",
            "recipient_name": "Valid Name",
            "recipient_phone": "12345",  # Too short (< 10 digits)
            "destination_address": "123 Main Street, Sector 15",
            "destination_city": "Pune",
            "initial_location": "Central Warehouse"
        }
    )
    assert response.status_code == 422
    assert "Invalid phone format" in str(response.json())

def test_invalid_tracking_id_format_rejection(client):
    """Test that malformed tracking IDs return 400 Bad Request."""
    response = client.get("/api/track/MALFORMED_123")
    assert response.status_code == 400
    assert "Invalid tracking ID format" in response.json()["detail"]

def test_delete_shipment(client, admin_token):
    """Test administrator deletion of a shipment without UI button."""
    # 1. Create a shipment to delete
    create_res = client.post(
        "/api/shipments",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "product_name": "Temporary Package for Deletion",
            "recipient_name": "Delete Tester",
            "recipient_phone": "+91 9111222333",
            "destination_address": "Test Deletion Address, Lane 3",
            "destination_city": "Nagpur",
            "initial_location": "Nagpur Hub"
        }
    )
    assert create_res.status_code == 201
    tracking_id = create_res.json()["tracking_id"]

    # 2. Delete by tracking_id
    delete_res = client.delete(
        f"/api/shipments/{tracking_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert delete_res.status_code == 200
    assert delete_res.json()["status"] == "success"

    # 3. Verify it is gone from tracking endpoint
    track_res = client.get(f"/api/track/{tracking_id}")
    assert track_res.status_code == 404


