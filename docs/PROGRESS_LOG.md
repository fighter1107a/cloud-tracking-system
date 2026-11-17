# Course Project Progress Log & Milestone Tracker

**Project Title:** Cloud-Based Product Delivery and Real-Time Tracking System  
**Course:** Cloud Computing (SEM 5)  
**System Architecture:** Three-Tier Cloud Architecture (FastAPI + PostgreSQL on RDS + S3/CloudFront)  
**Status:** In Active Development & Local Verification Phase

---

## 1. Project Milestone Overview

| Milestone | Phase Description | Target Deliverable | Status |
| :---: | :--- | :--- | :---: |
| **M1** | **Requirements, Architecture & Environment Setup** | Python 3.11 virtual environment, dependency management, project directory structure, architecture documentation. | 🟢 **Completed** |
| **M2** | **Data Models & State Machine Engine** | PostgreSQL database schemas (`shipments`, `tracking_events`), state transition validation (`CREATED` $\to$ `DELIVERED`), atomic transactions. | 🟢 **Completed** |
| **M3** | **REST API & Security Subsystem** | FastAPI routes (`/api/shipments`, `/api/track/{id}`, `/health`), JWT authentication, password hashing, customer data minimization (zero PII leakage). | 🟢 **Completed** |
| **M4** | **Dual Web Interfaces (Frontend)** | Modern Administrator Dashboard (create & update shipments) + Customer Tracking Portal (timeline, checkpoints). | 🟢 **Completed** |
| **M5** | **Local Verification & Automated Testing** | End-to-end integration test suite (`test_backend.py`), invalid status transition prevention, customer privacy assertion. | 🟢 **Completed** |
| **M6** | **Cloud Load Simulation (Locust)** | Realistic multi-user load testing script measuring RPS, latency percentiles (p50/p95/p99), and error rates. | 🟢 **Completed** |
| **M7** | **AWS Cloud Deployment Specifications** | EC2 `systemd` service configuration, Nginx reverse proxy config, RDS private subnet security group guide, S3 hosting guide. | 🟢 **Completed** |
| **M8** | **CloudWatch Monitoring & Alarms Guide** | Observability design, log streaming, EC2 CPU utilization alarm, automated operational health checks. | 🟢 **Completed** |

---

## 2. Cloud Computing Concepts Demonstrated

```
┌────────────────────────────────────────────────────────────────────────┐
│                        AWS CLOUD INFRASTRUCTURE                        │
├────────────────────────────────┬───────────────────────────────────────┤
│ Concept / Service              │ Practical Implementation in Project   │
├────────────────────────────────┼───────────────────────────────────────┤
│ Infrastructure as a Service    │ Amazon EC2 hosting FastAPI with       │
│ (IaaS)                         │ systemd daemon for automatic restart   │
├────────────────────────────────┼───────────────────────────────────────┤
│ Database as a Service (DBaaS)  │ Amazon RDS PostgreSQL in private      │
│                                │ subnet; DB port 5432 ingress from EC2 │
├────────────────────────────────┼───────────────────────────────────────┤
│ Object Storage & CDN           │ Amazon S3 static website hosting +    │
│                                │ CloudFront for low-latency HTTPS      │
├────────────────────────────────┼───────────────────────────────────────┤
│ Cloud Security & IAM           │ Least-privilege IAM instance profile, │
│                                │ bcrypt password hashing, zero PII leak│
├────────────────────────────────┼───────────────────────────────────────┤
│ Cloud Observability & Alarms   │ Amazon CloudWatch metrics, logs, and  │
│                                │ high-CPU threshold alert simulation   │
├────────────────────────────────┼───────────────────────────────────────┤
│ Scalability & Performance      │ Locust benchmark testing: concurrency,│
│ Testing                        │ response times, throughput (req/sec)  │
└────────────────────────────────┴───────────────────────────────────────┘
```

---

## 3. Progress Verification Log

- **[2026-10-14]** Project workspace initialized; isolated Python 3.11 environment configured.
- **[2026-10-14]** Core dependencies specified (`FastAPI`, `Uvicorn`, `SQLAlchemy`, `psycopg2-binary`, `Locust`, `pytest`).
- **[2026-10-14]** Database schema established for shipments and immutable tracking history checkpoints.
- **[2026-10-14]** Delivery lifecycle state machine created with strict transition guardrails.
- **[2026-10-14]** Customer data minimization implemented: Public tracking API never returns recipient phone number or physical address.
- **[2026-10-28]** Input validation guardrails implemented across frontend and backend: phone number format & digit count (10-15 digits), recipient name format, address minimum length, tracking ID regex (`TRK-YYYY-NNNNN`), and Pydantic 422 error parsing.
