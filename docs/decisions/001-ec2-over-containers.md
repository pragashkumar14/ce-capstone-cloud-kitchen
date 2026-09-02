# ADR 001: EC2 + Auto Scaling over Containers

**Status:** Accepted

**Context:** The project's advanced requirements list Container Orchestration (ECS/EKS) as one optional pick among several.

**Decision:** Run the application directly on EC2 instances via an Auto Scaling Group, not containers.

**Consequences:** Simpler to build, explain, and demo within a one-week timeline — no Dockerfile, image registry, or task definitions to manage. The trade-off is that a genuinely production-scale system with multiple services would benefit more from container orchestration; for a single-service app at this scale, the added complexity wasn't justified.

