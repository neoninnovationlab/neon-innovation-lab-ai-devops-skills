#!/usr/bin/env python3
"""
lock-analyzer.py — static scanner for Postgres migration files.

Flags patterns that reliably cause table-level locking, deadlocks, or
production downtime when a migration runs against a live, populated
database. This is a pattern scanner, not a query planner — it does not
know your table sizes or live traffic, so severity is about lock TYPE,
not guaranteed real-world duration.

Usage:
    python3 lock-analyzer.py <path-to-scan> [--json]
"""
import argparse
import json
import re
import sys
from pathlib import Path

FINDINGS = []


def add_finding(path, line_no, snippet, rule, message, patch=None, severity="high"):
    FINDINGS.append({
        "file": str(path), "line": line_no, "snippet": snippet.strip(),
        "rule": rule, "message": message, "patch": patch, "severity": severity,
    })


NOT_NULL_DEFAULT_RE = re.compile(
    r'ALTER\s+TABLE\s+(\w+)\s+ADD\s+COLUMN\s+(\w+)\s+\S+.*?NOT\s+NULL\s+DEFAULT\s+(\S+)',
    re.IGNORECASE,
)
CREATE_INDEX_RE = re.compile(
    r'CREATE\s+(UNIQUE\s+)?INDEX\s+(?!CONCURRENTLY)(\w+)?\s*ON\s+(\w+)',
    re.IGNORECASE,
)
FK_RE = re.compile(
    r'ALTER\s+TABLE\s+(\w+)\s+ADD\s+CONSTRAINT\s+\w+\s+FOREIGN\s+KEY\s*\(([^)]+)\)\s*REFERENCES\s+(\w+)',
    re.IGNORECASE,
)
CREATE_INDEX_ANY_RE = re.compile(r'CREATE\s+(?:UNIQUE\s+)?INDEX\s+(?:CONCURRENTLY\s+)?\w+\s+ON\s+(\w+)\s*\(([^)]+)\)', re.IGNORECASE)
DROP_RE = re.compile(r'DROP\s+(TABLE|COLUMN)\s+(\w+)', re.IGNORECASE)
FOR_UPDATE_RE = re.compile(r'FOR\s+UPDATE', re.IGNORECASE)


def scan_text(path: Path, text: str):
    lines = text.splitlines()

    for i, line in enumerate(lines, 1):
        m = NOT_NULL_DEFAULT_RE.search(line)
        if m:
            table, col, default = m.groups()
            if not re.match(r'^[\'"]?[\w.]+[\'"]?$', default) or "()" in default:
                add_finding(
                    path, i, line, "NOT_NULL_VOLATILE_DEFAULT",
                    f'ADD COLUMN "{col}" NOT NULL DEFAULT {default} on "{table}" rewrites every '
                    "row under an ACCESS EXCLUSIVE lock.",
                    patch=(f"ALTER TABLE {table} ADD COLUMN {col} <type>; -- nullable first\n"
                           f"-- backfill in batches, then:\n"
                           f"ALTER TABLE {table} ADD CONSTRAINT {col}_not_null "
                           f"CHECK ({col} IS NOT NULL) NOT VALID;\n"
                           f"ALTER TABLE {table} VALIDATE CONSTRAINT {col}_not_null;"),
                )

        m = CREATE_INDEX_RE.search(line)
        if m and "CONCURRENTLY" not in line.upper():
            _, idx_name, table = m.groups()
            add_finding(
                path, i, line, "INDEX_NOT_CONCURRENT",
                f'CREATE INDEX on "{table}" without CONCURRENTLY blocks writes for the build duration.',
                patch=re.sub(r'CREATE\s+(UNIQUE\s+)?INDEX', lambda mm: mm.group(0).replace("INDEX", "INDEX CONCURRENTLY"), line, flags=re.IGNORECASE)
                      + "  -- run outside a transaction block",
            )

        m = DROP_RE.search(line)
        if m:
            kind, name = m.groups()
            add_finding(
                path, i, line, f"DROP_{kind.upper()}_LIVE",
                f'DROP {kind} "{name}" on what may be a live table — verify application code '
                "no longer reads/writes it before this ships (expand-contract pattern).",
                severity="medium",
            )

        if FOR_UPDATE_RE.search(line) and not re.search(r'LIMIT\s+\d+', line, re.IGNORECASE):
            add_finding(
                path, i, line, "FOR_UPDATE_UNBOUNDED",
                "SELECT ... FOR UPDATE without a LIMIT — risk of long lock hold / deadlock "
                "under concurrent access. Consider batching with LIMIT + SKIP LOCKED.",
                severity="medium",
            )

    # Cross-check: FK added vs whether an index exists on the referencing column(s)
    indexed_cols = set()
    for m in CREATE_INDEX_ANY_RE.finditer(text):
        table, cols = m.groups()
        for c in cols.split(","):
            indexed_cols.add((table.strip(), c.strip()))

    for m in FK_RE.finditer(text):
        table, cols, ref_table = m.groups()
        line_no = text[:m.start()].count("\n") + 1
        for c in cols.split(","):
            c = c.strip()
            if (table, c) not in indexed_cols:
                add_finding(
                    path, line_no, m.group(0), "FK_NO_INDEX",
                    f'Foreign key on {table}.{c} -> {ref_table} has no matching index — '
                    "parent-row updates/deletes will full-scan this table under load.",
                    patch=f"CREATE INDEX CONCURRENTLY idx_{table}_{c} ON {table} ({c});",
                )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    root = Path(args.path)
    files = [root] if root.is_file() else list(root.rglob("*.sql"))

    for f in files:
        scan_text(f, f.read_text(errors="ignore"))

    order = {"high": 0, "medium": 1, "low": 2}
    FINDINGS.sort(key=lambda f: order.get(f["severity"], 3))

    if args.json:
        print(json.dumps(FINDINGS, indent=2))
        return

    if not FINDINGS:
        print("No locking/deadlock risk patterns found.")
        return

    print(f"Found {len(FINDINGS)} finding(s), ordered by lock severity:\n")
    for f in FINDINGS:
        print(f"[{f['severity'].upper()}] [{f['rule']}] {f['file']}:{f['line']}")
        print(f"  {f['snippet']}")
        print(f"  -> {f['message']}")
        if f['patch']:
            print(f"  patch:\n    " + f['patch'].replace("\n", "\n    "))
        print()


if __name__ == "__main__":
    sys.exit(main())
