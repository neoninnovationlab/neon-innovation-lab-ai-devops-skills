# Enterprise AI Agent Skills: Cloud Cost, Postgres Lock Safety & OWASP Reviewer

> **Production-grade `SKILL.md` rule engines and zero-dependency static analyzers for Claude Code, Cursor, GitHub Copilot, and Gemini CLI.**

[![Compatible with Claude Code](https://img.shields.io/badge/Claude%20Code-Compatible-6366f1?style=flat-square)](https://claude.ai/code)
[![Compatible with Cursor](https://img.shields.io/badge/Cursor%20IDE-Compatible-000000?style=flat-square)](https://cursor.com)
[![Compatible with GitHub Copilot](https://img.shields.io/badge/Copilot-Compatible-22c55e?style=flat-square)](https://github.com/features/copilot)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-blue.svg?style=flat-square)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)

---

## Why This Exists

Most AI coding assistants write code that looks clean on the surface but can quietly take down production or leak cloud spend:
- An AI will generate `CREATE INDEX` on an active PostgreSQL table, holding an `ACCESS EXCLUSIVE` lock that blocks all live writes until the build finishes.
- An AI will declare `type = "gp2"` in Terraform, silently leaving 20% baseline storage savings and higher baseline IOPS on the table compared to `gp3`.
- An AI will export a `"use server"` function in Next.js without checking `auth()`, inadvertently creating a publicly accessible unauthenticated POST endpoint.

This repository provides **3 specialized, framework-hardened `SKILL.md` packages** and matching **zero-dependency Python CLI scanners** that turn your AI agent into a Senior DBA, DevOps FinOps Engineer, and AppSec Reviewer.

---

## ⚡ Quickstart (Run in 10 Seconds)

Clone the repository and run the test suite to see the scanners in action:

```bash
git clone https://github.com/neoninnovationlab/neon-innovation-lab-ai-devops-skills.git
cd neon-innovation-lab-ai-devops-skills

# Run all verification tests across test fixtures
./scripts/run-all-tests.sh
```

---

## 🛠️ The 3 Specialized Skills

### 1. Cloud Cost-Optimization Auditor (`cloud-cost-auditor`)
* **Target:** Terraform (`.tf`), OpenTofu, CloudFormation, and Docker Compose.
* **Scope & Honesty Invariant:** Distinguishes declarative HCL smells from runtime state. Never claims to detect unattached volumes without asking to run read-only AWS CLI queries first.
* **What it catches:**
  - **Legacy gp2 Volumes:** Flags `gp2` declarations and provides one-line diffs to `gp3` (instant ~20% savings + higher baseline throughput).
  - **CloudWatch Indefinite Retention:** Detects `aws_cloudwatch_log_group` missing `retention_in_days` (default is "Never Expire", which silently builds permanent monthly storage charges).
  - **S3 Cold Tiering:** Identifies archive/backup buckets missing `aws_s3_bucket_lifecycle_configuration` transitions to Glacier.
  - **Public IPv4 Allocation:** Flags `associate_public_ip_address = true` on subnets/instances ($0.005/hr per IPv4).
  - **Non-Prod RDS Waste:** Identifies Multi-AZ and provisioned IOPS (`io1`/`io2`) on dev/staging databases.

```bash
# Run static scan on your infrastructure directory
python3 cloud-cost-auditor/scripts/tf-cost-scanner.py path/to/terraform/
```

---

### 2. Postgres Migration & Lock Safety Auditor (`postgres-migration-auditor`)
* **Target:** Raw SQL migrations, Prisma `migration.sql`, Drizzle, TypeORM, and Alembic (`versions/*.py`).
* **Focus:** Zero-downtime database deployments and lock-escalation prevention.
* **What it catches:**
  - **Blocking Index Builds:** Catches `CREATE INDEX` without `CONCURRENTLY` which halts write traffic.
  - **Table-Rewriting Column Additions:** Flags `ADD COLUMN ... NOT NULL DEFAULT <expression>` with volatile defaults that rewrite tables under lock.
  - **Unindexed Foreign Keys:** Flags `FOREIGN KEY` constraints where the child table lacks an index, preventing full-table scan locks during parent deletions.
  - **Unbounded Row Locking:** Flags `SELECT FOR UPDATE` queries lacking `LIMIT` and `SKIP LOCKED`.

```bash
# Run static lock scan on pending migration files
python3 postgres-migration-auditor/scripts/lock-analyzer.py path/to/migrations/
```

---

### 3. OWASP Top 10 & API Security Reviewer (`owasp-security-reviewer`)
* **Target:** Next.js 14/15 App Router, FastAPI, and Express.js applications.
* **Focus:** Adversarial code audits with concrete exploit paths and code replacements.
* **What it catches:**
  - **Next.js Server Actions Auth:** Catches exported `"use server"` functions missing explicit session/user authorization checks.
  - **Client-Side Secret Leaks:** Catches sensitive credentials prefixed with `NEXT_PUBLIC_` bundled into browser JavaScript.
  - **Raw SQL Injection:** Identifies unparameterized string template interpolations (`$queryRawUnsafe`, ``db.query(`...${val}`)``).
  - **SSRF & Open Redirects:** Detects user-controlled URLs fed into `fetch()` or `redirect()` without domain allowlists.

```bash
# Run security scan on application routes
python3 owasp-security-reviewer/scripts/security-scanner.py path/to/app/
```

---

## 📦 How to Install in Your AI Coding Agent

### For Claude Code
Copy the `SKILL.md` file from any skill folder into your agent's skills directory:
```bash
cp cloud-cost-auditor/SKILL.md ~/.claude/skills/cloud-cost-auditor.md
```

### For Cursor IDE / Windsurf
Add the contents of the `SKILL.md` to your `.cursorrules` or save it as `.cursor/rules/devops-guard.mdc`.

### For Gemini CLI / Antigravity
Link the skill directory into your active agent plugins directory.

---

## 🏢 Community Edition vs. Enterprise Pro Bundle

This repository contains the **Community Edition** (open-source under MIT), designed for individual developers to run manual terminal audits.

For engineering teams looking to automate these checks across their CI/CD pipelines, we offer the **Enterprise Pro Bundle**:

| Feature | Community Edition (Free) | Enterprise Pro Bundle ($69) |
| :--- | :---: | :---: |
| **All 3 Core `SKILL.md` Engines** | ✅ | ✅ |
| **Zero-Dependency Python Scanners** | ✅ | ✅ |
| **Local Test Fixture Suite** | ✅ | ✅ |
| **GitHub Actions CI/CD Workflows (`.github/workflows/`)** | ❌ | **Included (Cost, DB, & Security Guards)** |
| **Pre-Commit Git Hooks (`.pre-commit-config.yaml`)** | ❌ | **Included (Blocks bad commits locally)** |
| **Automated PR Bot Review Comments** | ❌ | **Included** |
| **Commercial Team License (Unlimited Seats)** | ❌ | **Included** |
| **Quarterly AWS & Postgres 17+ Rule Updates** | ❌ | **Included** |

### 👉 [Get the Enterprise Pro Bundle on Gumroad ($69)](https://gumroad.com)
*Instant ZIP download • 1-click PayPal & Credit Card Checkout • Multi-Seat Commercial License*

---

## 🧪 Testing & Verification

We practice what we preach. Every scanner in this repository is tested against paired positive (wasteful/vulnerable) and negative (clean/secure) fixtures:

```bash
./scripts/run-all-tests.sh
```

Output:
```
==================================================
🧪 AI SKILLS MARKETPLACE: SENIOR QA/QC TEST SUITE
==================================================
1️⃣  Testing Cloud Cost Auditor (tf-cost-scanner.py)...
   ✅ PASS: Correctly detected all 5 waste patterns.
   ✅ PASS: Clean fixture reported 0 smells.

2️⃣  Testing Postgres Migration Auditor (lock-analyzer.py)...
   ✅ PASS: Correctly detected all 5 lock hazards.
   ✅ PASS: Safe migration reported 0 lock risks.

3️⃣  Testing OWASP Security Reviewer (security-scanner.py)...
   ✅ PASS: Correctly detected 6 vulnerabilities and exited with status 1.
   ✅ PASS: Secure app reported 0 vulnerabilities and exited with status 0.

==================================================
🎉 ALL 6 QA/QC SUITE TESTS PASSED WITH 100% PRECISION!
==================================================
```

---

## 📄 License

The Community Edition is licensed under the [MIT License](LICENSE).  
The Enterprise Pro Bundle is distributed under the Commercial Team License.
