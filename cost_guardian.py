#!/usr/bin/env python3
"""Cloud Cost Guardian: mock cloud cost and exposure scanner."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


MOCK_DATA_FILE = Path("mock_cloud_infrastructure.json")
MARKDOWN_REPORT_FILE = Path("cloud_cost_report.md")
JSON_SUMMARY_FILE = Path("cloud_cost_summary.json")

HOURS_PER_MONTH = 730
RATES = {
    "ebs_gp3_gb_month": 0.08,
    "ebs_io2_gb_month": 0.125,
    "ebs_standard_gb_month": 0.05,
    "rds_db_t3_micro_hour": 0.017,
    "rds_db_t3_small_hour": 0.034,
    "rds_db_m6g_large_hour": 0.153,
    "ec2_t3_micro_hour": 0.0104,
    "ec2_t3_medium_hour": 0.0416,
    "ec2_m6i_large_hour": 0.096,
}


@dataclass(frozen=True)
class Finding:
    severity: str
    category: str
    resource_id: str
    provider: str
    region: str
    monthly_waste_usd: float
    recommendation: str
    detail: str


def money(value: float) -> str:
    return f"${value:,.2f}"


def generate_mock_dataset() -> dict[str, Any]:
    """Return a realistic multi-cloud-ish dataset focused on AWS/Azure cost patterns."""
    generated_at = datetime.now(UTC).isoformat(timespec="seconds")
    return {
        "metadata": {
            "generated_at": generated_at,
            "organization": "ExampleCorp",
            "environment": "mock-corporate-estate",
            "currency": "USD",
        },
        "ec2_instances": [
            {
                "id": "i-0a12webprod01",
                "provider": "aws",
                "name": "web-prod-01",
                "region": "us-east-1",
                "instance_type": "t3.medium",
                "state": "running",
                "avg_cpu_14d": 37.8,
                "public_ip": True,
                "security_groups": [
                    {"port": 443, "source": "0.0.0.0/0"},
                    {"port": 22, "source": "203.0.113.0/24"},
                ],
                "owner": "platform",
            },
            {
                "id": "i-0b45admin01",
                "provider": "aws",
                "name": "admin-jumpbox",
                "region": "us-east-1",
                "instance_type": "t3.micro",
                "state": "running",
                "avg_cpu_14d": 3.2,
                "public_ip": True,
                "security_groups": [
                    {"port": 22, "source": "0.0.0.0/0"},
                    {"port": 3389, "source": "0.0.0.0/0"},
                ],
                "owner": "it-ops",
            },
            {
                "id": "vm-az-dev-analytics-01",
                "provider": "azure",
                "name": "dev-analytics-worker",
                "region": "eastus",
                "instance_type": "t3.medium",
                "state": "running",
                "avg_cpu_14d": 1.4,
                "public_ip": False,
                "security_groups": [{"port": 8080, "source": "10.20.0.0/16"}],
                "owner": "data",
            },
            {
                "id": "i-0c78batch01",
                "provider": "aws",
                "name": "nightly-batch-01",
                "region": "eu-west-2",
                "instance_type": "m6i.large",
                "state": "stopped",
                "avg_cpu_14d": 0.0,
                "public_ip": False,
                "security_groups": [],
                "owner": "finance-eng",
            },
        ],
        "ebs_volumes": [
            {
                "id": "vol-0aa111",
                "provider": "aws",
                "name": "web-prod-root",
                "region": "us-east-1",
                "type": "gp3",
                "size_gb": 120,
                "attached_to": "i-0a12webprod01",
                "encrypted": True,
                "last_snapshot_days": 7,
                "owner": "platform",
            },
            {
                "id": "vol-0bb222",
                "provider": "aws",
                "name": "legacy-build-cache",
                "region": "us-east-1",
                "type": "gp3",
                "size_gb": 950,
                "attached_to": None,
                "encrypted": False,
                "last_snapshot_days": 124,
                "owner": "unknown",
            },
            {
                "id": "vol-0cc333",
                "provider": "aws",
                "name": "old-prod-db-migration",
                "region": "eu-west-2",
                "type": "io2",
                "size_gb": 2048,
                "attached_to": None,
                "encrypted": True,
                "last_snapshot_days": 45,
                "owner": "database",
            },
            {
                "id": "disk-az-4477",
                "provider": "azure",
                "name": "orphaned-managed-disk",
                "region": "eastus",
                "type": "standard",
                "size_gb": 512,
                "attached_to": None,
                "encrypted": True,
                "last_snapshot_days": 92,
                "owner": "data",
            },
        ],
        "rds_databases": [
            {
                "id": "db-prod-orders",
                "provider": "aws",
                "engine": "postgres",
                "region": "us-east-1",
                "instance_class": "db.m6g.large",
                "status": "available",
                "avg_cpu_14d": 29.4,
                "connections_14d_avg": 52,
                "publicly_accessible": False,
                "storage_gb": 500,
                "owner": "commerce",
            },
            {
                "id": "db-old-crm",
                "provider": "aws",
                "engine": "mysql",
                "region": "us-east-1",
                "instance_class": "db.t3.small",
                "status": "available",
                "avg_cpu_14d": 0.7,
                "connections_14d_avg": 0,
                "publicly_accessible": True,
                "storage_gb": 100,
                "owner": "sales-ops",
            },
            {
                "id": "sql-az-test-ledger",
                "provider": "azure",
                "engine": "sqlserver",
                "region": "eastus",
                "instance_class": "db.t3.micro",
                "status": "available",
                "avg_cpu_14d": 1.1,
                "connections_14d_avg": 1,
                "publicly_accessible": False,
                "storage_gb": 50,
                "owner": "finance-eng",
            },
        ],
    }


def write_dataset(dataset: dict[str, Any], path: Path = MOCK_DATA_FILE) -> None:
    path.write_text(json.dumps(dataset, indent=2), encoding="utf-8")


def volume_rate(volume_type: str) -> float:
    return RATES.get(f"ebs_{volume_type}_gb_month", RATES["ebs_gp3_gb_month"])


def instance_rate(instance_type: str) -> float:
    normalized = instance_type.replace(".", "_")
    return RATES.get(f"ec2_{normalized}_hour", RATES["ec2_t3_medium_hour"])


def database_rate(instance_class: str) -> float:
    normalized = instance_class.replace("db.", "db_").replace(".", "_")
    return RATES.get(f"rds_{normalized}_hour", RATES["rds_db_t3_small_hour"])


def analyze(dataset: dict[str, Any]) -> dict[str, Any]:
    findings: list[Finding] = []

    for volume in dataset["ebs_volumes"]:
        if volume["attached_to"] is None:
            waste = volume["size_gb"] * volume_rate(volume["type"])
            findings.append(
                Finding(
                    severity="high" if waste >= 100 else "medium",
                    category="orphaned_storage",
                    resource_id=volume["id"],
                    provider=volume["provider"],
                    region=volume["region"],
                    monthly_waste_usd=waste,
                    recommendation="Snapshot if retention is required, then delete the unattached volume.",
                    detail=f"{volume['size_gb']} GB {volume['type']} volume is unattached.",
                )
            )
        if not volume["encrypted"]:
            findings.append(
                Finding(
                    severity="medium",
                    category="security_exposure",
                    resource_id=volume["id"],
                    provider=volume["provider"],
                    region=volume["region"],
                    monthly_waste_usd=0.0,
                    recommendation="Encrypt replacement storage and restrict reuse of the unencrypted asset.",
                    detail="Volume is not encrypted at rest.",
                )
            )

    for database in dataset["rds_databases"]:
        is_idle = database["avg_cpu_14d"] < 2.0 and database["connections_14d_avg"] <= 1
        if database["status"] == "available" and is_idle:
            waste = database_rate(database["instance_class"]) * HOURS_PER_MONTH
            findings.append(
                Finding(
                    severity="high" if database["publicly_accessible"] else "medium",
                    category="idle_database",
                    resource_id=database["id"],
                    provider=database["provider"],
                    region=database["region"],
                    monthly_waste_usd=waste,
                    recommendation="Confirm ownership, take final backup, then stop, downsize, or decommission.",
                    detail=(
                        f"{database['instance_class']} averages {database['avg_cpu_14d']}% CPU "
                        f"and {database['connections_14d_avg']} connections."
                    ),
                )
            )
        if database["publicly_accessible"]:
            findings.append(
                Finding(
                    severity="critical",
                    category="security_exposure",
                    resource_id=database["id"],
                    provider=database["provider"],
                    region=database["region"],
                    monthly_waste_usd=0.0,
                    recommendation="Remove public accessibility and require private network access.",
                    detail="Database is publicly accessible.",
                )
            )

    for instance in dataset["ec2_instances"]:
        if instance["state"] == "running" and instance["avg_cpu_14d"] < 5.0:
            waste = instance_rate(instance["instance_type"]) * HOURS_PER_MONTH * 0.5
            findings.append(
                Finding(
                    severity="medium",
                    category="underutilized_compute",
                    resource_id=instance["id"],
                    provider=instance["provider"],
                    region=instance["region"],
                    monthly_waste_usd=waste,
                    recommendation="Rightsize, schedule off-hours shutdown, or migrate workload to shared capacity.",
                    detail=f"{instance['instance_type']} averages {instance['avg_cpu_14d']}% CPU over 14 days.",
                )
            )

        open_admin_ports = [
            rule["port"]
            for rule in instance["security_groups"]
            if rule["source"] == "0.0.0.0/0" and rule["port"] in {22, 3389}
        ]
        if instance["public_ip"] and open_admin_ports:
            findings.append(
                Finding(
                    severity="critical",
                    category="security_exposure",
                    resource_id=instance["id"],
                    provider=instance["provider"],
                    region=instance["region"],
                    monthly_waste_usd=0.0,
                    recommendation="Restrict admin ingress to VPN, SSO broker, or approved office CIDR ranges.",
                    detail=f"Public instance exposes admin port(s): {', '.join(map(str, open_admin_ports))}.",
                )
            )

    findings_payload = [finding.__dict__ for finding in findings]
    total_waste = sum(item["monthly_waste_usd"] for item in findings_payload)
    security_exposures = [item for item in findings_payload if item["category"] == "security_exposure"]

    return {
        "generated_at": dataset["metadata"]["generated_at"],
        "organization": dataset["metadata"]["organization"],
        "currency": dataset["metadata"]["currency"],
        "asset_counts": {
            "ec2_instances": len(dataset["ec2_instances"]),
            "ebs_volumes": len(dataset["ebs_volumes"]),
            "rds_databases": len(dataset["rds_databases"]),
        },
        "estimated_monthly_waste_usd": round(total_waste, 2),
        "estimated_annual_waste_usd": round(total_waste * 12, 2),
        "security_exposure_count": len(security_exposures),
        "finding_count": len(findings_payload),
        "findings": sorted(
            findings_payload,
            key=lambda item: (
                {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(item["severity"], 9),
                -item["monthly_waste_usd"],
            ),
        ),
    }


def render_markdown(summary: dict[str, Any]) -> str:
    rows = "\n".join(
        "| {severity} | {category} | `{resource_id}` | {provider} | {region} | {waste} | {recommendation} |".format(
            severity=item["severity"].upper(),
            category=item["category"].replace("_", " "),
            resource_id=item["resource_id"],
            provider=item["provider"],
            region=item["region"],
            waste=money(item["monthly_waste_usd"]),
            recommendation=item["recommendation"],
        )
        for item in summary["findings"]
    )

    details = "\n".join(
        f"- **{item['severity'].upper()}** `{item['resource_id']}`: {item['detail']}"
        for item in summary["findings"]
    )

    return f"""# Cloud Cost Governance Scanner Report

Generated: {summary["generated_at"]}  
Organization: {summary["organization"]}  
Currency: {summary["currency"]}

## Executive Summary

- Estimated monthly waste: **{money(summary["estimated_monthly_waste_usd"])}**
- Estimated annualized waste: **{money(summary["estimated_annual_waste_usd"])}**
- Findings: **{summary["finding_count"]}**
- Public or configuration security exposures: **{summary["security_exposure_count"]}**

## Asset Coverage

| Asset Type | Count |
| --- | ---: |
| EC2 / compute instances | {summary["asset_counts"]["ec2_instances"]} |
| EBS / storage volumes | {summary["asset_counts"]["ebs_volumes"]} |
| RDS / managed databases | {summary["asset_counts"]["rds_databases"]} |

## Prioritized Findings

| Severity | Category | Resource | Provider | Region | Monthly Waste | Recommended Action |
| --- | --- | --- | --- | --- | ---: | --- |
{rows}

## Technical Notes

{details}

## Next Actions

1. Validate ownership for every high and critical finding.
2. Snapshot and delete unattached storage after retention approval.
3. Stop, downsize, or retire idle databases and compute resources.
4. Remove public admin ingress and public database exposure before cost cleanup work.
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate mock cloud infrastructure data and scan it for cost and security governance issues."
    )
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Output a technician-ready markdown report or a raw JSON summary.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    dataset = generate_mock_dataset()
    write_dataset(dataset)
    summary = analyze(dataset)

    if args.format == "json":
        JSON_SUMMARY_FILE.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(json.dumps(summary, indent=2))
        print(f"\nWrote dataset to {MOCK_DATA_FILE} and JSON summary to {JSON_SUMMARY_FILE}")
        return

    report = render_markdown(summary)
    MARKDOWN_REPORT_FILE.write_text(report, encoding="utf-8")
    print(report)
    print(f"\nWrote dataset to {MOCK_DATA_FILE} and markdown report to {MARKDOWN_REPORT_FILE}")


if __name__ == "__main__":
    main()
