# Cloud Computing Performance & Load Testing with Locust

This module executes automated load testing on the **Cloud-Based Product Delivery & Real-Time Tracking System** to evaluate cloud compute throughput, latency percentiles, and database stability under varying user concurrency.

---

## 1. Test Scenarios Simulated

1. **Customer Traffic (Weight: 90%)**:
   - High-concurrency read queries to `/api/track/{tracking_id}`.
   - Continuous `/health` checks simulating ALB or CloudWatch uptime probes.
   - Negative-lookup resilience (handling invalid tracking IDs without server error).

2. **Administrator Operations (Weight: 10%)**:
   - JWT authentication via `/api/auth/login-json`.
   - Polling shipment records (`GET /api/shipments`).
   - Transactional creation and checkpoint updates (`POST /api/shipments` and `/api/shipments/{id}/events`).

---

## 2. Running Load Tests Locally

### Option A: Interactive Web UI Mode
Run the following command from the project root:
```powershell
.\.venv\Scripts\python.exe -m locust -f load_testing/locustfile.py --host http://localhost:8000
```
Open your browser at **http://localhost:8089**:
- **Number of users**: `50` (or `200` for stress testing)
- **Spawn rate**: `5` users/second
- **Host**: `http://localhost:8000` (or your EC2 public IP/domain)
- Click **Start Swarming**.

### Option B: Headless Automated Mode (For Course Report Metrics)
To generate tabular performance statistics directly from the command line:
```powershell
.\.venv\Scripts\python.exe -m locust -f load_testing/locustfile.py --host http://localhost:8000 --headless -u 50 -r 5 --run-time 1m --csv=load_testing/results_50users
```

---

## 3. Key Metrics to Record for Course Report

| Metric | Target Cloud Objective | Observation |
| :--- | :--- | :--- |
| **Throughput (Requests/Sec)** | Measure peak requests handled without dropping connections | e.g. ~450 RPS |
| **Median Latency (p50)** | Evaluate baseline fast-path response time | e.g. < 15ms |
| **95th Percentile Latency (p95)** | Evaluate tail latency under database load | e.g. < 45ms |
| **Error Rate (%)** | Confirm resilience (should be 0.00% under normal load) | 0.00% |
| **EC2 CPU Utilization** | Check CloudWatch correlation during the test | e.g. 68% spike |
