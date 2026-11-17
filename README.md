# Cloud-Based Product Delivery & Real-Time Tracking System

> **Cloud Computing Course Project (Semester 5)**  
> A three-tier cloud application demonstrating compute, managed relational storage, object distribution, security hardening, monitoring, and load performance.

---

## 🌟 Key Project Highlights

- **Cloud Compute (IaaS):** FastAPI backend designed for Amazon EC2 with a self-healing `systemd` daemon.
- **Managed Relational Storage (DBaaS):** Amazon RDS for PostgreSQL with network isolation on port 5432.
- **Frontend & Edge Acceleration:** Amazon S3 + CloudFront static hosting for low-latency HTTPS delivery.
- **Data Minimization & Privacy:** Public tracking endpoints expose checkpoint telemetry while strictly withholding recipient personal data (phone, street address, name).
- **Strict State Guardrails:** Delivery state machine prevents illegal status transitions (`CREATED` $\to$ `PACKED` $\to$ `DISPATCHED` $\to$ `IN_TRANSIT` $\to$ `OUT_FOR_DELIVERY` $\to$ `DELIVERED`).
- **Observability & Stress Testing:** Locust load test scenario simulating high-concurrency read/write traffic with Amazon CloudWatch alarms.

---

## 📁 Repository Structure

```
.
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application & route aggregator
│   │   ├── config.py            # Environment & database settings
│   │   ├── database.py          # SQLAlchemy engine & session manager
│   │   ├── models.py            # Shipments, TrackingEvents, AdminUsers
│   │   ├── schemas.py           # Pydantic validation & PII masking models
│   │   ├── auth.py              # JWT tokens & bcrypt password hashing
│   │   ├── state_machine.py     # Delivery lifecycle transition rules
│   │   └── routers/
│   │       ├── health.py        # GET /health probe
│   │       ├── auth.py          # POST /api/auth/login-json
│   │       ├── shipments.py     # Admin CRUD & checkpoint events
│   │       └── tracking.py      # Public sanitized tracking endpoint
│   └── requirements.txt         # Python dependencies
├── frontend/
│   ├── index.html               # Customer tracking portal
│   ├── admin.html               # Administrator operations dashboard
│   ├── css/
│   │   └── style.css            # Modern glassmorphism styling
│   └── js/
│       ├── app.js               # Customer tracking interactivity
│       └── admin.js             # Admin management & event updates
├── tests/
│   └── test_backend.py          # Automated integration test suite
├── load_testing/
│   ├── locustfile.py            # Multi-user cloud load simulation
│   └── README.md                # Load testing instructions
├── aws/
│   ├── systemd/
│   │   └── tracking-system.service # Linux systemd daemon configuration
│   ├── nginx/
│   │   └── tracking-system.conf   # Reverse proxy configuration
│   ├── ec2_setup.sh             # Automated EC2 setup script
│   ├── rds_setup_notes.md       # Amazon RDS configuration guide
│   └── cloudwatch_setup.md      # CloudWatch agent & alarm setup guide
├── docs/
│   ├── PROGRESS_LOG.md          # Course milestone tracker & progress record
│   └── ARCHITECTURE.md          # Architecture & dataflow diagrams
└── README.md
```

---

## 🚀 Quickstart: Running Locally on Windows

### 1. Prerequisites
- Python 3.11+ (installed in the `.venv` folder)
- Web Browser

### 2. Launch the Backend Server
Run the following command in PowerShell:
```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 3. Open the Interfaces
- **Customer Tracking Portal:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Administrator Dashboard:** [http://127.0.0.1:8000/admin.html](http://127.0.0.1:8000/admin.html)
- **Interactive OpenAPI Documentation:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health Check Endpoint:** [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

> **Default Admin Credentials:**  
> Username: `admin`  
> Password: `Admin@2026`

---

## 🧪 Running Automated Tests

Run the full integration test suite:
```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_backend.py -v -p no:cacheprovider
```

---

## ⚡ Running Locust Cloud Load Simulation

Start the interactive load testing UI:
```powershell
.\.venv\Scripts\python.exe -m locust -f load_testing/locustfile.py --host http://localhost:8000
```
Open **http://localhost:8089** to configure concurrent users and monitor throughput and response times.

---

## ☁️ AWS Cloud Deployment Roadmap

See the `aws/` directory for detailed deployment scripts and configurations:
1. **Amazon RDS:** Follow [`aws/rds_setup_notes.md`](aws/rds_setup_notes.md) to launch a PostgreSQL instance with security group restrictions.
2. **Amazon EC2:** Run [`aws/ec2_setup.sh`](aws/ec2_setup.sh) to install dependencies, configure the `systemd` unit file, and set up the Nginx reverse proxy.
3. **Amazon S3 + CloudFront:** Upload `frontend/` files to an S3 bucket configured for static website hosting with CloudFront TLS distribution.
4. **Amazon CloudWatch:** Follow [`aws/cloudwatch_setup.md`](aws/cloudwatch_setup.md) to set up CPU utilization alarms and stream application logs.
