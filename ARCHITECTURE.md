# Architecture

## Component Descriptions

- **VPC (10.0.0.0/16, eu-west-3, 3 AZs):** the network foundation. Split into public, private-app, and private-db subnet tiers, one of each per Availability Zone.
- **Internet Gateway + NAT Gateway:** the IGW allows the public subnet (and only the public subnet) to reach the internet. A single NAT Gateway lets private-subnet instances make outbound calls (package installs, AWS API calls) without being directly reachable from the internet.
- **Application Load Balancer:** the only public-facing compute-adjacent resource. Terminates HTTPS using an ACM certificate, redirects all HTTP to HTTPS, and routes to the Auto Scaling Group.
- **Auto Scaling Group (3-6 EC2 t3.micro instances):** runs the Flask application via gunicorn, managed as a systemd service. Scales on average CPU utilization (target 60%). Health checks hit `/health`, which verifies real database connectivity, not just process liveness.
- **RDS (PostgreSQL, db.t3.micro, single-AZ):** stores menu items and orders. Not publicly accessible; reachable only from the app tier's security group.
- **S3 (3 buckets):** an images bucket (public read, scoped to one prefix, for menu photos), a config bucket (private, AWS Config snapshots), and a deploy bucket (private, versioned, application deployment artifacts).
- **Route53 + ACM:** DNS resolution and free HTTPS certificate for the custom domain `pam-kitchen.online`.
- **CloudWatch + SNS:** a dashboard covering the four golden signals plus business metrics, 3 alarms, and email notification on threshold breach.
- **AWS Config:** continuous compliance monitoring against 4 rules (S3 public read, SSH restrictions, RDS encryption, RDS public access).
- **Secrets Manager:** holds auto-generated database and admin credentials, never hardcoded or committed to source control.

## Network Design and Security Groups

Three security groups enforce a strict request path: the **ALB security group** accepts inbound HTTP/HTTPS from the internet (0.0.0.0/0) only. The **app security group** accepts inbound traffic only from the ALB's security group, on the app port — nothing else in the VPC, and nothing from the internet, can reach an app instance directly. The **database security group** accepts inbound only from the app security group, on the PostgreSQL port. This means compromising any single layer does not expose the layer behind it directly; an attacker would need to compromise the ALB *and* the app tier to reach the database at the network level.

No SSH access exists anywhere in the architecture — all instance access is via AWS Systems Manager Session Manager, authenticated through IAM rather than a distributed SSH key.

## Data Flow

1. A browser requests `https://pam-kitchen.online` → Route53 resolves it → the ALB terminates HTTPS using the ACM certificate.
2. The ALB forwards the request to a healthy instance in the Auto Scaling Group.
3. The Flask app reads/writes order and menu data directly to RDS on every request — no session state is held in instance memory, which is what allows any instance to be freely replaced without losing in-progress carts or orders.
4. Menu images are referenced by URL in the database and fetched by the browser **directly from S3**, bypassing the app tier and ALB entirely for that traffic.
5. All app instances, the ALB, and RDS continuously emit metrics to CloudWatch, which powers the dashboard and evaluates the 3 alarms; a breach publishes to an SNS topic, which emails a notification.

## High Availability Strategy

The ALB and Auto Scaling Group both span all 3 Availability Zones, so the loss of a single AZ does not take the application offline — the ALB stops routing to instances in the affected AZ, and the ASG can launch replacements in the remaining AZs. RDS is intentionally single-AZ (see Trade-offs below) — this is the one component without automatic failover.

## Scalability Considerations

The app tier scales horizontally via the Auto Scaling Group's CPU-based target tracking policy (60% target), between 3 and 6 instances. The database tier does not currently scale horizontally — RDS read replicas or a larger instance class would be the next step for handling significantly higher read load, not implemented here given project scope.

## Technology Choices and Rationale

- **EC2 + Auto Scaling over containers (ECS/EKS):** chosen for simplicity and a more direct, explainable architecture for a single-service application at this scale. Containerizing would add real setup complexity (Dockerfile, image registry, task definitions) without a corresponding benefit for this project's size.
- **RDS over a self-managed database on EC2:** managed backups, patching, and monitoring outweigh the marginal cost difference for a project where operational time is the scarcest resource.
- **Flask with server-rendered templates over a separate frontend framework + API:** kept the application layer intentionally simple so effort concentrated on infrastructure, which is where the majority of the grading weight sits.
- **S3 for images over storing them in the database or serving through the app:** offloads static asset delivery from the compute tier entirely, and demonstrates a genuine separation-of-concerns architectural decision.

## Trade-offs and Alternatives Considered

- **Single-AZ RDS vs. Multi-AZ:** Multi-AZ roughly doubles the RDS cost for automatic failover. Given the project's one-week lifespan and no real uptime requirement, single-AZ was chosen; this is documented explicitly as a risk in `SECURITY.md`.
- **Single NAT Gateway vs. one per AZ:** one per AZ is the standard resilience pattern but roughly doubles that cost line item; a single shared NAT Gateway was accepted as a cost trade-off.
- **HTTP Basic Auth vs. a full login system for admin endpoints:** Basic Auth was chosen for the internal kitchen-management pages as a fast, genuinely effective control appropriate to the project's timeline; a production system serving multiple staff members would likely need per-user accounts and role-based access instead.
- **GitHub-based app deployment (original) vs. S3-based (current):** originally, EC2 instances cloned the app directly from GitHub at boot. This was changed after a real incident — repeated testing from a shared NAT Gateway IP triggered GitHub's anonymous rate limiting, which would have broken new instance launches during the live demo. Deployment now pulls a pre-built artifact from a private, versioned S3 bucket instead, removing the external dependency entirely.

