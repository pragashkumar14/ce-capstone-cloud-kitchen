# Security

## Threat Model (STRIDE)

### Spoofing
**Threat:** An attacker impersonates a legitimate customer, or forges requests to kitchen management endpoints.
**Mitigations:** HTTPS (ACM certificate) prevents man-in-the-middle spoofing of the domain. AWS IAM roles (no long-lived credentials on instances) prevent credential spoofing for AWS API access. Kitchen management endpoints (`/kitchen`, `/kitchen/all`, `/kitchen/complete`) require HTTP Basic Auth with credentials stored in Secrets Manager.

### Tampering
**Threat:** SQL injection, or tampering with order data in transit.
**Mitigations:** All database queries use parameterized statements (`psycopg2` `%s` placeholders), not string concatenation — verified manually against the checkout form. HTTPS encrypts all traffic in transit. RDS is not publicly reachable, blocking direct database tampering.

### Repudiation
**Threat:** No record of who changed an order's status, or dispute over whether an order was placed.
**Mitigations:** Every order has a `created_at` timestamp. Application logs (gunicorn/systemd journal) capture request activity. AWS CloudTrail logs all infrastructure-level API calls by default. Kitchen actions now require authentication, so a specific credential (not "anyone") is tied to any status change.

### Information Disclosure
**Threat:** Database credentials leaking, or overly broad public access to stored data.
**Mitigations:** Database and admin credentials are auto-generated and stored in AWS Secrets Manager, never hardcoded; the app's IAM role can only read that one specific secret. RDS is not publicly accessible. The S3 images bucket has public read access scoped *only* to the `images/` prefix (verified via AWS Config and Prowler scan) — a deliberate, documented exception, not an oversight. The deployment artifacts bucket is fully private. A privacy policy discloses what customer data is collected and why.

### Denial of Service
**Threat:** Traffic flood overwhelming the app or database.
**Mitigations:** The Auto Scaling Group adds instances automatically when average CPU exceeds 60%. The ALB distributes load across 3 Availability Zones. CloudWatch alarms alert when saturation or error thresholds are crossed.
**Known trade-off:** No WAF or dedicated DDoS protection layer (AWS Shield Standard is on by default at no cost, but no WAF was added) — a deliberate cost/scope decision for a one-week academic demo, not appropriate for a real production deployment facing genuine attack traffic.

### Elevation of Privilege
**Threat:** A compromised app instance being used to gain broader access to the AWS account.
**Mitigations:** The app instance's IAM role is scoped to only what it needs (read specific secrets, publish CloudWatch metrics, read from the deploy bucket) — verified via Prowler/Trivy scans showing no overly broad permissions. IMDSv2 is required on all instances (verified live via AWS CLI), which blocks a common SSRF technique for stealing instance credentials. No SSH access exists anywhere (SSM Session Manager only), reducing the attack surface for credential theft entirely. Security groups are least-privilege: the app tier is only reachable from the ALB, and RDS is only reachable from the app tier.

## Risk Matrix (Likelihood × Impact)

| # | Risk | Likelihood | Impact | Overall Risk | Status |
|---|------|-----------|--------|---------------|--------|
| 1 | RDS is single-instance, 1-day backup retention, no read replica | Low | Medium | Medium | Documented cost/scope trade-off |
| 2 | No WAF / DDoS protection layer | Low | Medium | Medium | Documented cost/scope trade-off |
| 3 | S3 images bucket has public read on `images/` prefix | Low | Low | Low | Deliberate, scoped, documented |
| 4 | Secrets Manager rotation not enabled | Low | Low | Low | Documented cost/scope trade-off |
| 5 | GitHub was used as an initial code source (now resolved) | N/A | N/A | Resolved | Migrated to S3-based deployment after diagnosing a real rate-limiting incident during testing |

