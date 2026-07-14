# AWS Cloud Cost Guardian

An automated cloud governance and FinOps utility designed to run scheduled resource audits, identify orphaned infrastructure, and alert administrators to cloud spend leakages.

<div align="center">
  <img src="screenshots/cloud-cost-dashboard.png" width="800" alt="Cloud Optimization Dashboard">
</div>

---

### ⚡ Operational Focus
* **The Problem:** Left unchecked, cloud environments accumulate orphaned assets (such as unattached EBS volumes and idle Elastic IPs) that silently inflate enterprise AWS bills.
* **The Solution:** A Python-based automation engine that queries AWS infrastructure via the Boto3 SDK, evaluates assets against cost-compliance policies, and flags immediately actionable savings.

---

### 🛠️ Core Capabilities
* **Orphaned Asset Detection:** Automated scripts that systematically target and list unattached storage volumes and unallocated public IP addresses.
* **Resource Drift Diagnostics:** Evaluates running instance profiles and configurations to flag deviations from cloud budgeting guidelines.
* **FinOps Governance Reporting:** Generates clean, structured JSON summaries mapping detected cost leaks to specific AWS regions for rapid remediation.
* **Automated Cleanup Hooks:** Built to easily integrate with scheduled tasks (cron/Lambda) to automatically de-provision verified waste resources.

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

## 🛠️ Local Setup & Execution

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

---

## Recent Architectural Upgrades
* **Operational Restructuring:** Standardized repository file hierarchies by separating core automation logic, helper scripts, and test files.
* **Security Hardening:** Swapped legacy credential configs for environment variables and secure token validation policies.
* **Database Schema Upgrades:** Refactored primitive database types into native data structures for robust ORM and transaction handling.
* **Systems Maintenance:** Eradicated legacy diagnostic scripts, optimized loops, and established static analysis scanning to ensure code hygiene.
