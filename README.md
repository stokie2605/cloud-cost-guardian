# Cloud Cost Guardian
<img src="screenshots/cloud-cost-dashboard.png" width="800" alt="Cloud Optimization Dashboard">
> **The 1-Line Mission:** Automated AWS FinOps scanner that detects idle EC2 resources and estimates wasted monthly spend for DevOps and Cloud engineering teams.

### ⚡ Engineering Breakdown
* **The Problem:** Cloud estates quietly accumulate orphaned storage and unused public IP addresses, leading to silent, recurring monthly waste and weak operational visibility.
* **The Solution:** A containerized Python scanner that queries EC2 APIs via Boto3, calculates monthly and annualized waste estimates, outputs structured logs to CloudWatch, and triggers Discord/Slack alerts, accompanied by a React/Vite visualization dashboard.
* **The Tech Stack:** `AWS Boto3` `Python` `React` `Docker`

---

## 🎥 Visual Preview

```text
+--------------------------+----------------+
| Governance Metric        | Current Scan   |
+--------------------------+----------------+
| Unattached EBS volumes   | 2              |
| Idle Elastic IPs         | 1              |
| Monthly waste estimate   | $24.00         |
| Annualized waste         | $288.00        |
+--------------------------+----------------+
```

---

## ⚙️ Architecture & Governance Logic
```text
EventBridge Schedule
   |
   v
ECS Fargate Task
   |
   v
Python boto3 Scanner
   |
   +--> EC2 DescribeVolumes
   +--> EC2 DescribeAddresses
   |
   v
CloudWatch Logs
   |
   +--> Optional Discord/Slack Webhook Alert
```

- **Metadata Discovery:** Queries EC2 API endpoints using `boto3` to audit unattached EBS volumes (filtered by `state == 'available'`) and unassigned Elastic IP addresses.
- **Cost Calculation:** Computes wasted spend based on local region pricing rates (defaults to `eu-west-2`).
- **Containerized Run:** Packageable via `Dockerfile` for execution as an AWS EventBridge-triggered scheduled task under ECS Fargate.
- **Reporting Feed:** Outputs JSON structures to standard stdout for easy CloudWatch ingestion, alongside optional Slack/Discord webhook alerts.

---

## 🛠️ Local Execution & Setup

### Running with Docker (Recommended)
1. Configure your AWS credentials in `.env` (refer to `.env.example`).
2. Build and start the containerized scanner and React dashboard:
   ```bash
   docker-compose up --build
   ```

### Running Unit Tests Locally
This repository contains a mock-based `pytest` suite ensuring offline verification:
1. Install dependencies:
   ```bash
   pip install -r requirements.txt -r requirements-dev.txt
   ```
2. Execute test run:
   ```bash
   python -m pytest
   ```


### Recent Project Cleanups & Upgrades
* **Project Organization:** Cleaned up project folders by separating backend logic, frontend code, and testing suites.
* **Security Fixes:** Swapped out weak authentication methods for secure hashing and tokens to protect user data.
* **Database Tuning:** Reorganized database tables and data types to make queries run faster and handle dates/times properly.
* **Code Cleanup:** Removed dead code, optimized slow loops, and set up strict linting rules to keep the codebase easy to read.
