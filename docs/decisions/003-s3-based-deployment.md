# ADR 003: S3-based Application Deployment (over GitHub clone)

**Status:** Accepted (supersedes original GitHub-clone approach)

**Context:** EC2 instances originally cloned the application directly from GitHub at boot. Repeated instance cycling during development triggered GitHub's anonymous rate limiting from the shared NAT Gateway IP, breaking new instance launches. Full incident report: `docs/incident-reports/002-github-rate-limiting.md`.

**Decision:** Deploy application code via a private, versioned S3 bucket instead. GitHub Actions automatically zips and uploads the app on every push to `main`; instances pull from S3 at boot using their IAM role.

**Consequences:** Removes an external dependency and its associated rate-limit risk entirely. Slightly more setup (a new bucket, IAM policy, and GitHub Actions workflow) but more resilient and arguably more production-appropriate than pulling from a public git host at boot time.

