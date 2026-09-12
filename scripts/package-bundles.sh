#!/usr/bin/env bash
set -e

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="$BASE_DIR/dist"

echo "=================================================="
echo "📦 PACKAGING AI SKILLS RELEASES FOR GUMROAD"
echo "=================================================="
echo "Output Directory: $DIST_DIR"

mkdir -p "$DIST_DIR"
rm -f "$DIST_DIR"/*.zip

cd "$BASE_DIR"

# 1. Package Cloud Cost Auditor
echo ">> Packaging cloud-cost-auditor.zip..."
zip -q -r "$DIST_DIR/cloud-cost-auditor.zip" \
  cloud-cost-auditor/SKILL.md \
  cloud-cost-auditor/scripts \
  cloud-cost-auditor/tests \
  templates/ci-cd/cost-guard.yml

# 2. Package Postgres Migration Auditor
echo ">> Packaging postgres-migration-auditor.zip..."
zip -q -r "$DIST_DIR/postgres-migration-auditor.zip" \
  postgres-migration-auditor/SKILL.md \
  postgres-migration-auditor/scripts \
  postgres-migration-auditor/tests \
  templates/ci-cd/migration-guard.yml

# 3. Package OWASP Security Reviewer
echo ">> Packaging owasp-security-reviewer.zip..."
zip -q -r "$DIST_DIR/owasp-security-reviewer.zip" \
  owasp-security-reviewer/SKILL.md \
  owasp-security-reviewer/scripts \
  owasp-security-reviewer/tests \
  templates/ci-cd/security-guard.yml

# 4. Package All-in-One Enterprise DevOps Bundle
echo ">> Packaging enterprise-devops-bundle.zip..."
zip -q -r "$DIST_DIR/enterprise-devops-bundle.zip" \
  cloud-cost-auditor \
  postgres-migration-auditor \
  owasp-security-reviewer \
  templates \
  scripts/run-all-tests.sh

echo ""
echo "✅ All packages built successfully in $DIST_DIR:"
ls -lh "$DIST_DIR"/*.zip
echo "=================================================="
