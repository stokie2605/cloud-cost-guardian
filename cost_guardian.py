#!/usr/bin/env python3
"""Cloud Cost Guardian: live AWS idle resource scanner for ECS Fargate."""

from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

import boto3
import requests
from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError, NoRegionError

DEFAULT_REGION = "eu-west-2"
DEFAULT_EBS_MONTHLY_WASTE_USD = 10.0
DEFAULT_EIP_MONTHLY_WASTE_USD = 4.0
WEBHOOK_TIMEOUT_SECONDS = 10


@dataclass(frozen=True)
class WasteFinding:
    resource_type: str
    resource_id: str
    region: str
    estimated_monthly_waste_usd: float
    reason: str


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def get_region() -> str:
    return os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or DEFAULT_REGION


def print_log(level: str, message: str, **context: Any) -> None:
    """Emit CloudWatch-friendly structured log lines through stdout."""
    payload = {
        "timestamp": utc_now(),
        "level": level.upper(),
        "message": message,
        **context,
    }
    print(json.dumps(payload, default=str), flush=True)


def create_ec2_client(region: str):
    return boto3.client("ec2", region_name=region)


def find_unattached_ebs_volumes(ec2_client, region: str) -> list[WasteFinding]:
    print_log("info", "Scanning for unattached EBS volumes", region=region)
    findings: list[WasteFinding] = []

    paginator = ec2_client.get_paginator("describe_volumes")
    for page in paginator.paginate(Filters=[{"Name": "status", "Values": ["available"]}]):
        for volume in page.get("Volumes", []):
            volume_id = volume.get("VolumeId", "unknown-volume")
            size_gb = volume.get("Size", "unknown")
            volume_type = volume.get("VolumeType", "unknown")
            findings.append(
                WasteFinding(
                    resource_type="ebs_volume",
                    resource_id=volume_id,
                    region=region,
                    estimated_monthly_waste_usd=DEFAULT_EBS_MONTHLY_WASTE_USD,
                    reason=(
                        f"EBS volume is in 'available' state and unattached "
                        f"(size={size_gb}GB, type={volume_type})."
                    ),
                )
            )
            print_log(
                "warning",
                "Unattached EBS volume detected",
                resource_id=volume_id,
                size_gb=size_gb,
                volume_type=volume_type,
                estimated_monthly_waste_usd=DEFAULT_EBS_MONTHLY_WASTE_USD,
            )

    return findings


def find_idle_elastic_ips(ec2_client, region: str) -> list[WasteFinding]:
    print_log("info", "Scanning for idle Elastic IP addresses", region=region)
    findings: list[WasteFinding] = []

    response = ec2_client.describe_addresses()
    for address in response.get("Addresses", []):
        if address.get("AssociationId"):
            continue

        allocation_id = address.get("AllocationId")
        public_ip = address.get("PublicIp", "unknown-ip")
        resource_id = allocation_id or public_ip
        findings.append(
            WasteFinding(
                resource_type="elastic_ip",
                resource_id=resource_id,
                region=region,
                estimated_monthly_waste_usd=DEFAULT_EIP_MONTHLY_WASTE_USD,
                reason=f"Elastic IP address {public_ip} has no AssociationId and appears idle.",
            )
        )
        print_log(
            "warning",
            "Idle Elastic IP detected",
            resource_id=resource_id,
            public_ip=public_ip,
            estimated_monthly_waste_usd=DEFAULT_EIP_MONTHLY_WASTE_USD,
        )

    return findings


def build_summary(region: str, findings: list[WasteFinding]) -> dict[str, Any]:
    ebs_findings = [item for item in findings if item.resource_type == "ebs_volume"]
    eip_findings = [item for item in findings if item.resource_type == "elastic_ip"]
    total_monthly_waste = sum(item.estimated_monthly_waste_usd for item in findings)

    return {
        "project": "Cloud Cost Guardian",
        "generated_at": utc_now(),
        "region": region,
        "summary": {
            "unattached_ebs_volume_count": len(ebs_findings),
            "idle_elastic_ip_count": len(eip_findings),
            "finding_count": len(findings),
            "estimated_monthly_waste_usd": round(total_monthly_waste, 2),
            "estimated_annual_waste_usd": round(total_monthly_waste * 12, 2),
        },
        "estimation_model": {
            "ebs_volume_monthly_usd": DEFAULT_EBS_MONTHLY_WASTE_USD,
            "idle_elastic_ip_monthly_usd": DEFAULT_EIP_MONTHLY_WASTE_USD,
            "note": "Static portfolio estimates. Replace with AWS pricing or Cost Explorer for production finance reporting.",
        },
        "findings": [asdict(item) for item in findings],
    }


def build_webhook_payload(summary: dict[str, Any]) -> dict[str, Any]:
    finding_count = summary["summary"]["finding_count"]
    monthly_waste = summary["summary"]["estimated_monthly_waste_usd"]
    annual_waste = summary["summary"]["estimated_annual_waste_usd"]
    region = summary["region"]

    title = "Cloud Cost Guardian Scan Complete"
    description = (
        f"Found {finding_count} idle AWS resource(s) in `{region}` with an estimated "
        f"monthly waste of `${monthly_waste:,.2f}`."
    )

    return {
        "username": "Cloud Cost Guardian",
        "content": f"**{title}**\n{description}",
        "embeds": [
            {
                "title": title,
                "description": description,
                "color": 15158332 if finding_count else 3066993,
                "fields": [
                    {
                        "name": "Unattached EBS Volumes",
                        "value": str(summary["summary"]["unattached_ebs_volume_count"]),
                        "inline": True,
                    },
                    {
                        "name": "Idle Elastic IPs",
                        "value": str(summary["summary"]["idle_elastic_ip_count"]),
                        "inline": True,
                    },
                    {
                        "name": "Monthly Waste",
                        "value": f"${monthly_waste:,.2f}",
                        "inline": True,
                    },
                    {
                        "name": "Annualized Waste",
                        "value": f"${annual_waste:,.2f}",
                        "inline": True,
                    },
                ],
                "footer": {"text": "Cloud Cost Guardian | ECS Fargate scheduled scan"},
                "timestamp": summary["generated_at"],
            }
        ],
        "cloud_cost_guardian": summary,
    }


def send_webhook(summary: dict[str, Any]) -> None:
    webhook_url = os.getenv("COST_ALERT_WEBHOOK")
    if not webhook_url:
        print_log("info", "COST_ALERT_WEBHOOK not set; skipping alert delivery")
        return

    payload = build_webhook_payload(summary)
    print_log("info", "Sending cost alert webhook", finding_count=summary["summary"]["finding_count"])

    try:
        response = requests.post(webhook_url, json=payload, timeout=WEBHOOK_TIMEOUT_SECONDS)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        print_log("error", "Webhook delivery timed out", timeout_seconds=WEBHOOK_TIMEOUT_SECONDS)
        raise
    except requests.exceptions.HTTPError as error:
        print_log(
            "error",
            "Webhook endpoint returned an HTTP error",
            status_code=error.response.status_code if error.response is not None else "unknown",
        )
        raise
    except requests.exceptions.RequestException as error:
        print_log("error", "Webhook delivery failed", error=str(error))
        raise

    print_log("info", "Webhook alert delivered successfully", status_code=response.status_code)


def run() -> int:
    region = get_region()
    print_log("info", "Starting Cloud Cost Guardian AWS scan", region=region)

    try:
        ec2_client = create_ec2_client(region)
        findings = [
            *find_unattached_ebs_volumes(ec2_client, region),
            *find_idle_elastic_ips(ec2_client, region),
        ]
        summary = build_summary(region, findings)
        print_log("info", "Cloud Cost Guardian scan summary", **summary["summary"])
        print(json.dumps(summary, indent=2), flush=True)
        send_webhook(summary)
    except NoCredentialsError:
        print_log("critical", "AWS credentials were not found for the ECS task role or local environment")
        return 1
    except NoRegionError:
        print_log("critical", "AWS region was not configured", default_region=DEFAULT_REGION)
        return 1
    except ClientError as error:
        print_log(
            "critical",
            "AWS API call failed",
            error_code=error.response.get("Error", {}).get("Code"),
            error_message=error.response.get("Error", {}).get("Message"),
        )
        return 1
    except BotoCoreError as error:
        print_log("critical", "AWS SDK failure occurred", error=str(error))
        return 1
    except requests.exceptions.RequestException:
        return 1
    except Exception as error:  # noqa: BLE001 - final guardrail for scheduled task reliability.
        print_log("critical", "Unexpected scanner failure", error=str(error))
        return 1

    print_log("info", "Cloud Cost Guardian scan completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(run())
