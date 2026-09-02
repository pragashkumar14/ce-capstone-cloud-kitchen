# ADR 004: HTTP Basic Auth for Kitchen Management Endpoints

**Status:** Accepted

**Context:** The `/kitchen`, `/kitchen/all`, and `/kitchen/complete` endpoints were initially built with no authentication at all — discovered as a real gap during security review.

**Decision:** Protect these endpoints with HTTP Basic Auth, credentials auto-generated and stored in Secrets Manager (reusing the existing database secret's IAM permission rather than creating a new one).

**Consequences:** Fast, genuinely effective for a single-admin use case within the project's timeline. A production system serving multiple kitchen staff would need per-user accounts and role-based access instead of one shared credential — noted as a future improvement in RETROSPECTIVE.md.

