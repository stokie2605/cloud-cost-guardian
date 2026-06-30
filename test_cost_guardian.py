import os
from unittest.mock import MagicMock, patch
import pytest

from cost_guardian import (
    WasteFinding,
    get_region,
    findings_from_unattached_ebs_volumes,
    findings_from_idle_elastic_ips,
    build_findings,
    build_summary,
    fetch_live_data,
)

def test_get_region_default():
    with patch.dict(os.environ, {}, clear=True):
        assert get_region() == "eu-west-2"

def test_get_region_env():
    with patch.dict(os.environ, {"AWS_REGION": "us-east-1"}):
        assert get_region() == "us-east-1"

def test_findings_from_unattached_ebs_volumes():
    sample_volumes = [
        {
            "VolumeId": "vol-12345",
            "Size": 100,
            "AvailabilityZone": "eu-west-2a",
            "VolumeType": "gp3"
        }
    ]
    findings = findings_from_unattached_ebs_volumes(sample_volumes, "eu-west-2")
    assert len(findings) == 1
    assert findings[0].resource_type == "ebs_volume"
    assert findings[0].resource_id == "vol-12345"
    assert findings[0].estimated_monthly_waste_usd == 10.0

def test_findings_from_idle_elastic_ips():
    sample_addresses = [
        {
            "AllocationId": "eipalloc-123",
            "PublicIp": "1.2.3.4",
            "AssociationId": "assoc-123"  # Associated -> should be ignored
        },
        {
            "AllocationId": "eipalloc-456",
            "PublicIp": "5.6.7.8"  # Idle -> should be flagged
        }
    ]
    findings = findings_from_idle_elastic_ips(sample_addresses, "eu-west-2")
    assert len(findings) == 1
    assert findings[0].resource_type == "elastic_ip"
    assert findings[0].resource_id == "eipalloc-456"
    assert findings[0].estimated_monthly_waste_usd == 4.0

def test_build_summary():
    findings = [
        WasteFinding("ebs_volume", "vol-1", "eu-west-2", 10.0, "reason"),
        WasteFinding("elastic_ip", "eip-1", "eu-west-2", 4.0, "reason")
    ]
    summary = build_summary("eu-west-2", findings, "live")
    assert summary["summary"]["unattached_ebs_volume_count"] == 1
    assert summary["summary"]["idle_elastic_ip_count"] == 1
    assert summary["summary"]["finding_count"] == 2
    assert summary["summary"]["estimated_monthly_waste_usd"] == 14.0
    assert summary["summary"]["estimated_annual_waste_usd"] == 168.0

@patch("cost_guardian.create_ec2_client")
def test_fetch_live_data(mock_create_client):
    mock_client = MagicMock()
    mock_create_client.return_value = mock_client
    
    # Mock paginator for describe_volumes
    mock_paginator = MagicMock()
    mock_client.get_paginator.return_value = mock_paginator
    mock_paginator.paginate.return_value = [
        {"Volumes": [{"VolumeId": "vol-1"}]}
    ]
    
    # Mock describe_addresses
    mock_client.describe_addresses.return_value = {
        "Addresses": [{"PublicIp": "1.2.3.4"}]
    }
    
    data = fetch_live_data("eu-west-2")
    assert "Volumes" in data
    assert "Addresses" in data
    assert len(data["Volumes"]) == 1
    assert len(data["Addresses"]) == 1
    assert data["Volumes"][0]["VolumeId"] == "vol-1"
    assert data["Addresses"][0]["PublicIp"] == "1.2.3.4"
