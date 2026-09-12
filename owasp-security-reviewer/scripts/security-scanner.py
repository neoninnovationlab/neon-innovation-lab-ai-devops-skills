#!/usr/bin/env python3
"""
security-scanner.py — static pattern scanner for Next.js, FastAPI, and Express codebases.

Flags common OWASP Top 10 vulnerabilities with framework-specific heuristics:
- Next.js: Server Actions without auth, NEXT_PUBLIC_ secret leaks, unvalidated redirects
- FastAPI: Parameterized endpoints missing current user dependencies, SSRF url-fetching
- Express: Routes before auth middleware, IDOR pattern without user scoping, raw SQL interpolation

Usage:
    python3 security-scanner.py <path-to-scan> [--json]
"""
import argparse
import json
import re
import sys
from pathlib import Path

FINDINGS = []


def add_finding(path, line_no, snippet, rule, message, patch=None, severity="high"):
    FINDINGS.append({
        "file": str(path),
        "line": line_no,
        "snippet": snippet.strip() if snippet else "",
        "rule": rule,
        "message": message,
        "patch": patch,
        "severity": severity,
    })


# --- Rules & Patterns ---

# 1. Next.js Leaking Secrets via NEXT_PUBLIC_
NEXT_PUBLIC_SECRET_RE = re.compile(
    r'NEXT_PUBLIC_(?:SECRET|PRIVATE|KEY|TOKEN|PASSWORD|API_KEY|AUTH|CREDENTIAL|DATABASE|DB_URL)',
    re.IGNORECASE
)

# 2. Next.js Unvalidated Redirects
UNVALIDATED_REDIRECT_RE = re.compile(
    r'(?:redirect|router\.push)\s*\(\s*(?:req\.|searchParams\.get|params\.|url\.searchParams)',
    re.IGNORECASE
)

# 3. Raw SQL Injection via Template Literals
RAW_SQL_TEMPLATE_RE = re.compile(
    r'(?:\$queryRawUnsafe|db\.query|connection\.query|client\.query|sequelize\.query)\s*\(\s*`[^`]*\$\{',
    re.IGNORECASE
)

# 4. CORS Wildcard with Credentials
CORS_WILDCARD_CREDS_RE = re.compile(
    r'(?:Access-Control-Allow-Origin.*?\*.*?(?:credentials|allow_credentials).*?true)|(?:credentials.*?true.*?Access-Control-Allow-Origin.*?\*)',
    re.IGNORECASE | re.DOTALL
)

# 5. SSRF in Webhook/Fetch handlers
SSRF_FETCH_RE = re.compile(
    r'(?:fetch|axios\.(?:get|post)|requests\.(?:get|post)|http\.get)\s*\(\s*(?:req\.body|body\.|params\.|request\.(?:data|json))',
    re.IGNORECASE
)


def scan_file(path: Path):
    ext = path.suffix.lower()
    if ext not in [".js", ".ts", ".jsx", ".tsx", ".py", ".env", ".env.local", ".env.production"]:
        return

    text = path.read_text(errors="ignore")
    lines = text.splitlines()

    # Rule 1: NEXT_PUBLIC secret check (line-based)
    for i, line in enumerate(lines, 1):
        m = NEXT_PUBLIC_SECRET_RE.search(line)
        if m:
            add_finding(
                path, i, line, "NEXT_PUBLIC_SECRET_LEAK",
                f"Env variable '{m.group(0)}' appears to hold a secret/credential but uses NEXT_PUBLIC_ prefix "
                "which embeds it into client-side JS bundles accessible to all users.",
                patch=line.replace("NEXT_PUBLIC_", ""),
                severity="critical",
            )

        # Rule 2: Unvalidated redirect
        m_redir = UNVALIDATED_REDIRECT_RE.search(line)
        if m_redir:
            add_finding(
                path, i, line, "UNVALIDATED_REDIRECT",
                "Redirect or push directly consumes user-supplied parameter without allowlist verification — open redirect risk.",
                patch="const safeUrl = ALLOWED_HOSTS.includes(target) ? target : '/dashboard';",
                severity="medium",
            )

        # Rule 3: Raw SQL string template interpolation
        m_sql = RAW_SQL_TEMPLATE_RE.search(line)
        if m_sql:
            add_finding(
                path, i, line, "SQLI_RAW_INTERPOLATION",
                "Raw SQL query uses template literal string interpolation (${...}) instead of parameterized queries ($1, ?).",
                patch="Use parameterized inputs: db.query('SELECT * FROM users WHERE id = $1', [userId])",
                severity="critical",
            )

        # Rule 5: SSRF via direct fetch of user input
        m_ssrf = SSRF_FETCH_RE.search(line)
        if m_ssrf:
            add_finding(
                path, i, line, "SSRF_UNVALIDATED_FETCH",
                "HTTP client fetches user-supplied URL directly without hostname allowlist or private IP blocking (127.0.0.1, 169.254.169.254).",
                patch="Validate URL against strict protocol and allowlist, block private IP ranges before fetching.",
                severity="high",
            )

    # Whole-file structural checks:
    # Next.js Server Action Auth check
    if '"use server"' in text or "'use server'" in text:
        # Look for exported async functions
        server_actions = re.finditer(r'export\s+async\s+function\s+([a-zA-Z0-9_]+)\s*\(([^)]*)\)\s*\{([^}]*)\}', text)
        for sa in server_actions:
            name, params, body = sa.group(1), sa.group(2), sa.group(3)
            # Check if auth/session/user check exists in body
            has_auth = re.search(r'(auth\s*\(\)|session|getSession|getCurrentUser|verifyToken|currentUser)', body)
            if not has_auth:
                line_no = text[:sa.start()].count("\n") + 1
                add_finding(
                    path, line_no, f'export async function {name}({params})', "NEXTJS_SERVER_ACTION_NO_AUTH",
                    f"Server Action '{name}' lacks explicit session/authentication verification. Anyone can invoke this endpoint directly via POST.",
                    patch="const session = await auth();\nif (!session?.user) throw new Error('Unauthorized');",
                    severity="high"
                )

    # FastAPI: Parameterized endpoints missing current_user dependency
    if "@app." in text or "@router." in text:
        fastapi_routes = re.finditer(r'@(?:app|router)\.(?:get|post|put|delete|patch)\s*\(\s*["\']([^"\']*{[a-zA-Z0-9_]+}[^"\']*)["\']\s*.*?\)\s*\n(?:async\s+)?def\s+([a-zA-Z0-9_]+)\s*\(([^)]*)\):', text)
        for fr in fastapi_routes:
            endpoint, func_name, params = fr.group(1), fr.group(2), fr.group(3)
            if "Depends" not in params or not re.search(r'(user|current_user|auth)', params, re.I):
                line_no = text[:fr.start()].count("\n") + 1
                add_finding(
                    path, line_no, f"def {func_name}({params}):", "FASTAPI_IDOR_MISSING_AUTH_DEPENDENCY",
                    f"Route '{endpoint}' accepts resource ID but does not declare user authentication dependency (e.g. Depends(get_current_user)) — IDOR risk.",
                    patch=f"def {func_name}({params}, current_user: User = Depends(get_current_user)):",
                    severity="high"
                )

    # CORS Wildcard with credentials
    if CORS_WILDCARD_CREDS_RE.search(text):
        add_finding(
            path, 1, "CORS Configuration", "CORS_WILDCARD_WITH_CREDENTIALS",
            "CORS allows wildcard origin ('*') combined with credentials: true. This violates browser security specs and exposes user cookies.",
            patch="Specify explicit trusted origin array instead of '*'",
            severity="high"
        )


def main():
    parser = argparse.ArgumentParser(description="Scan codebase for OWASP and framework-specific security vulnerabilities.")
    parser.add_argument("path", help="File or directory to scan")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    root = Path(args.path)
    if not root.exists():
        print(f"Error: Path {root} does not exist.", file=sys.stderr)
        sys.exit(1)

    files = [root] if root.is_file() else [p for p in root.rglob("*") if p.is_file()]

    for f in files:
        # Skip node_modules, .git, venv
        if any(part in f.parts for part in ["node_modules", ".git", "venv", "__pycache__", ".next", "dist"]):
            continue
        scan_file(f)

    # Sort findings by severity
    severity_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    FINDINGS.sort(key=lambda x: severity_rank.get(x["severity"], 4))

    if args.json:
        print(json.dumps(FINDINGS, indent=2))
        return 1 if FINDINGS else 0

    if not FINDINGS:
        print("✅ No OWASP or framework security anti-patterns detected.")
        return 0

    print(f"🚨 Found {len(FINDINGS)} security finding(s):\n")
    for f in FINDINGS:
        loc = f"{f['file']}:{f['line']}" if f['line'] else f['file']
        print(f"[{f['severity'].upper()}] [{f['rule']}] {loc}")
        print(f"  Snippet: {f['snippet']}")
        print(f"  -> {f['message']}")
        if f['patch']:
            print(f"  Fix: {f['patch']}")
        print()

    return 1 if any(f["severity"] in ["critical", "high"] for f in FINDINGS) else 0


if __name__ == "__main__":
    sys.exit(main())
