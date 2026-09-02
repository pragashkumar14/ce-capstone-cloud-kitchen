# Runbook

## How to Deploy Infrastructure

One-time backend bootstrap (only needed once per AWS account):

```bash
BUCKET_NAME="ce-capstone-cloud-kitchen-tfstate-$(openssl rand -hex 3)"
REGION="eu-west-3"
aws s3api create-bucket --bucket "$BUCKET_NAME" --region "$REGION" --create-bucket-configuration LocationConstraint="$REGION"
aws s3api put-bucket-versioning --bucket "$BUCKET_NAME" --versioning-configuration Status=Enabled
aws s3api put-public-access-block --bucket "$BUCKET_NAME" --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
aws dynamodb create-table --table-name ce-capstone-tflock --attribute-definitions AttributeName=LockID,AttributeType=S --key-schema AttributeName=LockID,KeyType=HASH --billing-mode PAY_PER_REQUEST --region "$REGION"
```

Update the bucket name in `terraform/backend.tf` to match, then:

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

After the first apply, the printed `route53_nameservers` output must be added at the domain registrar (Namecheap) as custom nameservers, and DNS propagation allowed to complete before ACM certificate validation succeeds.

## How to Update the Application

Push a change to `app/src/**` on `main` — GitHub Actions (`deploy-app.yml`) automatically zips the app and uploads it to the S3 deployment bucket. New instances launched after that point pull the latest version automatically. Currently-running instances do **not** auto-update — cycle them manually to pick up a new deploy:

```bash
aws autoscaling describe-auto-scaling-instances --region eu-west-3 --query "AutoScalingInstances[].InstanceId" --output text
# for each instance ID:
aws autoscaling terminate-instance-in-auto-scaling-group --instance-id <id> --no-should-decrement-desired-capacity --region eu-west-3
```

## How to Monitor System Health

- **CloudWatch dashboard** `Pam-Kitchen-Dashboard` — golden signals (traffic, latency, errors, saturation) plus business metrics (orders placed, revenue).
- **Alarms** — 3 configured (5xx errors, high latency, high CPU), notifying via SNS email.
- **Target health:**
```bash
aws elbv2 describe-target-health --target-group-arn <arn> --region eu-west-3
```

## Common Troubleshooting Scenarios

- **New instance stuck `unhealthy`:** SSM into it (`aws ssm start-session --target <id>`) and check `sudo journalctl -u cloudkitchen -n 50` for an application error, or `sudo cat /var/log/cloud-init-output.log` for a boot-time failure (e.g. failed S3 download or dependency install).
- **`/kitchen` returns 401:** expected — these endpoints require HTTP Basic Auth. Credentials are in Secrets Manager under `admin_username`/`admin_password`.
- **Site returns 502:** the ALB has no healthy targets. Check target health (above) and instance logs.

## Incident Response Procedures

See the full 6-step Incident Response Plan in `SECURITY.md` (Isolate → Investigate → Contain → Notify → Remediate → Post-mortem).

## Backup and Recovery Procedures

RDS automated backups run with a 1-day retention window (documented cost trade-off — see `COSTS.md`). The S3 deployment bucket has versioning enabled, allowing rollback to a previous application artifact if a bad deploy needs reverting. Terraform state itself is versioned in its S3 backend, providing a recovery path if state is ever corrupted.

## Scaling Procedures

Scaling is automatic via the Auto Scaling Group's target-tracking policy (60% average CPU), between 3 and 6 instances — no manual action needed under normal load. To manually adjust capacity:

```bash
aws autoscaling update-auto-scaling-group --auto-scaling-group-name <name> --desired-capacity <n> --region eu-west-3
```

