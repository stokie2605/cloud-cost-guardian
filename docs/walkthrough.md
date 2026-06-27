# Cloud Cost Guardian Walkthrough

This walkthrough is designed for recruiters, hiring managers, and interviewers who want a fast understanding of the project and the DevOps practices it demonstrates.

## Scenario

A cloud account can accumulate small recurring costs from resources that are no longer attached or actively used. Two common examples are unattached EBS volumes and idle Elastic IP addresses.

This project models a lightweight FinOps scanner that can run locally, in a container, or as a scheduled ECS Fargate-style task.

## What Happens When It Runs

1. The scanner loads AWS configuration from standard `boto3` credential providers.
2. It calls EC2 APIs to list EBS volumes and Elastic IP addresses.
3. It detects unattached EBS volumes where the volume state is `available`.
4. It detects idle Elastic IPs where no `AssociationId` is present.
5. It calculates simple monthly and annualized waste estimates.
6. It writes clean execution logs to stdout for local review or CloudWatch ingestion.
7. If `COST_ALERT_WEBHOOK` is configured, it sends a formatted alert payload to Discord or Slack.
8. It exits with a clear success or failure code for automation consumers.

## Runtime Flow

```text
Python Scanner
   |
   +--> boto3 EC2 DescribeVolumes
   +--> boto3 EC2 DescribeAddresses
   |
   v
Waste Findings and Summary
   |
   +--> stdout logs
   +--> optional webhook alert
```

## Scheduled Cloud Pattern

```text
EventBridge Schedule
   |
   v
ECS Fargate Task
   |
   v
Containerized Python Scanner
   |
   v
CloudWatch Logs
   |
   +--> Discord/Slack Alert
```

## Important Files

| File | Why It Matters |
| --- | --- |
| `cost_guardian.py` | Main scanner logic, AWS API calls, waste estimates, logging, and webhook alerting |
| `Dockerfile` | Packages the scanner for repeatable local or ECS-style execution |
| `docker-compose.yml` | Provides a simple local container run path |
| `.github/workflows/ci-cd.yml` | Shows CI/CD hygiene for project validation |
| `CloudDashboard.jsx` | Provides a visual portfolio dashboard for quick review |
| `screenshots/cloud-cost-dashboard.png` | Gives recruiters immediate visual context |

## DevOps Practices Demonstrated

- Cloud API automation using AWS SDK calls.
- Cost governance and infrastructure hygiene checks.
- Containerized task execution suitable for scheduled jobs.
- Clear logs and exit codes for automation platforms.
- Optional webhook integration for operational alerting.
- Documentation that explains both prototype behavior and production extension path.

## Production Extension Ideas

- Manage the ECS task, schedule, IAM role, and log group with Terraform.
- Use AWS Cost Explorer or Pricing API instead of static portfolio estimates.
- Store scan results in DynamoDB or S3 for trend reporting.
- Add CloudWatch metrics and alarms for high waste thresholds.
- Add approval workflows before releasing Elastic IPs or deleting EBS volumes.
- Route findings into Slack, Teams, Jira, ServiceNow, or a FinOps dashboard.
