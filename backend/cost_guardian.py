#!/usr/bin/env python3
"""Cloud Cost Guardian: live AWS idle resource scanner for ECS Fargate."""

from __future__ import annotations

import argparse
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scan AWS for idle cost-wasting infrastructure or run a local mock dry run."
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Bypass live boto3 AWS API calls and scan static local mock data instead.",
    )
    parser.add_argument(
        "--out",
        type=str,
        help="Path to write the JSON scan results summary.",
    )
    return parser.parse_args()


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


def get_mock_data() -> dict[str, list[dict[str, Any]]]:
    """Return static AWS-shaped mock resources for local dry runs."""
    return {
        "Volumes": [
            {
                "VolumeId": "vol-0mock001orphaned",
                "Size": 80,
                "AvailabilityZone": "eu-west-2a",
            },
            {
                "VolumeId": "vol-0mock002legacy",
                "Size": 250,
                "AvailabilityZone": "eu-west-2b",
            },
        ],
        "Addresses": [
            {
                "PublicIp": "203.0.113.10",
            },
            {
                "PublicIp": "203.0.113.25",
            },
        ],
    }


def create_ec2_client(region: str):
    endpoint_url = os.getenv("AWS_ENDPOINT_URL")
    if endpoint_url:
        print_log("info", "Using custom AWS endpoint", endpoint_url=endpoint_url)
    return boto3.client("ec2", region_name=region, endpoint_url=endpoint_url)


def fetch_live_data(region: str) -> dict[str, list[dict[str, Any]]]:
    print_log("info", "Fetching live AWS EC2 data", region=region)
    ec2_client = create_ec2_client(region)

    volumes: list[dict[str, Any]] = []
    paginator = ec2_client.get_paginator("describe_volumes")
    for page in paginator.paginate(Filters=[{"Name": "status", "Values": ["available"]}]):
        volumes.extend(page.get("Volumes", []))

    addresses = ec2_client.describe_addresses().get("Addresses", [])
    return {"Volumes": volumes, "Addresses": addresses}


def findings_from_unattached_ebs_volumes(
    volumes: list[dict[str, Any]],
    region: str,
) -> list[WasteFinding]:
    print_log("info", "Scanning for unattached EBS volumes", region=region)
    findings: list[WasteFinding] = []

    for volume in volumes:
        volume_id = volume.get("VolumeId", "unknown-volume")
        size_gb = volume.get("Size", "unknown")
        availability_zone = volume.get("AvailabilityZone", "unknown-az")
        volume_type = volume.get("VolumeType", "unknown")
        findings.append(
            WasteFinding(
                resource_type="ebs_volume",
                resource_id=volume_id,
                region=region,
                estimated_monthly_waste_usd=DEFAULT_EBS_MONTHLY_WASTE_USD,
                reason=(
                    f"EBS volume is in 'available' state and unattached "
                    f"(size={size_gb}GB, az={availability_zone}, type={volume_type})."
                ),
            )
        )
        print_log(
            "warning",
            "Unattached EBS volume detected",
            resource_id=volume_id,
            size_gb=size_gb,
            availability_zone=availability_zone,
            volume_type=volume_type,
            estimated_monthly_waste_usd=DEFAULT_EBS_MONTHLY_WASTE_USD,
        )

    return findings


def findings_from_idle_elastic_ips(
    addresses: list[dict[str, Any]],
    region: str,
) -> list[WasteFinding]:
    print_log("info", "Scanning for idle Elastic IP addresses", region=region)
    findings: list[WasteFinding] = []

    for address in addresses:
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


def build_findings(resource_data: dict[str, list[dict[str, Any]]], region: str) -> list[WasteFinding]:
    return [
        *findings_from_unattached_ebs_volumes(resource_data.get("Volumes", []), region),
        *findings_from_idle_elastic_ips(resource_data.get("Addresses", []), region),
    ]


def build_summary(region: str, findings: list[WasteFinding], mode: str) -> dict[str, Any]:
    ebs_findings = [item for item in findings if item.resource_type == "ebs_volume"]
    eip_findings = [item for item in findings if item.resource_type == "elastic_ip"]
    total_monthly_waste = sum(item.estimated_monthly_waste_usd for item in findings)

    return {
        "project": "Cloud Cost Guardian",
        "mode": mode,
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
    mode = summary["mode"]

    title = "Cloud Cost Guardian Scan Complete"
    description = (
        f"Found {finding_count} idle AWS resource(s) in `{region}` using `{mode}` mode with an "
        f"estimated monthly waste of `${monthly_waste:,.2f}`."
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
                        "name": "Mode",
                        "value": mode,
                        "inline": True,
                    },
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


def run(args: argparse.Namespace) -> int:
    region = get_region()
    mode = "mock" if args.mock else "live"
    print_log("info", "Starting Cloud Cost Guardian scan", region=region, mode=mode)

    try:
        if args.mock:
            print_log("info", "Using local mock dry-run data; boto3 AWS calls are bypassed", mode=mode)
            resource_data = get_mock_data()
        else:
            resource_data = fetch_live_data(region)

        findings = build_findings(resource_data, region)
        summary = build_summary(region, findings, mode)
        print_log("info", "Cloud Cost Guardian scan summary", **summary["summary"], mode=mode)
        print(json.dumps(summary, indent=2), flush=True)

        if args.out:
            try:
                from pathlib import Path
                out_path = Path(args.out)
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
                print_log("info", "Wrote scan results to output file", path=args.out)
            except Exception as error:
                print_log("error", "Failed to write output file", path=args.out, error=str(error))

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
        print_log("critical", "Unexpected scanner failure", error=str(error), mode=mode)
        return 1

    print_log("info", "Cloud Cost Guardian scan completed successfully", mode=mode)
    return 0


def main() -> None:
    args = parse_args()
    exit_code = run(args)
    if exit_code == 0:
        sys.exit(0)
    sys.exit(1)


if __name__ == "__main__":
    main()
