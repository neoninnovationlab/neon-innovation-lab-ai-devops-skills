# Agensi.io Listing Manifests (Ready to Submit)

Below are the exact listing manifests for publishing on [Agensi.io](https://www.agensi.io). Each listing is structured to deliver immediate standalone value to developers while complying 100% with marketplace standards.

---

## Listing 1: Cloud Cost-Optimization Auditor

* **Title:** Cloud Cost-Optimization Auditor (AWS & GCP)
* **Category:** DevOps & Infrastructure
* **Target Agents:** Claude Code, Cursor, Codex CLI, Gemini CLI, GitHub Copilot
* **Short Tagline:** Static IaC smell auditor that catches unattached EBS waste, unexpiring CloudWatch logs, and public IP leaks before deploy.
* **Price:** Free / Community Edition
* **Description:**
```markdown
Stop burning cloud budget on misconfigured Terraform declarations.

Cloud Cost-Optimization Auditor equips your AI coding agent to act as a FinOps engineer. It scans `.tf`, CloudFormation, Pulumi, and Docker Compose files to identify common architectural spend leaks without needing AWS account credentials.

### What it checks:
- **EBS gp2 to gp3:** Instant 20% cost reduction by converting legacy EBS types to gp3.
- **Unexpiring CloudWatch Logs:** Detects log groups with missing retention policies that silently accumulate indefinite storage charges.
- **S3 Glacier Transitions:** Flags backup and archive buckets missing lifecycle transition rules.
- **Public IPv4 Waste:** Identifies unneeded public IP auto-assignment on instances and subnets ($0.005/hr charge).
- **Non-Prod RDS Over-Provisioning:** Flags Multi-AZ and provisioned IOPS on dev/staging databases.

### Install in 30 Seconds:
Copy `SKILL.md` into your agent's skill directory or invoke directly:
```bash
python3 scripts/tf-cost-scanner.py path/to/terraform/
```
```

---

## Listing 2: Postgres Migration & Lock Safety Auditor

* **Title:** Postgres Migration & Deadlock Auditor
* **Category:** Backend & Databases
* **Target Agents:** Claude Code, Cursor, Codex CLI, Gemini CLI, GitHub Copilot
* **Short Tagline:** Zero-downtime DDL safety scanner for Prisma, Drizzle, Alembic, and raw SQL migrations.
* **Price:** Free / Community Edition
* **Description:**
```markdown
Never lock your production database during a deployment again.

Postgres Migration & Lock Safety Auditor analyzes pending migration files for dangerous DDL operations that take ACCESS EXCLUSIVE table locks or trigger deadlock conditions under concurrent traffic.

### What it checks:
- **Blocking Index Creation:** Flags `CREATE INDEX` without `CONCURRENTLY` that blocks table writes.
- **Table-Rewriting Column Additions:** Flags `ADD COLUMN` with volatile defaults that rewrite entire tables under lock.
- **Unindexed Foreign Keys:** Identifies foreign key constraints lacking indexes on the referencing table, preventing catastrophic full-table lock cascades.
- **Unbounded Row Locking:** Flags `SELECT FOR UPDATE` queries lacking `LIMIT` and `SKIP LOCKED`.

### Install in 30 Seconds:
```bash
python3 scripts/lock-analyzer.py path/to/migrations/
```
```

---

## Listing 3: OWASP Top 10 & API Penetration Reviewer

* **Title:** OWASP Top 10 & API Security Reviewer
* **Category:** Security & Code Review
* **Target Agents:** Claude Code, Cursor, Codex CLI, Gemini CLI, GitHub Copilot
* **Short Tagline:** Adversarial code reviewer for Next.js App Router, FastAPI, and Express with concrete exploit paths.
* **Price:** Free / Community Edition
* **Description:**
```markdown
Turn your AI coding agent into an adversarial penetration tester.

Instead of lecturing with generic OWASP definitions, this skill enforces concrete, framework-specific vulnerability checks with working remediation patches.

### What it checks:
- **Next.js 14/15 Server Actions Auth:** Detects exported server action functions missing session or user authentication checks.
- **Client-Side Secret Exposure:** Flags `NEXT_PUBLIC_` env variables attempting to store sensitive keys or database URLs.
- **Raw SQL Injection:** Identifies unparameterized template literal queries (`$queryRawUnsafe`).
- **SSRF & Open Redirects:** Detects unvalidated user URLs passed into `fetch()` or `redirect()`.
- **CORS Misconfiguration:** Flags wildcard origins coupled with `credentials: true`.

### Install in 30 Seconds:
```bash
python3 scripts/security-scanner.py path/to/app/
```
```
