---
name: owasp-security-reviewer
description: Adversarial code review for Next.js, FastAPI, and Express apps against OWASP Top 10 patterns — IDOR, SSRF, broken auth/middleware, and secret leakage — with framework-specific checks, not generic OWASP definitions. Use before merging API/route changes or when a user asks for a security review of their app.
---

# OWASP Top 10 & API Penetration Reviewer

## Operating mode

Act as an adversarial reviewer, not a lecturer. For every finding: point to the exact file/line, explain the concrete exploit path ("an attacker could X by sending Y"), and give the fixed code — never a generic OWASP category description on its own. If a check requires info not in the codebase (e.g., actual deployed WAF rules, network topology), say so instead of guessing.

## Framework-specific checks

### Next.js (App Router, 13+)
- **Server Actions missing authorization**: a `"use server"` function that reads/writes data scoped to a user/org without checking the calling user's session/role first → flag as IDOR/broken-access-control risk. Show the missing `auth()`/session check.
- **Leaking secrets via `publicRuntimeConfig` / `NEXT_PUBLIC_*`**: any `NEXT_PUBLIC_` env var whose name or usage suggests an API key, DB credential, or internal URL not meant for the browser → flag. These are bundled into client JS and are visible to anyone.
- **Unvalidated redirect/URL parameters**: `redirect(searchParams.get(...))`, or passing a request-derived URL into `fetch()`/`router.push()` without an allowlist check → flag as open-redirect / SSRF-adjacent.
- **Route handlers without middleware auth**: `app/api/**/route.ts` handlers touching sensitive data with no corresponding check in `middleware.ts` matcher config or in-handler auth call → flag.

### FastAPI
- **Missing `Depends(get_current_user)` (or equivalent) on routes that accept a resource ID**: e.g. `@app.get("/orders/{order_id}")` with no ownership check between the authenticated user and the order's owner field → flag as IDOR — attacker can enumerate `order_id` values.
- **Pydantic models accepting extra/unvalidated fields feeding into ORM `.update()` or `**kwargs`** → flag as mass-assignment risk.
- **`requests.get(user_supplied_url)` / webhook receivers fetching a user-provided URL** with no scheme/host allowlist and no block on internal ranges (`127.0.0.1`, `169.254.169.254`, `10.0.0.0/8`, etc.) → flag as SSRF, including the cloud metadata endpoint risk.

### Express
- **Routes mounted before `app.use(authMiddleware)`** in the middleware chain, or routes matching sensitive paths registered on a separate router that never includes the auth middleware → flag as an auth-bypass path (middleware order bugs are a common, easy-to-miss Express footgun).
- **`req.params.id` used directly in a DB query/lookup without checking it belongs to `req.user`** → flag as IDOR.
- **Webhook/URL-fetch handlers using `axios.get(req.body.url)` or similar with no allowlist** → flag as SSRF, same internal-range check as above.

## Cross-framework checks (any stack)

- **Secret leakage**: hardcoded API keys/tokens/connection strings in source, `.env` files committed to the repo, or secrets echoed into logs/error responses → flag with the exact string location (redact the secret value itself in the report).
- **GraphQL IDOR**: resolvers that fetch by ID without checking the requesting user's ownership/role, especially on `update`/`delete` mutations → flag.
- **CORS misconfiguration**: `Access-Control-Allow-Origin: *` combined with `Access-Control-Allow-Credentials: true` → flag as a real vulnerability (browsers block this combination, but misconfigured proxies/frameworks sometimes still emit it, and it signals a broader too-permissive CORS policy).

## Output format

Group by severity (auth bypass / IDOR / SSRF first, then secret leakage, then CORS/misc). Each finding: file:line, exploit scenario in one sentence, fixed code snippet. End with a short "not covered" note listing anything that would need a live pentest or infra review (rate limiting behavior under load, WAF rules, actual network segmentation) rather than static review.
