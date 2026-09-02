# Cost Analysis

## Monthly Cost Estimate (if run continuously, eu-west-3)

| Service | Resource | Est. Monthly Cost |
|---------|----------|-------------------|
| EC2 | 3 × t3.micro (Auto Scaling Group) | ~$29 |
| NAT Gateway | 1 gateway + data processing | ~$32 |
| Application Load Balancer | 1 ALB, low request volume | ~$18 |
| RDS | 1 × db.t3.micro, 20GB storage, single-AZ | ~$15 |
| Route53 | 1 hosted zone | $0.50 |
| Secrets Manager | 1 secret (DB + admin credentials) | $0.40 |
| AWS Config | Recorder + 4 rules, low resource count | ~$2 |
| CloudWatch | 1 dashboard, 3 alarms, custom metrics | ~$0.30 |
| S3 | Images + config + deploy buckets, low storage/transfer | ~$0.50 |
| SNS | Low message volume | ~$0.10 |
| **Total (if run 24/7 for a month)** | | **~$98/month** |

## Actual Cost for This Project

The infrastructure was run for approximately one week (development, testing, and demo), not a full month. Prorated: **~$98 ÷ 30 × 7 ≈ $23** for the AWS infrastructure over the project period.

**Domain registration (one-time, already paid):** `pam-kitchen.online` via Namecheap — **$1.18 total**, auto-renew disabled since the domain is not needed beyond the demo period.

**Total project cost: approximately $24.**

## Cost Allocation

All resources are tagged via Terraform's `default_tags` block (`Project`, `Environment`, `ManagedBy`), applied automatically to every resource created — no manual tagging required, and no resource can be created without these tags since they're set at the provider level.

## Cost Optimization Strategies Applied

1. **Single NAT Gateway** instead of one per AZ — the standard production pattern is one NAT Gateway per AZ for resilience, but that would roughly double this line item (~$32 → ~$64/month) for redundancy not needed in a one-week academic demo.
2. **Single-AZ RDS**, not Multi-AZ — Multi-AZ roughly doubles RDS cost for automatic failover, which isn't justified for a project with no real uptime SLA.
3. **t3.micro instances throughout** — smallest burstable instance type sufficient for demo-level traffic, rather than provisioning for peak capacity that will never be reached outside the live demo window.
4. **Auto-renew disabled on the domain** — avoids an unnecessary recurring charge for a domain that serves no purpose after submission.
5. **1-day RDS backup retention** instead of the default longer window — reduces backup storage cost; acceptable since this isn't production data requiring long-term recovery guarantees.

## Cost / Performance Trade-offs

- **NAT Gateway is the single largest line item** (~33% of total monthly cost) despite being pure infrastructure overhead with no direct performance benefit to the user — it exists purely so private-subnet instances can reach the internet for package installs and AWS API calls. A NAT instance (a small EC2 acting as a NAT) would be cheaper but less reliable and adds operational overhead; the managed NAT Gateway was chosen for reliability over marginal cost savings.
- **Auto Scaling Group sized at 3–6 instances** balances demo cost against the ability to visibly scale up under real load during the presentation — fewer minimum instances would reduce cost but weaken the live scaling demo; more would increase baseline cost without added value.
- **No Reserved Instances or Savings Plans** — these require a 1-year+ commitment to pay off, making them inappropriate for infrastructure intended to run for roughly one week and then be torn down.

## Budget Alerts

Not configured for this project — a known, deliberate gap given the short, bounded project timeline and close manual monitoring throughout development. A production deployment would configure AWS Budgets with a defined monthly threshold and SNS notification, reusing the same SNS topic already built for operational alerts.

