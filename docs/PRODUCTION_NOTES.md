# Production Notes

Cloud Cost Guardian is portfolio-ready as a scanner pattern and demo dashboard. In a production AWS account, the scanner would normally run as a scheduled ECS/Fargate task with a task role, CloudWatch logs, and a controlled alert destination.

## Runtime Flow

```text
EventBridge Schedule
  -> ECS Fargate Task
  -> Python boto3 Scanner
  -> CloudWatch Logs
  -> Optional webhook alert
  -> Optional ticket / FinOps workflow
```

## Configuration

Copy `.env.example` for local dry runs:

```bash
AWS_DEFAULT_REGION=eu-west-2
COST_ALERT_WEBHOOK=https://example.com/webhook
```

The scanner also supports standard boto3 credential sources such as AWS profiles, environment variables, or ECS task roles.

## Review Without AWS Credentials

Use the mock mode:

```bash
python cost_guardian.py --mock
```

A representative output fixture is available at `docs/sample-scan-output.json`.

## Production Extensions

- Move webhook values into AWS Secrets Manager or ECS task secrets.
- Send summary metrics to CloudWatch metrics or a FinOps datastore.
- Route high-waste findings into Slack, Teams, Jira, ServiceNow, or a helpdesk queue.
- Replace static waste estimates with AWS Pricing or Cost Explorer data.
