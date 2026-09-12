---
name: cloud-cost-auditor
description: Audits Terraform, Pulumi, CloudFormation, and Docker Compose files for common AWS/GCP cost leaks. Use when a user asks to review infrastructure-as-code for cost savings, wasteful config, or before merging a Terraform PR. Runs entirely as a static source scan by default; can optionally invoke read-only AWS CLI calls if the user approves a live scan.
---

# Cloud Cost-Optimization Auditor

## Scope and honesty rule

This skill finds two different kinds of things, and it must never blur them:

1. **Static config smells** — patterns visible directly in the IaC source that reliably correlate with wasted spend. These can be flagged with full confidence from the files alone.
2. **Live-state waste** — things like "this EBS volume is actually unattached right now" or "this instance is idle." These CANNOT be determined from `.tf`/`.yaml` source. Terraform/CloudFormation declare *desired* config, not runtime usage. Never claim to detect these from static files. Only check them if the user explicitly opts into a live scan with read-only credentials.

If a check requires runtime/billing data the skill does not have, say so plainly instead of guessing.

## Static checks (zero credentials, safe to run in any CI or IDE)

Scan `*.tf`, `*.tf.json`, Pulumi (`*.ts`/`*.py` resource declarations), CloudFormation (`*.yaml`/`*.json` templates), and `docker-compose.yml`.

- **EBS type**: `aws_ebs_volume` or root/EBS blocks declared with `type = "gp2"` → flag, recommend `gp3` (same durability, ~20% cheaper baseline, higher default IOPS/throughput at no extra cost). Show the one-line diff.
- **CloudWatch log retention**: `aws_cloudwatch_log_group` with no `retention_in_days` → flag. Default is "Never Expire," which silently accumulates indefinite storage cost. Recommend an explicit value (e.g. 30/90/400 days depending on compliance needs).
- **S3 lifecycle**: `aws_s3_bucket` (or `aws_s3_bucket_lifecycle_configuration` absent for a bucket used for logs/backups/artifacts) → flag missing lifecycle rules for transition to Glacier/Glacier Deep Archive or expiration.
- **Public IP sprawl**: `associate_public_ip_address = true` on instances/subnets used at scale, or many `aws_eip` resources → flag; each associated public IPv4 now carries an hourly charge. Suggest NAT Gateway or VPC endpoints where the public IP isn't actually required for inbound access.
- **NAT Gateway vs VPC endpoints**: multiple NAT Gateways with traffic patterns implying S3/DynamoDB/ECR access → flag and suggest Gateway/Interface VPC Endpoints, which remove per-GB NAT processing charges for that traffic.
- **RDS non-prod over-provisioning**: `multi_az = true`, `storage_type = "io1"/"io2"`, or explicit `provisioned_iops` on resources whose naming/tags/environment variable indicate `dev`/`staging`/`test` → flag as likely unnecessary for non-prod.
- **Unpinned/oversized defaults**: instance types on placeholder/example values left unchanged from scaffolding (e.g. `m5.4xlarge` in a dev module) → flag for review, not auto-fix.

Each finding must include: file + line, the exact snippet, why it costs money, and a concrete patch (the corrected line(s)), not just a description.

## Optional live-account mode

Before running anything against a real AWS account, ask explicitly:

> "Want me to also run a live, read-only scan against your AWS account for idle/unattached resources? This requires AWS CLI configured with read-only credentials and will run:
> `aws ec2 describe-volumes --filters Name=status,Values=available`
> `aws ec2 describe-addresses --filters Name=association-id,Values=null`
> No resources will be modified."

Only run these (or GCP/Azure equivalents) after explicit yes. Never run mutating commands. Report findings the same way — resource ID, monthly cost estimate if derivable from public pricing, and the exact command to delete/release it (for the user to run themselves — this skill does not delete infrastructure).

## Output format

1. Summary table: check name, count of findings, estimated static-savings tier (low/med/high — do not fabricate precise dollar figures without a live pricing lookup).
2. Per-finding detail with file/line/snippet/patch.
3. If live mode wasn't run, one line noting which categories of savings require it.
