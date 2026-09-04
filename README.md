# Pam Kitchen — Cloud Ordering Platform

A multi-cuisine cloud kitchen food ordering platform. Pickup only, pay on collection. Built as a Week 9 solo capstone for the Ironhack Cloud Engineering bootcamp, demonstrating a production-style AWS architecture provisioned entirely via Terraform, with CI/CD, observability, and security practices applied throughout.

**Live site:** https://pam-kitchen.online

## Architecture Overview

A stateless Flask application runs on an Auto Scaling Group of EC2 instances behind an Application Load Balancer, spread across 3 Availability Zones. All order and menu data lives in RDS (PostgreSQL); nothing is held in instance memory, so any instance can be replaced without data loss. Menu photos are served directly from S3 to the browser, bypassing the app tier entirely. HTTPS is provided via Route53 + ACM on a custom domain. Full observability (CloudWatch dashboard, alarms, SNS notifications) and security tooling (AWS Config, Prowler, Trivy) are built in.

See `ARCHITECTURE.md` for the full breakdown of components, data flow, and design rationale.

## Prerequisites

- AWS account with credentials configured (`aws configure`)
- Terraform >= 1.5.0
- Python 3.10+ (for local app development only — deployed instances provision their own environment)
- An S3 bucket + DynamoDB table for Terraform remote state (see backend bootstrap commands in `RUNBOOK.md`)

## Deployment Guide

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

Full step-by-step deployment, including the one-time backend bootstrap, is documented in `RUNBOOK.md`.

## Testing Instructions

- **Application:** `python3 -m py_compile app/src/app.py` for a syntax check; manual end-to-end testing covered the full order flow (menu → cart → checkout → confirmation → kitchen view → order completion).
- **Infrastructure:** `terraform validate` and `terraform plan` before every apply. GitHub Actions runs `terraform-plan.yml` and `tests.yml` automatically on every pull request.
- **Security:** Prowler (CIS AWS benchmark), Trivy (IaC + dependency scanning), and manual verification. Full results in `SECURITY.md`.

## Cost Summary

Approximately $24 total for the project (~$23 in AWS infrastructure over roughly one week, plus a $1.18 domain registration). Full breakdown, including monthly-run estimates and cost optimization decisions, is in `COSTS.md`.

## Project Structure

- **terraform/** — Infrastructure as code (networking, compute, database, monitoring, storage, config modules)
- **app/src/** — Flask application source
- **.github/workflows/** — CI/CD pipelines (Terraform validation, tests, automated app deployment)
- **docs/** — Architecture diagrams and decision records
- **presentation/** — Demo script and slides


## Contact / Attribution

Pragash Kumaravel — Ironhack Cloud Engineering Capstone, September 2026.

# Branch protection test
