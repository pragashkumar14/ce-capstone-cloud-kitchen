# ADR 002: Single-AZ RDS

**Status:** Accepted

**Context:** RDS supports Multi-AZ deployment for automatic failover, at roughly double the cost.

**Decision:** Deploy RDS single-AZ.

**Consequences:** Lower cost, appropriate for a project with a bounded, short lifespan and no real uptime SLA. Documented explicitly as an accepted risk in SECURITY.md's risk matrix — a production deployment serving real customers would need Multi-AZ.

