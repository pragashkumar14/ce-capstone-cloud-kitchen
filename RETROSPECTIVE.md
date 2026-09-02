# Retrospective

## What Went Well

The core architecture decisions held up throughout the project — the stateless app tier writing directly to RDS meant that cycling instances (which happened dozens of times during development) never once lost cart or order data. The modular Terraform structure (separate modules for networking, compute, database, monitoring, storage, and config) made it genuinely easy to add new pieces later — AWS Config and the S3 deployment bucket were both added cleanly to an already-working stack without touching unrelated code. The security testing phase (Prowler, Trivy) surfaced real, actionable findings rather than noise, and every fix applied was verified live against the running infrastructure, not just assumed from the Terraform diff.

## Challenges Faced

- **An AWS account mix-up.** Partway through Phase 1, an `AWS_PROFILE` environment variable left over from an earlier lab exercise silently redirected all infrastructure to a classmate's AWS account instead of my own, without any error or warning — the console simply looked empty because I was checking the wrong account entirely.
- **A GitHub rate-limiting incident.** Heavy iterative testing meant repeatedly cycling EC2 instances, each cloning the app from GitHub at boot. All of that traffic shared one NAT Gateway IP, which GitHub's abuse detection eventually flagged, blocking anonymous clones and breaking new instance launches.
- **Several subtle Terraform and Python bugs** introduced by manual text edits — missing return statements, duplicated resource blocks, and off-by-one line insertions that silently broke working code.
- **An unauthenticated internal admin area** discovered only after building the full kitchen management flow — `/kitchen` had no access control for a significant stretch of development.

## How Challenges Were Overcome

The account mix-up was resolved by tracing the actual AWS account ID through `aws sts get-caller-identity`, confirming the environment variable was the cause, cleanly destroying everything built in the wrong account, and rebuilding from scratch under the correct one — the Terraform code itself needed zero changes, only the credentials pointing at it. The GitHub rate-limit issue was diagnosed by directly testing an anonymous clone from inside a failing instance and from a fresh local shell to isolate GitHub itself (not the repo configuration) as the cause, then fixed by migrating application deployment to a private, versioned S3 bucket with an automated GitHub Actions upload pipeline — removing the external dependency entirely rather than just waiting for the rate limit to clear. Code bugs were caught by adopting a stricter verification habit: compiling and doing a full file read-through after every edit, rather than trusting a partial diff. The missing authentication was fixed by adding HTTP Basic Auth backed by Secrets Manager credentials, reusing the existing IAM permission pattern rather than provisioning a new secret.

## Technical Skills Learned

- Practical, hands-on experience with Terraform module design and the dependency graph Terraform builds automatically across modules.
- Real incident diagnosis under time pressure — tracing a failure from a symptom (unhealthy instances) back to a root cause (shared NAT IP rate-limiting) using logs, direct testing, and process of elimination rather than guessing.
- AWS security tooling in practice, not just theory — running Prowler and Trivy, interpreting real findings, and triaging them into genuine fixes versus documented, deliberate trade-offs.
- The operational reality of "stateless" architecture — understanding *why* it matters by watching instances get destroyed and replaced repeatedly with zero data loss, rather than just being told it's a best practice.

## Key Takeaways

Infrastructure automation doesn't remove the need for careful verification — it makes mistakes propagate faster if you skip it. The habit of checking `aws sts get-caller-identity` before any destructive action, and re-reading a full file after every edit rather than trusting a diff, caught real problems before they became worse. Security testing is most valuable when findings are actually triaged and acted on, not just run once and filed away — the difference between a checklist exercise and a real security posture is whether anything changes as a result.

## What Would Be Done Differently

Environment isolation would be set up more deliberately from the start — a dedicated terminal profile or explicit account confirmation step before any `terraform apply`, rather than discovering an account mix-up after infrastructure was already partially built. Deployment would be S3-based from day one rather than GitHub-based, avoiding the rate-limit incident entirely instead of hitting it and then fixing it. Authentication on internal-only routes would be designed in from the first version of those routes, rather than retrofitted after the fact.

## Future Improvements Planned

Beyond the capstone's scope: Multi-AZ RDS with automated failover, a customer-managed KMS key for encryption instead of AWS-managed defaults, Secrets Manager automatic rotation, a WAF layer in front of the ALB, and role-based access for kitchen staff instead of a single shared admin credential.

