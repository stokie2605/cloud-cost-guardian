# Cloud Cost Guardian

[![CI/CD Quality Gate](https://github.com/stokie2605/cloud-cost-guardian/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/stokie2605/cloud-cost-guardian/actions/workflows/ci-cd.yml)

[Live Demo](https://cloud-cost-guardian-ten.vercel.app)

Built by Dean Wilshaw.

Cloud Cost Guardian is an AWS FinOps automation project that scans for idle, cost-wasting resources and can run as a scheduled ECS Fargate task. The Python scanner uses `boto3` to detect unattached EBS volumes and idle Elastic IP addresses, estimates monthly waste, logs cleanly to CloudWatch, and can send a formatted Discord or Slack webhook alert.

The project is designed to demonstrate practical cloud cost governance, DevOps automation, containerized task execution, CI/CD hygiene, and operational reporting in one portfolio-ready repository.

## Recruiter Snapshot

| Area | What This Project Shows |
| --- | --- |
| Cloud Automation | Live AWS EC2 metadata discovery using `boto3` |
| FinOps | Monthly and annualized waste estimation for orphaned resources |
| Containers | Dockerized scanner suitable for scheduled ECS Fargate execution |
| Operations | CloudWatch-friendly stdout logging and webhook alert delivery |
| Portfolio UX | React/Vite dashboard and live demo for quick visual review |

## Case Study

### Problem

Cloud estates quietly accumulate orphaned storage and unused public IP addresses. These resources are easy to miss, but they create recurring monthly waste and weak operational visibility unless teams scan for them on a schedule.

### Solution

Cloud Cost Guardian models a scheduled AWS scanner. A Python script runs inside a container, uses AWS credentials or an ECS task role to query EC2 APIs, identifies unattached EBS volumes and idle Elastic IP addresses, estimates monthly and annualized waste, prints structured logs to stdout for CloudWatch, and optionally posts a formatted alert to a Discord or Slack webhook.

## Architecture

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

## DevOps Skills Demonstrated

- Built a Python scanner that uses AWS APIs instead of hardcoded findings.
- Containerized the scanner for repeatable local and ECS-style execution.
- Designed the runtime around task-role permissions and standard `boto3` credential providers.
- Added CI/CD validation through GitHub Actions.
- Produced reviewer-friendly evidence: dashboard screenshot, live demo, run commands, IAM policy notes, and production extension path.
- Modeled an operational pattern that could feed CloudWatch, ticketing, Slack, Teams, or FinOps reporting.

## Visual Output / Preview

![Cloud Cost Guardian dashboard](screenshots/cloud-cost-dashboard.png)

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

## ✅ Automated Testing

The repository contains a `pytest` suite that tests all aspects of the cost scanner without calling the live AWS API:
- Region environment variable overrides.
- Unattached EBS volume logic.
- Idle Elastic IP detection logic.
- Monthly/annualized waste estimation and rounding.
- Mocking of boto3 client paginators to verify metadata fetches.

To run the unit tests locally:
1. Install testing requirements:
   ```bash
   pip install -r requirements.txt -r requirements-dev.txt
   ```
2. Execute `pytest`:
   ```bash
   python -m pytest
   ```

The GitHub Actions CI pipeline runs these scanner tests automatically on every push.

## Scanner Architecture & Governance Logic

- Uses `boto3` to scan the active AWS account in `eu-west-2` by default.
- Detects EBS volumes with state `available`, meaning they are unattached or orphaned.
- Detects Elastic IP addresses with no `AssociationId`, meaning they are unallocated or idle.
- Uses simple portfolio estimates: `$10/month` per orphaned EBS volume and `$4/month` per idle Elastic IP.
- Prints structured execution logs to stdout so ECS/Fargate can stream them into CloudWatch.
- Checks `COST_ALERT_WEBHOOK` and sends a formatted JSON alert payload when configured.
- Returns exit code `0` on successful scan completion and `1` on critical AWS or webhook failure.

## Technical Toolkit

- **Python 3.11** for scanner logic and ECS task execution.
- **boto3** for live AWS EC2 API discovery.
- **requests** for Discord/Slack-compatible webhook delivery.
- **Docker** and **Docker Compose** for containerized scanner execution.
- **React + Vite** for the public portfolio dashboard.
- **GitHub Actions** for repository CI validation.

## Key Files

| File | Purpose |
| --- | --- |
| `cost_guardian.py` | AWS scanner for unattached EBS volumes, idle Elastic IPs, waste estimates, logs, and webhook alerts |
| `Dockerfile` | Container runtime for local or ECS-style scanner execution |
| `docker-compose.yml` | Local container execution path for repeatable scanner runs |
| `.github/workflows/ci-cd.yml` | CI/CD quality gate for repository validation |
| `CloudDashboard.jsx` | React dashboard used for the public portfolio demo |
| `screenshots/cloud-cost-dashboard.png` | Visual proof for quick recruiter review |
| `docs/walkthrough.md` | Guided explanation of the scanner workflow and production path |

## Local Scanner Usage

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the scanner with default region `eu-west-2`:

```bash
python cost_guardian.py
```

Override the region:

```bash
AWS_DEFAULT_REGION=eu-west-1 python cost_guardian.py
```

Send alerts to Discord or Slack:

```bash
COST_ALERT_WEBHOOK=https://example.com/webhook python cost_guardian.py
```

The scanner needs AWS credentials from your shell, AWS profile, ECS task role, or another standard `boto3` credential provider.

## Container Deployment

Build the image:

```bash
docker build -t cloud-cost-guardian .
```

Run the scanner with your local AWS credentials mounted:

```bash
docker run --rm \
  -e AWS_DEFAULT_REGION=eu-west-2 \
  -e COST_ALERT_WEBHOOK="$COST_ALERT_WEBHOOK" \
  -v "$HOME/.aws:/root/.aws:ro" \
  cloud-cost-guardian
```

Run through Docker Compose:

```bash
docker compose up --build
```

## ECS Fargate Runtime Notes

For ECS Fargate, attach a task role that can read EC2 volume and address metadata. Minimum useful permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeVolumes",
        "ec2:DescribeAddresses"
      ],
      "Resource": "*"
    }
  ]
}
```

Set `COST_ALERT_WEBHOOK` as an ECS task environment variable or secret if alert delivery is required.

## Finding Categories

| Category | Detection | Portfolio Estimate |
| --- | --- | ---: |
| Orphaned EBS volume | EC2 volume state is `available` | `$10/month` |
| Idle Elastic IP | EC2 address has no `AssociationId` | `$4/month` |

## Production Readiness Notes

- Replace static estimates with AWS Pricing API or Cost Explorer data for finance-grade reporting.
- Store scan history in S3, DynamoDB, or a time-series datastore for trend analysis.
- Add approval workflow before deleting or releasing resources.
- Use AWS Secrets Manager or SSM Parameter Store for webhook secrets in ECS.
- Expand detection to idle load balancers, NAT gateways, snapshots, stopped instances, and RDS resources.
- Add EventBridge scheduling and Terraform-managed ECS infrastructure if this scanner is promoted from portfolio prototype to deployed workload.

## Problems Faced & Solved

**Problem: Making the scanner look like real cloud operations work rather than a hardcoded demo**
The challenge was building something that would feel credible to a technical reviewer — not just a script that prints fake data, but something genuinely structured around how AWS cost and security tooling actually works.

**Solution:** Used `boto3` to query real EC2 and Elastic IP metadata directly, structured the output to mirror CloudWatch-style JSON logs, and documented the ECS/Fargate production path with the exact IAM permissions needed for a real deployment. The scanner flags real resource patterns (unattached EBS volumes, unused Elastic IPs) that AWS Cost Explorer and Trusted Advisor flag in production accounts.

---

## Production Notes


- Environment template: [.env.example](.env.example)
- Sample scanner output: [docs/sample-scan-output.json](docs/sample-scan-output.json)
- Production routing notes: [docs/PRODUCTION_NOTES.md](docs/PRODUCTION_NOTES.md)
