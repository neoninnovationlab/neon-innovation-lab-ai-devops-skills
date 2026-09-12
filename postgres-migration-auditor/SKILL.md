---
name: postgres-migration-auditor
description: Reviews Postgres migration files (raw SQL, Prisma, Drizzle, TypeORM, Alembic/SQLAlchemy) for patterns that cause production locking, downtime, or deadlocks. Use before merging a migration PR, or when a user reports a migration hung/blocked production traffic.
---

# Postgres Migration & Deadlock Auditor

## What this catches (all statically detectable from migration source)

Scan `*.sql`, Prisma `migration.sql`, Alembic `versions/*.py`, TypeORM migration classes, and Drizzle migration output.

- **ADD COLUMN with NOT NULL and no/volatile default (pre-PG11 behavior, and still relevant with volatile defaults on any version)**: `ALTER TABLE ... ADD COLUMN ... NOT NULL DEFAULT <non-constant-expr>` rewrites every row and takes an ACCESS EXCLUSIVE lock for the duration → flag. Recommend: add the column nullable, backfill in batches, then add a `NOT NULL` constraint via `ADD CONSTRAINT ... NOT VALID` + `VALIDATE CONSTRAINT` (which only needs a brief lock).
- **CREATE INDEX without CONCURRENTLY**: any `CREATE INDEX` (or `CREATE UNIQUE INDEX`) on an existing, presumably-populated table without `CONCURRENTLY` → flag. Plain `CREATE INDEX` takes a lock that blocks writes for the build duration. Note the constraint: `CONCURRENTLY` cannot run inside a transaction block — flag if the migration framework wraps migrations in an implicit transaction (common in TypeORM/Prisma) and suggest the framework's "no-transaction" migration mode.
- **Missing index on foreign key columns**: a `REFERENCES` / `FOREIGN KEY` constraint added where the referencing column has no corresponding index → flag. Unindexed FK columns cause full table scans on parent-row deletes/updates, escalating into long lock waits under concurrent load.
- **DROP COLUMN / DROP TABLE on a live table without a soft-deprecation step** → flag as high-risk; recommend a two-step deploy (stop writing/reading the column in application code first, drop in a later migration).
- **Long-running `SELECT ... FOR UPDATE` inside a loop** (e.g., iterating rows one at a time while holding row locks, or `FOR UPDATE` combined with an unbounded `WHERE`) → flag as a deadlock/starvation risk; recommend batching with `LIMIT` + `SKIP LOCKED` where semantics allow, or moving the lock scope tighter.
- **Renaming a column/table still referenced by running application code** → flag as a compatibility break, not just a lock issue; recommend expand-contract (add new, dual-write, backfill, cut over, drop old).
- **Multiple DDL statements against different tables in one migration without explicit lock ordering** → flag as a deadlock risk if two migrations/transactions could plausibly touch the same tables in reverse order.

## What this does NOT claim to catch

- Actual lock contention under your specific production traffic pattern (that depends on live query load, not the migration file).
- Whether a "brief" lock is actually brief on your table's real size — always recommend testing large-table migrations against a production-sized snapshot or with `pg_stat_activity` monitoring during rollout.

## Output format

For each finding: file, statement, why it locks/deadlocks, and the exact rewritten SQL (not just a description) using the CONCURRENTLY / NOT VALID+VALIDATE / expand-contract patterns above. Rank findings by lock severity: ACCESS EXCLUSIVE table-lock issues first, then row-lock/deadlock risks, then compatibility-break issues.
