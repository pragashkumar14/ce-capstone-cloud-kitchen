# Incident Report 002: GitHub Rate-Limiting Broke New Instance Launches

**Date:** September 1-2, 2026
**Severity:** Medium (caught during development, would have been High if it occurred during the live demo)
**Status:** Resolved

## Summary

New EC2 instances launched by the Auto Scaling Group began failing health checks. Investigation showed the instance's boot script (`user_data`) was failing to clone the application from GitHub — GitHub was demanding authentication on what should have been an anonymous, public repository clone.

## Timeline

- Multiple new instances launched (as part of routine testing/redeployment) all showed `unhealthy` status shortly after boot.
- SSM into an affected instance showed no `cloudkitchen.service` had ever been created — the boot script had failed before that point.
- `cloud-init-output.log` on the instance showed: `fatal: could not read Username for 'https://github.com': No such device or address`.
- Confirmed via the GitHub API that the repository was still genuinely public (`"private": false`), ruling out a repo configuration change.
- Reproduced the exact same failure from a fresh `git clone` run directly inside an EC2 instance, and separately confirmed the repository cloned successfully from a different network origin — isolating the cause to the shared NAT Gateway's public IP being rate-limited or challenged by GitHub after repeated anonymous clone requests during testing.

## Root Cause

All EC2 instances in the private subnets share a single NAT Gateway, and therefore a single public IP, for all outbound internet traffic. Extensive iterative testing throughout development involved repeatedly cycling instances, each performing a fresh anonymous `git clone` from that same shared IP. GitHub's abuse-detection systems flagged the resulting request pattern and began requiring authentication instead of permitting the anonymous clone.

## Resolution

Rather than wait for the rate limit to clear (with no guaranteed timeline, and a real risk of recurring during the live Friday demo when new instances would launch under real audience traffic), application deployment was re-architected:

1. Created a new, private, versioned S3 bucket for deployment artifacts.
2. Added IAM permission for app instances to read from it.
3. Updated the EC2 launch template to download and unzip the application from S3 (authenticated via the instance's IAM role, not credentials) instead of cloning from GitHub.
4. Added a GitHub Actions workflow that automatically zips and uploads the application to S3 on every push to `main`, preserving an automated deployment pipeline without depending on GitHub for the actual artifact delivery.
5. Verified the fix by cycling all instances and confirming healthy status, and separately confirming the GitHub Actions workflow itself completed successfully end-to-end.

Full architectural rationale documented in `docs/decisions/003-s3-based-deployment.md`.

## Follow-up Actions

- Deployment no longer depends on GitHub's availability or rate limits at all — a genuine resilience improvement, not just a workaround.
- Noted as a "what would be done differently" item in `RETROSPECTIVE.md`: this dependency should have been recognized and avoided from the start, rather than discovered through an outage.

