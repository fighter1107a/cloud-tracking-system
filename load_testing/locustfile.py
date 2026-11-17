import random
from locust import HttpUser, task, between, tag

SAMPLE_TRACKING_IDS = [
    "TRK-2026-10001",
    "TRK-2026-10002",
    "TRK-2026-10003",
    "TRK-2026-10004",
    "TRK-2026-10005"
]

CITIES = ["Mumbai", "Bangalore", "Delhi", "Hyderabad", "Pune", "Chennai"]
PRODUCTS = ["Wireless Headphones", "Cloud IoT Gateway", "Smart Watch", "Developer Laptop", "Mechanical Keyboard"]

class CustomerTrackingUser(HttpUser):
    """
    Simulates real-world customer behavior:
    High concurrency read traffic querying shipment statuses and health probes.
    """
    weight = 9
    wait_time = between(1, 3)

    @task(3)
    @tag('health')
    def check_health(self):
        """Simulates automated load balancer or uptime health probes."""
        self.client.get("/health", name="/health [Probe]")

    @task(6)
    @tag('track_valid')
    def track_existing_shipment(self):
        """Simulates customer looking up their package status."""
        tracking_id = random.choice(SAMPLE_TRACKING_IDS)
        self.client.get(f"/api/track/{tracking_id}", name="/api/track/[valid_id]")

    @task(1)
    @tag('track_invalid')
    def track_nonexistent_shipment(self):
        """Tests system error handling and negative cache response times."""
        random_code = f"TRK-2026-{random.randint(90000, 99999)}"
        with self.client.get(f"/api/track/{random_code}", name="/api/track/[invalid_id]", catch_response=True) as response:
            if response.status_code == 404:
                response.success()
            else:
                response.failure(f"Expected 404 but got {response.status_code}")

class AdminOperationsUser(HttpUser):
    """
    Simulates administrator back-office operations:
    Lower frequency write traffic creating shipments and updating delivery milestones.
    """
    weight = 1
    wait_time = between(3, 7)
    token = None

    def on_start(self):
        """Authenticate session upon virtual user launch."""
        res = self.client.post("/api/auth/login-json", json={
            "username": "admin",
            "password": "Admin@2026"
        }, name="/api/auth/login-json")
        if res.status_code == 200:
            self.token = res.json().get("access_token")

    @task(3)
    @tag('admin_list')
    def list_all_shipments(self):
        """List current shipments."""
        if not self.token:
            return
        headers = {"Authorization": f"Bearer {self.token}"}
        self.client.get("/api/shipments?limit=25", headers=headers, name="/api/shipments [List]")

    @task(1)
    @tag('admin_create')
    def create_and_progress_shipment(self):
        """Creates a new shipment and advances its status to PACKED."""
        if not self.token:
            return
        headers = {"Authorization": f"Bearer {self.token}"}
        
        city = random.choice(CITIES)
        product = random.choice(PRODUCTS)
        
        # 1. Create shipment
        res = self.client.post("/api/shipments", headers=headers, json={
            "product_name": f"{product} (Load Test)",
            "recipient_name": "Test Recipient",
            "recipient_phone": "+91 9876500000",
            "destination_address": "Locust Automated Test Address",
            "destination_city": city,
            "initial_location": f"{city} Fulfillment Hub"
        }, name="/api/shipments [Create]")
        
        if res.status_code == 201:
            shipment_id = res.json()["id"]
            # 2. Advance to PACKED
            self.client.post(f"/api/shipments/{shipment_id}/events", headers=headers, json={
                "status": "PACKED",
                "checkpoint_location": f"{city} Packing Station",
                "remarks": "Automated verification under load"
            }, name="/api/shipments/[id]/events [Update]")
