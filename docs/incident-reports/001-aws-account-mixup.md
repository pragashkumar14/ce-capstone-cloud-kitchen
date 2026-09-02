# Incident Report 001: Infrastructure Deployed to Wrong AWS Account

**Date:** August 31, 2026
**Severity:** High (no data loss, but full infrastructure had to be rebuilt)
**Status:** Resolved

## Summary

An environment variable (`AWS_PROFILE=miguel`), left set in a terminal session from an earlier, unrelated lab exercise, silently redirected all Terraform commands to a classmate's AWS account instead of the project owner's own account. Approximately the first several hours of infrastructure work (VPC, compute, database, DNS records) were built in the wrong account without any error or warning — the AWS Console simply appeared empty when checked, because the wrong account was being viewed.

## Timeline

- Backend bootstrap and initial `terraform apply` completed successfully, appearing to work correctly.
- Multiple checks of the AWS Console (S3, Route53, EC2) showed no resources, despite `terraform apply` reporting success — root cause not yet identified at this point.
- `aws sts get-caller-identity` run directly, revealing the active AWS account ID did not match the project owner's own account.
- Traced to a leftover `export AWS_PROFILE=miguel` command in shell history from an earlier lab session, whose effect had persisted across the terminal session.

## Root Cause

A shell environment variable does not reset between commands within the same terminal session, and had been set during unrelated coursework earlier in the same session. No verification step existed at the time to confirm the active AWS identity before running infrastructure commands.

## Resolution

1. Confirmed the correct scope of the problem via `terraform state list` (30+ resources) and `terraform destroy` against the wrong account, using its credentials one final time specifically to clean up.
2. Verified via a follow-up `terraform state list` that the wrong account was left completely clean.
3. `unset AWS_PROFILE` and confirmed the correct account via `aws sts get-caller-identity`.
4. Rebuilt the entire backend (new S3 bucket, DynamoDB table) and re-ran `terraform apply` under the correct account. No Terraform code changes were required — the issue was entirely about which credentials were active, not the infrastructure code itself.
5. Notified the classmate whose account was affected, and rotated a CI/CD access key that had also been inadvertently created in the wrong account during this window.

## Follow-up Actions

- Adopted a standing habit of running `aws sts get-caller-identity --query Account --output text` before any `terraform apply` or destructive command, especially after switching terminal sessions.
- No permanent shell profile changes were needed, since the variable was never set in `~/.bashrc` — it was purely a session-level leftover, confirmed via `grep` against startup files during the investigation.

