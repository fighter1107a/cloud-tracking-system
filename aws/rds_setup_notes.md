# Amazon RDS PostgreSQL Configuration Guide

This guide details how to provision and configure **Amazon RDS (PostgreSQL)** for the Cloud-Based Product Delivery & Real-Time Tracking System, adhering to cloud security best practices and the Principle of Least Privilege.

---

## 1. Cloud Architecture & Network Isolation

```
 Internet
    │
    ▼ (Port 80 / 443 - Public Subnet)
[ EC2 Security Group: `sg-tracking-ec2` ]
    │
    ▼ (Port 5432 - Internal VPC Traffic Only)
[ RDS Security Group: `sg-tracking-rds` ]
    │
    ▼ (Private Subnets - No Public IP)
[ Amazon RDS PostgreSQL Instance ]
```

---

## 2. Step-by-Step RDS Provisioning in AWS Console

1. **Open AWS RDS Console** $\to$ Click **Create Database**.
2. **Database Engine**:
   - Engine type: **PostgreSQL**
   - Version: **PostgreSQL 15.x** or **16.x**
3. **Template**:
   - Select **Free tier** (uses `db.t3.micro` or `db.t4g.micro`, 20 GiB gp2/gp3 storage).
4. **Settings**:
   - DB instance identifier: `tracking-postgres-db`
   - Master username: `tracking_admin`
   - Master password: `ChooseStrongPassword2026!`
5. **Connectivity**:
   - Virtual Private Cloud (VPC): Select your default VPC or custom VPC.
   - Subnet group: Private subnets (where possible).
   - **Public Access**: Select **No** (Prevents direct internet scans or brute-force attempts).
   - VPC Security Group: Create new $\to$ `sg-tracking-rds`.
6. **Initial Database Name**:
   - Under *Additional configuration* $\to$ Initial database name: `tracking_db`.
7. Click **Create database**.

---

## 3. Configuring Security Group Ingress Rules (CRITICAL FOR COURSE AUDIT)

To demonstrate cloud network perimeter security:
1. Navigate to **EC2 $\to$ Security Groups**.
2. Find `sg-tracking-rds` $\to$ **Edit inbound rules**.
3. Add Rule:
   - **Type**: PostgreSQL (`TCP`)
   - **Port**: `5432`
   - **Source**: Select **Custom** $\to$ Enter the Security Group ID of the EC2 instance (e.g. `sg-0abc1234def56789a`).
   - *Result*: The database accepts zero connections from the public internet. Only the authorized EC2 backend can communicate with PostgreSQL.

---

## 4. Connection String for Backend

Update the `.env` or systemd service file on EC2 with your RDS endpoint:
```ini
DATABASE_URL=postgresql://tracking_admin:ChooseStrongPassword2026!@tracking-postgres-db.c123456789.us-east-1.rds.amazonaws.com:5432/tracking_db
```
The FastAPI application's SQLAlchemy engine automatically verifies the connection pool and creates all tables (`shipments`, `tracking_events`, `admin_users`) on its first launch!
