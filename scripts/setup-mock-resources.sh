#!/bin/bash
set -eo pipefail

echo "Waiting for LocalStack EC2 service to be ready..."
for i in {1..30}; do
  if aws --endpoint-url=http://localstack:4566 ec2 describe-volumes >/dev/null 2>&1; then
    echo "LocalStack is ready!"
    break
  fi
  echo "Waiting... ($i/30)"
  sleep 2
done

echo "Seeding unattached EBS volumes..."
aws --endpoint-url=http://localstack:4566 ec2 create-volume \
  --size 80 \
  --availability-zone eu-west-2a \
  --tag-specifications 'ResourceType=volume,Tags=[{Key=Name,Value=OrphanedStorage}]'

aws --endpoint-url=http://localstack:4566 ec2 create-volume \
  --size 250 \
  --availability-zone eu-west-2b \
  --tag-specifications 'ResourceType=volume,Tags=[{Key=Name,Value=LegacyData}]'

echo "Seeding unassociated Elastic IPs..."
aws --endpoint-url=http://localstack:4566 ec2 allocate-address --domain vpc
aws --endpoint-url=http://localstack:4566 ec2 allocate-address --domain vpc

echo "LocalStack mock seeding completed successfully!"
