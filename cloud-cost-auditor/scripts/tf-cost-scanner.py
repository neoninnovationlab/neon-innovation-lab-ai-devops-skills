#!/usr/bin/env python3
"""
tf-cost-scanner.py — static cost-smell scanner for Terraform (.tf) files.

Scope: this is a *static source* scanner. It flags config patterns that
reliably correlate with wasted cloud spend. It CANNOT tell you whether a
resource is actually idle/unattached right now — that requires querying
the live cloud API (see --live-hint output for the commands to run).

Usage:
    python3 tf-cost-scanner.py <path-to-scan> [--json]
"""
import argparse
import json
import re
import sys
from pathlib import Path

FINDINGS = []


def add_finding(path, line_no, snippet, rule, message, patch=None):
    FINDINGS.append({
        "file": str(path),
        "line": line_no,
        "snippet": snippet.strip(),
        "rule": rule,
        "message": message,
        "patch": patch,
    })


def scan_gp2(path, lines):
    for i, line in enumerate(lines, 1):
        if re.search(r'type\s*=\s*"gp2"', line):
            add_finding(
                path, i, line, "EBS_GP2",
                "gp2 volume declared — gp3 offers same durability with "
                "~20% lower baseline cost and better default IOPS/throughput.",
                patch=line.replace("gp2", "gp3"),
            )


def scan_cloudwatch_retention(path, text, lines):
    for m in re.finditer(r'resource\s+"aws_cloudwatch_log_group"\s+"([^"]+)"\s*{([^}]*)}', text, re.S):
        block = m.group(2)
        if "retention_in_days" not in block:
            line_no = text[:m.start()].count("\n") + 1
            add_finding(
                path, line_no, m.group(0)[:80] + "...", "CW_NO_RETENTION",
                f'aws_cloudwatch_log_group "{m.group(1)}" has no retention_in_days '
                "— defaults to Never Expire, accumulating indefinite storage cost.",
                patch='  retention_in_days = 90  # add inside the resource block',
            )


def scan_s3_lifecycle(path, text):
    bucket_names = set(re.findall(r'resource\s+"aws_s3_bucket"\s+"([^"]+)"', text))
    lifecycle_targets = set(re.findall(r'resource\s+"aws_s3_bucket_lifecycle_configuration"\s+"[^"]+"\s*{[^}]*bucket\s*=\s*aws_s3_bucket\.([^.\s]+)', text, re.S))
    for name in bucket_names:
        if name not in lifecycle_targets:
            add_finding(
                path, None, f'resource "aws_s3_bucket" "{name}"', "S3_NO_LIFECYCLE",
                f'Bucket "{name}" has no matching aws_s3_bucket_lifecycle_configuration '
                "— consider transitioning cold data to Glacier or expiring it.",
            )


def scan_public_ip(path, lines):
    for i, line in enumerate(lines, 1):
        if re.search(r'associate_public_ip_address\s*=\s*true', line):
            add_finding(
                path, i, line, "PUBLIC_IP",
                "Public IP association charges accrue hourly per address — "
                "confirm inbound public access is actually required here.",
            )


def scan_rds_nonprod(path, text):
    for m in re.finditer(r'resource\s+"aws_db_instance"\s+"([^"]+)"\s*{([^}]*)}', text, re.S):
        name, block = m.group(1), m.group(2)
        is_nonprod = re.search(r'(dev|staging|test|sandbox)', name, re.I) or \
                     re.search(r'(dev|staging|test|sandbox)', block, re.I)
        if not is_nonprod:
            continue
        line_no = text[:m.start()].count("\n") + 1
        if re.search(r'multi_az\s*=\s*true', block):
            add_finding(path, line_no, f'aws_db_instance "{name}"', "RDS_MULTIAZ_NONPROD",
                        "multi_az = true on a resource that looks non-prod — doubles RDS cost.")
        if re.search(r'storage_type\s*=\s*"io[12]"', block):
            add_finding(path, line_no, f'aws_db_instance "{name}"', "RDS_PROVISIONED_IOPS_NONPROD",
                        "Provisioned IOPS storage on a non-prod-looking DB instance — gp3 is usually sufficient.")


CHECKS = [scan_gp2, scan_public_ip]  # line-based
BLOCK_CHECKS = [scan_cloudwatch_retention, scan_s3_lifecycle, scan_rds_nonprod]  # whole-file regex


def scan_file(path: Path):
    text = path.read_text(errors="ignore")
    lines = text.splitlines()
    for check in CHECKS:
        check(path, lines)
    for check in BLOCK_CHECKS:
        check(path, text) if check is not scan_cloudwatch_retention else check(path, text, lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="File or directory to scan")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    root = Path(args.path)
    tf_files = [root] if root.is_file() else list(root.rglob("*.tf"))

    for f in tf_files:
        scan_file(f)

    if args.json:
        print(json.dumps(FINDINGS, indent=2))
        return

    if not FINDINGS:
        print("No static cost smells found in scanned .tf files.")
    else:
        print(f"Found {len(FINDINGS)} static cost finding(s):\n")
        for f in FINDINGS:
            loc = f"{f['file']}:{f['line']}" if f['line'] else f['file']
            print(f"[{f['rule']}] {loc}")
            print(f"  {f['snippet']}")
            print(f"  -> {f['message']}")
            if f['patch']:
                print(f"  patch: {f['patch']}")
            print()

    print("--- Not checked (requires live AWS API access) ---")
    print("Unattached EBS volumes:  aws ec2 describe-volumes --filters Name=status,Values=available")
    print("Unassociated Elastic IPs: aws ec2 describe-addresses --filters Name=association-id,Values=null")


if __name__ == "__main__":
    sys.exit(main())
