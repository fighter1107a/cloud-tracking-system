# System Architecture & Technical Specifications

**Project:** Cloud-Based Product Delivery & Real-Time Tracking System  
**Course:** Cloud Computing (Sem 5)

---

## 1. High-Level Cloud Architecture

```mermaid
graph TD
    subgraph Clients["Edge & Client Layer"]
        Customer["Customer Device<br/>(Public Tracking Portal)"]
        Admin["Administrator Device<br/>(Operations Dashboard)"]
    end

    subgraph CDN["Edge Caching & Content Delivery"]
        CF["Amazon CloudFront (HTTPS/TLS)"]
        S3["Amazon S3 Bucket<br/>(index.html, admin.html, CSS, JS)"]
    end

    subgraph PublicVPC["VPC Public Subnet"]
        Nginx["Nginx Reverse Proxy / Port 80/443"]
    end

    subgraph PrivateVPC["VPC Private Subnet"]
        EC2["Amazon EC2 Linux VM<br/>(FastAPI + Uvicorn + systemd)"]
        RDS[("Amazon RDS PostgreSQL<br/>(Port 5432 - Restricted SG)")]
    end

    subgraph Observability["Management & Observability"]
        CW["Amazon CloudWatch<br/>(Logs, Metrics & Alarms)"]
        IAM["AWS IAM Role<br/>(Least-Privilege Profile)"]
    end

    Customer -->|HTTPS| CF
    Admin -->|HTTPS| CF
    CF --> S3
    Customer -->|REST API /api/track/| Nginx
    Admin -->|REST API /api/shipments/| Nginx
    Nginx -->|Internal Proxy 127.0.0.1:8000| EC2
    EC2 -->|SQL Transactions| RDS
    EC2 -->|Telemetry Stream| CW
    IAM -.->|Assigned To| EC2
```

---

## 2. Database Entity-Relationship Diagram (ERD)

```mermaid
erDiagram
    ADMIN_USERS {
        int id PK
        string username UK
        string hashed_password
        boolean is_active
        datetime created_at
    }

    SHIPMENTS {
        int id PK
        string tracking_id UK "e.g. TRK-2026-10001"
        string product_name
        string recipient_name "Admin Only (PII)"
        string recipient_phone "Admin Only (PII)"
        string destination_city "Public"
        text destination_address "Admin Only (PII)"
        string current_status "CREATED ... DELIVERED"
        datetime created_at
        datetime updated_at
    }

    TRACKING_EVENTS {
        int id PK
        int shipment_id FK
        string status "Target Status"
        string checkpoint_location "City / Facility"
        text remarks "Optional"
        datetime event_timestamp
    }

    SHIPMENTS ||--o{ TRACKING_EVENTS : "contains immutable audit trail"
```

---

## 3. Delivery Lifecycle State Machine

```mermaid
stateDiagram-v2
    [*] --> CREATED: Admin Registers Shipment
    CREATED --> PACKED: Origin Hub Scans & Boxes
    PACKED --> DISPATCHED: Outbound Linehaul Loaded
    DISPATCHED --> IN_TRANSIT: Intermediate Transit Facility
    IN_TRANSIT --> IN_TRANSIT: Next Regional Checkpoint
    IN_TRANSIT --> OUT_FOR_DELIVERY: Local Courier Van Dispatched
    OUT_FOR_DELIVERY --> DELIVERED: Recipient Signature Handover
    OUT_FOR_DELIVERY --> IN_TRANSIT: Delivery Attempt Rescheduled
    
    CREATED --> CANCELLED: Order Terminated
    PACKED --> CANCELLED: Order Terminated
    DISPATCHED --> CANCELLED: Order Terminated
    
    DELIVERED --> [*]: Terminal State
    CANCELLED --> [*]: Terminal State
```

---

## 4. Cloud Security & Privacy Guarantees

1. **Zero Customer PII Exposure:**
   - The public `/api/track/{tracking_id}` endpoint selectively serializes data using `CustomerTrackingResponse`. Fields such as `recipient_name`, `recipient_phone`, and `destination_address` are omitted from the response schema.
2. **Database Isolation:**
   - In AWS, RDS PostgreSQL is deployed without a public IP. Security group `sg-tracking-rds` accepts inbound TCP on port `5432` strictly from `sg-tracking-ec2`.
3. **IAM Least Privilege:**
   - No permanent AWS Access Keys or Secret Keys are stored in configuration files or code. EC2 inherits credentials dynamically via instance profile roles.
4. **Parameterized Queries:**
   - SQLAlchemy ORM parameterizes all SQL queries automatically, preventing SQL injection vulnerabilities.
