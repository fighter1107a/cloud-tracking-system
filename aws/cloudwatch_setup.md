# Amazon CloudWatch Monitoring & Alarm Demonstration Guide

This guide describes how to configure **Amazon CloudWatch** to collect system metrics, stream application logs, and demonstrate an automated high-CPU alarm as required for the Cloud Computing course project.

---

## 1. CloudWatch Architecture & Telemetry Flow

```
[ Amazon EC2 Instance ] ──▶ CloudWatch Agent ──▶ [ CloudWatch Logs: /aws/ec2/tracking-system ]
          │                                  └─▶ [ CloudWatch Metrics: CPUUtilization, Memory ]
          │
          ▼
   [ Under Locust Load ]
          │
          ▼ (CPU > 70% for 1 evaluation period)
[ CloudWatch Alarm: `EC2-Tracking-HighCPU-Alarm` ] ──▶ [ Amazon SNS Notification ]
```

---

## 2. Setting Up the CloudWatch Unified Agent on EC2

1. **Attach IAM Role**:
   - In AWS IAM, create a role with policy: `CloudWatchAgentServerPolicy`.
   - Attach this role to your EC2 instance: **EC2 Console $\to$ Actions $\to$ Security $\to$ Modify IAM role**.

2. **Install CloudWatch Agent on EC2**:
   ```bash
   sudo wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
   sudo dpkg -i -E ./amazon-cloudwatch-agent.deb
   ```

3. **Configure Log & Metric Collection**:
   Create `/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json`:
   ```json
   {
     "agent": {
       "metrics_collection_interval": 60,
       "run_as_user": "root"
     },
     "logs": {
       "logs_collected": {
         "files": {
           "collect_list": [
             {
               "file_path": "/var/log/syslog",
               "log_group_name": "/aws/ec2/tracking-system/syslog",
               "log_stream_name": "{instance_id}"
             },
             {
               "file_path": "/var/log/nginx/access.log",
               "log_group_name": "/aws/ec2/tracking-system/nginx-access",
               "log_stream_name": "{instance_id}"
             }
           ]
         }
       }
     },
     "metrics": {
       "metrics_collected": {
         "mem": {
           "measurement": ["mem_used_percent"]
         }
       }
     }
   }
   ```

4. **Start the Agent**:
   ```bash
   sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
       -a fetch-config -m ec2 -s -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json
   ```

---

## 3. Creating the CloudWatch High CPU Alarm (Course Demonstration)

1. Open **CloudWatch Console** $\to$ **Alarms** $\to$ **Create Alarm**.
2. **Select Metric**:
   - Navigate to **EC2 $\to$ Per-Instance Metrics $\to$ CPUUtilization**.
   - Select your tracking system EC2 instance.
3. **Specify Conditions**:
   - Threshold type: **Static**
   - Whenever `CPUUtilization` is: **Greater than (>) 70%**
   - Evaluation period: **1 minute**
4. **Configure Actions**:
   - State trigger: **In alarm**
   - Send notification to: Create an **SNS topic** with your email (e.g. `student-tracking-alerts`).
5. **Name the Alarm**: `TrackingSystem-EC2-HighCPU`.

---

## 4. Triggering the Alarm for Project Demonstration

To demonstrate the alarm changing from `OK` $\to$ `In Alarm` during your project evaluation, use Locust or the Linux `stress` utility:

### Method A: Locust Real Traffic Flood
```powershell
.\.venv\Scripts\python.exe -m locust -f load_testing/locustfile.py --host http://YOUR-EC2-IP --headless -u 100 -r 10 --run-time 3m
```

### Method B: CPU Synthetic Load on EC2
```bash
sudo apt-get install -y stress
# Run 2 CPU workers for 2 minutes
stress --cpu 2 --timeout 120s
```

### Evidence Collection:
- Take a screenshot of the **CloudWatch Alarm graph** transitioning from green (`OK`) to red (`In Alarm`).
- Take a screenshot of the automated email received from **Amazon SNS**.
- Include these screenshots in the final project report to prove active cloud monitoring!
