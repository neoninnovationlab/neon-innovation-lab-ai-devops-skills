#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "=================================================="
echo "🧪 AI SKILLS MARKETPLACE: SENIOR QA/QC TEST SUITE"
echo "=================================================="
echo "Base Directory: $DIR"
echo ""

FAILURES=0

# Test 1: Cloud Cost Auditor
echo "--------------------------------------------------"
echo "1️⃣  Testing Cloud Cost Auditor (tf-cost-scanner.py)..."
echo "--------------------------------------------------"

echo ">> Running against wasteful fixture (expecting findings)..."
python3 "$DIR/cloud-cost-auditor/scripts/tf-cost-scanner.py" "$DIR/cloud-cost-auditor/tests/fixtures/wasteful.tf" > /tmp/tf_wasteful.out
if grep -q "Found 5 static cost finding(s)" /tmp/tf_wasteful.out; then
    echo "   ✅ PASS: Correctly detected all 5 waste patterns."
else
    echo "   ❌ FAIL: Unexpected output on wasteful.tf"
    FAILURES=$((FAILURES + 1))
fi

echo ">> Running against clean fixture (expecting zero findings)..."
python3 "$DIR/cloud-cost-auditor/scripts/tf-cost-scanner.py" "$DIR/cloud-cost-auditor/tests/fixtures/clean.tf" > /tmp/tf_clean.out
if grep -q "No static cost smells found" /tmp/tf_clean.out; then
    echo "   ✅ PASS: Clean fixture reported 0 smells."
else
    echo "   ❌ FAIL: Unexpected findings on clean.tf"
    FAILURES=$((FAILURES + 1))
fi

# Test 2: Postgres Migration Auditor
echo ""
echo "--------------------------------------------------"
echo "2️⃣  Testing Postgres Migration Auditor (lock-analyzer.py)..."
echo "--------------------------------------------------"

echo ">> Running against risky migration fixture (expecting findings)..."
python3 "$DIR/postgres-migration-auditor/scripts/lock-analyzer.py" "$DIR/postgres-migration-auditor/tests/fixtures/risky_migration.sql" > /tmp/sql_risky.out
if grep -q "Found 5 finding(s)" /tmp/sql_risky.out; then
    echo "   ✅ PASS: Correctly detected all 5 lock hazards."
else
    echo "   ❌ FAIL: Unexpected output on risky_migration.sql"
    FAILURES=$((FAILURES + 1))
fi

echo ">> Running against safe migration fixture (expecting zero findings)..."
python3 "$DIR/postgres-migration-auditor/scripts/lock-analyzer.py" "$DIR/postgres-migration-auditor/tests/fixtures/safe_migration.sql" > /tmp/sql_safe.out
if grep -q "No locking/deadlock risk patterns found" /tmp/sql_safe.out; then
    echo "   ✅ PASS: Safe migration reported 0 lock risks."
else
    echo "   ❌ FAIL: Unexpected findings on safe_migration.sql"
    FAILURES=$((FAILURES + 1))
fi

# Test 3: OWASP Security Reviewer
echo ""
echo "--------------------------------------------------"
echo "3️⃣  Testing OWASP Security Reviewer (security-scanner.py)..."
echo "--------------------------------------------------"

echo ">> Running against vulnerable app fixture (expecting findings & exit code 1)..."
set +e
python3 "$DIR/owasp-security-reviewer/scripts/security-scanner.py" "$DIR/owasp-security-reviewer/tests/fixtures/vulnerable_app.ts" > /tmp/owasp_vuln.out
VULN_EXIT=$?
set -e

if [ $VULN_EXIT -eq 1 ] && grep -q "Found 6 security finding(s)" /tmp/owasp_vuln.out; then
    echo "   ✅ PASS: Correctly detected 6 vulnerabilities and exited with status 1."
else
    echo "   ❌ FAIL: Vulnerable app test failed (Exit: $VULN_EXIT)"
    FAILURES=$((FAILURES + 1))
fi

echo ">> Running against secure app fixture (expecting clean & exit code 0)..."
python3 "$DIR/owasp-security-reviewer/scripts/security-scanner.py" "$DIR/owasp-security-reviewer/tests/fixtures/secure_app.ts" > /tmp/owasp_secure.out
if grep -q "No OWASP or framework security anti-patterns detected" /tmp/owasp_secure.out; then
    echo "   ✅ PASS: Secure app reported 0 vulnerabilities and exited with status 0."
else
    echo "   ❌ FAIL: Unexpected findings on secure_app.ts"
    FAILURES=$((FAILURES + 1))
fi

echo ""
echo "=================================================="
if [ $FAILURES -eq 0 ]; then
    echo "🎉 ALL 6 QA/QC SUITE TESTS PASSED WITH 100% PRECISION!"
    echo "=================================================="
    exit 0
else
    echo "💥 $FAILURES TEST(S) FAILED. REVIEW LOGS."
    echo "=================================================="
    exit 1
fi
